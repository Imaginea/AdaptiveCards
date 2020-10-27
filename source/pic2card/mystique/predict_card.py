"""Module to  get the predicted adaptive card json"""

import base64
import io
import json
import os
import uuid
from multiprocessing import Process, Queue
from typing import Dict, List, Tuple, Union

import cv2
import numpy as np
import requests
from PIL import Image
from mystique import config
from mystique.card_layout.arrange_card import CardArrange
from mystique.ac_export.card_template_data import DataBinding
from mystique.ac_export.adaptive_card_export import (
    AdaptiveCardExport)
from mystique.extract_properties import CollectProperties, ContainerProperties
from mystique.image_extraction import ImageExtraction
from mystique.utils import get_property_method
from mystique.card_layout.row_column_group import RowColumnGroup
from mystique.card_layout.container_group import ContainerGroup
from mystique.card_layout import bbox_utils


class PredictCard:
    """
    Collects the faster rcnn detected objects and handles the
    functionality of calling diffrent modules in card prediction
    and returning the predicted json objects.
    """

    def __init__(self, od_model=None):
        """
        Find the card components using Object detection model
        """
        self.od_model = od_model

    def collect_objects(self, output_dict=None, pil_image=None):
        """
        Returns the design elements from the faster rcnn model with its
        properties mapped
        @param output_dict: output dict from the object detection
        @param pil_image: input PIL image
        @return: Collected json of the design objects
                 and list of detected object's coordinates
        """
        boxes = output_dict["detection_boxes"]
        scores = output_dict["detection_scores"]
        classes = output_dict["detection_classes"]
        r, c = boxes.shape
        detected_coords = []
        json_object = {}.fromkeys(["objects"], [])
        width, height = pil_image.size
        for i in range(r):
            if scores[i] * 100 >= config.MODEL_CONFIDENCE:
                object_json = dict().fromkeys(
                    ["object", "xmin", "ymin", "xmax", "ymax"], "")
                object_json["object"] = config.ID_TO_LABEL[classes[i]]
                if object_json["object"]:
                    xmin, ymin, xmax, ymax = boxes[i]
                    object_json["xmin"] = xmin
                    object_json["ymin"] = ymin
                    object_json["xmax"] = xmax
                    object_json["ymax"] = ymax
                    object_json["coords"] = (xmin, ymin, xmax, ymax)
                    object_json["score"] = scores[i]
                    object_json['uuid'] = str(uuid.uuid4())
                    object_json["class"] = classes[i]

                    if object_json["object"] == "textbox":
                        detected_coords.append(
                            (xmin - config.TEXTBOX_PADDING, ymin,
                             xmax + config.TEXTBOX_PADDING, ymax))
                    else:
                        detected_coords.append((xmin, ymin, xmax, ymax))

                    json_object["objects"].append(object_json)

        return json_object, detected_coords

    def get_object_properties(self, design_objects: List[Dict],
                              pil_image: Image, queue=None) -> None:
        """
        Extract each design object's properties.
        @param design_objects: List of design objects collected from the model.
        @param pil_image: Input PIL image
        @param queue: Queue object of the calling process
        """
        # Creating an Extract Property class instance
        collect_prop = CollectProperties()
        for design_object in design_objects:
            # Invoking the methods from dict according to the design object
            property_object = get_property_method(collect_prop,
                                                  design_object.get("object"))
            property_element = property_object(pil_image,
                                               design_object.get("coords"))
            design_object.update(property_element)
        # If any Queue object is passed , put the return value inside the
        # queue in-order to retrieve the value after the process finishes.
        if queue:
            queue.put(design_objects)

    def main(self, image=None, card_format=None):
        """
        Handles the different components calling and returns the
        predicted card json to the API
        @param labels_path: faster rcnn model's label path
        @param forzen_graph_path: faster rcnn model path
        @param image: input image path
        @return: predicted card json
        """
        image = image.convert("RGB")
        image_np = np.asarray(image)
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        # Extract the design objects from faster rcnn model
        output_dict = self.od_model.get_objects(
            image_np=image_np, image=image
        )
        return self.generate_card(output_dict, image, image_np, card_format)

    def tf_serving_main(self, bs64_img: str, tf_server: str, model_name: str,
                        card_format: str = None) -> Dict:
        tf_uri = os.path.join(tf_server,
                              f"v1/models/{model_name}:predict")
        payloads = {
            "signature_name": "serving_default",
            "instances": [
                {"b64": bs64_img}
            ]
        }

        # Hit the tf-serving and get the prediction
        response = requests.post(tf_uri, json=payloads)
        pred_res = json.loads(response.content)["predictions"][0]

        filtered_res = {}
        for key_col in ["detection_boxes", "detection_scores",
                        "detection_classes"]:
            filtered_res[key_col] = np.array(pred_res[key_col])

        # Prepare the card from object detection.
        imgdata = base64.b64decode(bs64_img)
        image = Image.open(io.BytesIO(imgdata))
        image = image.convert("RGB")
        image_np = np.asarray(image)
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        card = self.generate_card(filtered_res,
                                  image, image_np, card_format)
        return card

    def layout_generation(self, json_objects: List, queue: Queue) -> List[Dict]:
        """
        Returns the generated hierarchical layout structure.
        @param json_objects: extracted list of design objects
        @param queue: Queue object of the calling process
        @return: Generated layout structure
        """
        layout_structure = []
        row_column_group = RowColumnGroup()
        row_column_group.row_column_grouping(json_objects,
                                             layout_structure)
        container_group = ContainerGroup()
        layout_structure = container_group.containers_grouping(
            layout_structure)
        if queue:
            queue.put(layout_structure)
        return layout_structure

    def export_to_card(self, layout_data_structure: List[Dict],
                       properties, pil_image) -> List:
        """
        Returns the exported adaptive card design body.
        @param layout_data_structure: Generated hierarchical layout structure.
        @param properties: List of design object with properties extracted.
        @param pil_image: Input design image
        @return: Exported adaptive card json body
        """
        export_card = AdaptiveCardExport()
        export_card.merge_properties(properties, layout_data_structure)
        container_properties = ContainerProperties(pil_image=pil_image)
        layout_data_structure = container_properties.get_container_properties(
            layout_data_structure, pil_image)
        body = export_card.build_adaptive_card(layout_data_structure)
        return body

    def new_layout_generation(self, json_objects: Dict,
                              image: Image) -> Union[List, None]:
        """
        Performs the property extraction and hierarchical layout structuring
        in parallel and merges both on completion to export it to the adaptive
        card json body.
        @param json_objects: List of extracted design objects
        @param image: input design image
        @return: exported adaptive card json body
        """

        queue1 = Queue()
        queue2 = Queue()
        try:
            process1 = Process(target=self.get_object_properties, args=(
                json_objects["objects"], image, queue1,))
            process2 = Process(target=self.layout_generation,
                               args=(json_objects["objects"], queue2,))
            process1.start()
            process2.start()

            properties = queue1.get()
            layout_structure = queue2.get()

            process1.join()
            process2.join()
            return self.export_to_card(layout_structure, properties, image)
        except Exception:
            return None

    def generate_card(self, prediction: Dict, image: Image,
                      image_np: np.array, card_format: str):
        """
        From the object detection result and image, generate adaptive
        card object.
        @param prediction: Prediction result from rcnn model
        @param image: PIL Image object to crop the regions.
        @param image_np: Array representation of the image.
        @param card_format: format specification for template data binding
        """
        # TODO: Remove the reduendant usage of image and image_np

        # Collect the objects along with its design properites

        json_objects, detected_coords = self.collect_objects(
            output_dict=prediction, pil_image=image)
        # Remove overlapping rcnn objects
        bbox_utils.remove_noise_objects(json_objects)

        # The property extraction happens sequentially only if the
        # NEW_LAYOUT_STRUCTURE is not enabled
        if not config.NEW_LAYOUT_STRUCTURE:
            # get design object properties
            self.get_object_properties(json_objects["objects"], image)
        # Get image coordinates from custom image pipeline
        # if config.USE_CUSTOM_IMAGE_PIPELINE:
        #     self.get_image_objects(json_objects, detected_coords,
        #     card_arrange, image_np, image)

        # Arrange the design elements
        return_dict = {}.fromkeys(["card_json"], "")
        card_json = {
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
        }

        # If the NEW_LAYOUT_STRUCTURE is enabled in the config
        # performs the card arranging as recursive hierarchical layout
        # structuring and property extraction in parallel and finally
        # merges both to export it to card json body
        if config.NEW_LAYOUT_STRUCTURE:
            body = self.new_layout_generation(json_objects, image)
        else:
            card_arrange = CardArrange()
            body, ymins = card_arrange.build_card_json(
                objects=json_objects.get("objects", []), image=image)
            # Sort the elements vertically
            body = [x for _, x in sorted(zip(ymins, body),
                                         key=lambda x: x[0])]
        # if format==template - generate template data json
        return_dict["card_json"] = {}.fromkeys(["data", "card"], {})
        if card_format == "template":
            databinding = DataBinding()
            data_payload, body = databinding.build_data_binding_payload(body)
            return_dict["card_json"]["data"] = data_payload
        # Prepare the response with error code
        error = None
        if not body or not detected_coords:
            error = {
                "msg": "Failed to generate card components",
                "code": 1000
            }
        else:
            card_json["body"] = body

        if card_format != "template":
            return_dict["card_json"]["card"] = card_json
        else:
            return_dict["card_json"]["card"] = card_json
        return_dict["error"] = error

        return return_dict

    def get_image_objects(self, json_objects: List[Dict],
                          detected_coords: List[Tuple],
                          card_arrange: CardArrange, image_np: np.array,
                          image: Image):
        """
        Collects the image objects using the custom image pipeline
        @param json_objects: list of design objects from the rcnn model
        @param detected_coords: list of coordinates of the design objects
        @param card_arrange: CardArrange object
        @param image_np: opencv input image
        @param image: PIL input image
        """
        # delete image from the rcnn model detected objects and coordinates
        positions_to_remove = [ctr for ctr, design_object in enumerate(
            json_objects.get("objects", []))
                               if design_object.get("object") == "image"]
        json_objects["objects"] = [
            design_object for ctr, design_object in enumerate(
                json_objects.get("objects")) if ctr not in positions_to_remove
        ]
        detected_coords = [coords for ctr, coords in enumerate(
            detected_coords) if ctr not in positions_to_remove]

        image_extraction = ImageExtraction()
        image_points = image_extraction.detect_image(
            image=image_np,
            detected_coords=detected_coords,
            pil_image=image
        )
        image_urls, image_sizes = image_extraction.image_crop_get_url(
            coords=image_points,
            image=image)
        # Append the image objects to the deisgn objects list
        card_arrange.append_image_objects(image_urls=image_urls,
                                          image_sizes=image_sizes,
                                          image_coords=image_points,
                                          pil_image=image,
                                          json_object=json_objects)
