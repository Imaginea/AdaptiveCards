"""Module for extracting design element's properties"""

import base64
import math
import operator
from io import BytesIO
from typing import Tuple, Dict, List

import numpy as np
import cv2
from PIL import Image
from pytesseract import pytesseract, Output

from mystique.utils import get_property_method
from mystique import config, default_host_configs
from mystique.extract_properties_abstract import (AbstractFontWeight,
                                                  AbstractFontSize,
                                                  AbstractBaseExtractProperties
                                                  )


class BaseExtractProperties(AbstractBaseExtractProperties):

    """
    Base Class for all property related extract functions.
    """

    def get_alignment(self, image: Image, xmin, xmax) -> str:
        """
        Get the horizontal alignment of the elements by defining a
        ratio based on the xmin and xmax center of each object.
        if a element's xmin and xmax avg lies within:
        0 - 45 % [ left range ] of the image width
        45 - 55% [ center rance ] of the image width
        > 55% [ right range ] of the image width
        @param image: input PIL image
        @param xmin: xmin of the object detected
        @param xmax: xmax of the object detected
        @return: position string[Left/Right/Center]
        """
        avg = math.ceil((xmin + xmax) / 2)
        w, h = image.size
        #  if an object lies within the 15% of the start of the image then the
        #  object is considered as left by default [to avoid any lengthy
        # textbox coming into center when considering the xmin and xmax center]
        left_range = (w * 15) / 100
        if math.floor(xmin) <= math.ceil(left_range) or abs(
                xmin - left_range) < 10:
            return "Left"

        if 0 <= (avg / w) * 100 < 45:
            return "Left"
        elif 45 <= (avg / w) * 100 < 55:
            return "Center"
        else:
            return "Right"

    def get_text(self, image, coords: Tuple) -> str:
        """
        Extract the text from the object coordinates
        in the input deisgn image using pytesseract.
        @param image: input PIL image
        @param coords: tuple of coordinates from which
                       text should be extracted
        @return: ocr text
        """
        coords = (coords[0] - 5, coords[1], coords[2] + 5, coords[3])
        cropped_image = image.crop(coords)
        cropped_image = cropped_image.convert("LA")

        img_data = pytesseract.image_to_data(
            cropped_image, lang="eng", config="--psm 6",
            output_type=Output.DICT)
        text_list = ' '.join(img_data['text']).split()
        extracted_text = ' '.join(text_list)

        return extracted_text, img_data

    def checkbox(self, image: Image, coords: Tuple) -> Dict:
        """
        Returns the checkbox properties of the extracted design object
        @return: property object
        """
        get_alignment = get_property_method(self, "horizontal_alignment")
        get_data = get_property_method(self, "data")

        return {
            "horizontal_alignment": get_alignment(
                image=image,
                xmin=coords[0],
                xmax=coords[2]
            ),
            "data": get_data(image, coords),
        }

    def radiobutton(self, image: Image, coords: Tuple) -> Dict:
        """
        Returns the radiobutton properties of the extracted design object
        @return: property object
        """
        return self.checkbox(image, coords)


class GetChoiceButton(BaseExtractProperties):

    """
    Class handles extraction of ocr text and alignment property of respective
    design elements.
    """
    pass


class GetFontWeight(AbstractFontWeight):
    """
    Class handles extraction of font weight from respective design elements
    """

    def get_weight(self, image: Image, coords: Tuple) -> str:
        """
        Extract the weight of the each words by
        skeletization applying morph operations on
        the input image

        @param image : input PIL image
        @param coords: list of coordinated from which
                       text and height should be extracted
        @return: weight
        """
        cropped_image = image.crop(coords)
        image_width, image_height = image.size
        c_img = np.asarray(cropped_image)
        """
        if(image_height/image_width) < 1:
            y_scale = round((800/image_width), 2)
            x_scale = round((500/image_height), 2)
            c_img = cv2.resize(c_img, (0, 0), fx=x_scale, fy=y_scale)
        """
        gray = cv2.cvtColor(c_img, cv2.COLOR_BGR2GRAY)
        # Converting input image to binary format
        _, img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        area_of_img = np.count_nonzero(img)
        # creating an empty skeleton
        skel = np.zeros(img.shape, np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        # Loop until erosion leads to thinning text in image to singular pixel
        while True:
            open = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
            temp = cv2.subtract(img, open)
            eroded = cv2.erode(img, kernel)
            skel = cv2.bitwise_or(skel, temp)
            img = eroded.copy()
            # if no white pixels left the image has been completely eroded
            if cv2.countNonZero(img) == 0:
                break
        # length of the lines in text
        area_of_skel = np.sum(skel)/255
        # width of line = area of the line / length of the line
        thickness = round(area_of_img/area_of_skel, 2)

        font_weight = default_host_configs.FONT_WEIGHT

        if font_weight['lighter'] >= thickness:
            weight = "Lighter"
        elif font_weight['bolder'] <= thickness:
            weight = "Bolder"
        else:
            weight = "Default"

        return weight


class GetFontSize(AbstractFontSize):
    """
    Class handles extraction of font size of respective design elements
    """

    def get_size(self, image: Image, coords: Tuple, img_data: Dict) -> str:
        """
        Extract the size by taking an average of
        ratio of height of each character to height
        input image using pytesseract

        @param image : input PIL image
        @param coords: list of coordinated from which
                       text and height should be extracted
        @param img_data : input image data from pytesseract
        @return: size
        """
        image_width, image_height = image.size
        box_height = []
        n_boxes = len(img_data['level'])
        for i in range(n_boxes):
            if len(img_data['text'][i]) > 1:  # to ignore img with wrong bbox
                (_, _, _, h) = (img_data['left'][i], img_data['top'][i],
                                img_data['width'][i], img_data['height'][i])
                # h = text_size_processing(img_data['text'][i], h)

                box_height.append(h)
        font_size = default_host_configs.FONT_SIZE
        # Handling of unrecognized characters
        if len(box_height) == 0:
            heights_ratio = font_size['default']
        else:
            heights = int(np.mean(box_height))
            heights_ratio = round((heights/image_height), 4)

        if font_size['small'] < heights_ratio < font_size['default']:
            size = "Small"
        elif font_size['default'] < heights_ratio < font_size['medium']:
            size = "Default"
        elif font_size['medium'] < heights_ratio < font_size['large']:
            size = "Medium"
        elif font_size['large'] < heights_ratio < font_size['extralarge']:
            size = "Large"
        elif font_size['extralarge'] < heights_ratio:
            size = "ExtraLarge"
        else:
            size = "Default"

        return size


class GetTextBoxProperty(BaseExtractProperties, GetFontSize, GetFontWeight):
    """
    Class handles extraction of text properties from all the design elements
    like size, weight, colour and ocr text
    """

    def get_colors(self, image: Image, coords: Tuple) -> str:
        """
        Extract the text color by quantaizing the image i.e
        [cropped to the coordiantes] into 2 colors mainly
        background and foreground and find the closest matching
        foreground color.
        @param image: input PIL image
        @param coords: coordinates from which color needs to be
                       extracted

        @return: foreground color name
        """
        cropped_image = image.crop(coords)
        # get 2 dominant colors
        q = cropped_image.quantize(colors=2, method=2)
        dominant_color = q.getpalette()[3:6]

        colors = {
            "Attention": [
                (255, 0, 0),
                (180, 8, 0),
                (220, 54, 45),
                (194, 25, 18),
                (143, 7, 0)
            ],
            "Accent": [
                (0, 0, 255),
                (7, 47, 95),
                (18, 97, 160),
                (56, 149, 211)
            ],
            "Good": [
                (0, 128, 0),
                (145, 255, 0),
                (30, 86, 49),
                (164, 222, 2),
                (118, 186, 27),
                (76, 154, 42),
                (104, 187, 89)
            ],
            "Dark": [
                (0, 0, 0),
                (76, 76, 76),
                (51, 51, 51),
                (102, 102, 102),
                (153, 153, 153)
            ],
            "Light": [
                (255, 255, 255)
            ],
            "Warning": [
                (255, 255, 0),
                (255, 170, 0),
                (184, 134, 11),
                (218, 165, 32),
                (234, 186, 61),
                (234, 162, 33)
            ]
        }
        color = "Default"
        found_colors = []
        distances = []
        # find the dominant text colors based on the RGB difference
        for key, values in colors.items():
            for value in values:
                distance = np.sqrt(np.sum(
                    (np.asarray(value) - np.asarray(dominant_color)) ** 2))
                if distance <= 150:
                    found_colors.append(key)
                    distances.append(distance)
        # If the color is predicted as LIGHT check for false cases
        # where both dominan colors are White
        if found_colors:
            index = distances.index(min(distances))
            color = found_colors[index]
            if found_colors[index] == "Light":
                background = q.getpalette()[:3]
                foreground = q.getpalette()[3:6]
                distance = np.sqrt(
                    np.sum(
                        (np.asarray(background) -
                         np.asarray(foreground)) ** 2))
                if distance < 150:
                    color = "Default"
        return color

    def textbox(self, image: Image, coords: Tuple) -> Dict:
        """
        Returns the textbox properties of the extracted design object
        @return: property object
        """
        get_alignment = get_property_method(self, "horizontal_alignment")
        get_data = get_property_method(self, "data")
        get_size = get_property_method(self, "size")
        get_weight = get_property_method(self, "weight")
        get_color = get_property_method(self, "color")
        # getting the pytesseract api image_to_data result and the text
        data, image_data = get_data(image, coords)

        return {
            "horizontal_alignment": get_alignment(
                image=image,
                xmin=coords[0],
                xmax=coords[2]
            ),
            "data": data,
            "size": get_size(image, coords, img_data=image_data),
            "weight": get_weight(image, coords),
            "color": get_color(image, coords)

        }


class GetImageProperty(BaseExtractProperties):
    """
    Class handles extraction of image properties from image design object
    like image size, image text and its alignment property
    """

    def get_data(self, base64_string) -> str:
        """
        Returns the base64 string for the detected image property object
        @param base64_string: input base64 encoded value for the buff object
        @return: base64_string appended to filepath
        """
        data = f'data:image/png;base64,{base64_string}'
        return data

    def extract_image_size(self, cropped_image: Image,
                           pil_image: Image) -> str:
        """
        Returns the image size value based on the width and height ratios
        of the image objects to the actual design image.
        @param cropped_image: image object
        @param pil_image: input design image
        @return: image width value
        """
        img_width, img_height = cropped_image.size
        width, height = pil_image.size
        width_ratio = (img_width / width) * 100
        height_ratio = (img_height / height) * 100
        # if the width and height ratio differs more the 25% return the size as
        # Auto
        if abs(width_ratio - height_ratio) > 20:
            return "Auto"
        else:
            # select the image size based on the minimum distance with
            # the default host config values for image size
            keys = list(config.IMAGE_SIZE_RATIOS.keys())
            ratio = (width_ratio, height_ratio)
            distances = [np.sqrt(np.sum(((np.asarray(ratio) -
                                          np.asarray(tuple(point))) ** 2)))
                         for point in keys]
            key = keys[distances.index(min(distances))]
            return config.IMAGE_SIZE_RATIOS[key]

    def image(self, image: Image, coords: Tuple) -> Dict:
        """
        Returns the image properties of the extracted design object
        @return: property object
        """
        cropped = image.crop(coords)
        buff = BytesIO()
        cropped.save(buff, format="PNG")
        base64_string = base64.b64encode(
            buff.getvalue()).decode()

        size = self.extract_image_size(cropped, image)
        return {
            "horizontal_alignment": self.get_alignment(
                image=image,
                xmin=coords[0],
                xmax=coords[2]
            ),
            "data": self.get_data(base64_string),
            "size": size
        }


class GetActionSetProperty(BaseExtractProperties):
    """
    Class handles extraction of actionset object properties of its
    respective design object
    """

    def get_actionset_type(self, image: Image, coords: Tuple) -> str:
        """
        Returns the actionset style by finding the
        closes background color of the obejct
        @param image: input PIL image
        @param coords: object's coordinate
        @return: style string of the actionset
        """
        cropped_image = image.crop(coords)
        # get 2 dominant colors
        quantized = cropped_image.quantize(colors=2, method=2)
        # extract the background color
        background_color = quantized.getpalette()[:3]
        colors = {
            "destructive": [
                (255, 0, 0),
                (180, 8, 0),
                (220, 54, 45),
                (194, 25, 18),
                (143, 7, 0)
            ],
            "positive": [
                (0, 0, 255),
                (7, 47, 95),
                (18, 97, 160),
                (56, 149, 211)
            ]
        }
        style = "default"
        found_colors = []
        distances = []
        # find the dominant background colors based on the RGB difference
        for key, values in colors.items():
            for value in values:
                distance = np.sqrt(
                    np.sum(
                        (np.asarray(value) - np.asarray(
                            background_color)) ** 2
                    )
                )
                if distance <= 150:
                    found_colors.append(key)
                    distances.append(distance)
        if found_colors:
            index = distances.index(min(distances))
            style = found_colors[index]
        return style

    def actionset(self, image: Image, coords: Tuple) -> Dict:
        """
        Returns the actionset properties of the extracted design object
        @return: property object
        """
        get_alignment = get_property_method(self, "horizontal_alignment")
        get_data = get_property_method(self, "data")
        get_actionset_type = get_property_method(self, "style")

        return {
            "horizontal_alignment": get_alignment(
                image=image,
                xmin=coords[0],
                xmax=coords[2]
            ),
            "data": get_data(image, coords),
            "style": get_actionset_type(image, coords)
        }


class CollectProperties(GetTextBoxProperty, GetActionSetProperty,
                        GetImageProperty):
    """
    Class handles of property extraction from the identified design
    elements.
    from all the design elements - extracts text, alignment
    from textual elements - extracts size, color, weight
    from actionset elements - extracts style based on the background
                              color
    from image objects - extracts image size and image text
    """

    def find_iou(self, coord1, coord2, inter_object=False,
                 columns_group=False) -> List:
        """
        Finds the intersecting bounding boxes by finding
           the highest x and y ranges of the 2 coordinates
           and determine the intersection by deciding weather
           the new xmin > xmax or the new ymin > ymax.
           For non image objects, includes finding the intersection
           area to a threshold to determine intersection

        @param coord1: list of coordinates of 1st object
        @param coord2: list of coordinates of 2nd object
        @param inter_object: check for cleaning between different overlapping
                             objects.

        @param columns_group: If the intersection finding is needed in columns
                              grouping use case

        @return: [True/False, point1 area, point2 area]
        """
        x5 = max(coord1[0], coord2[0])
        y5 = max(coord1[1], coord2[1])
        x6 = min(coord1[2], coord2[2])
        y6 = min(coord1[3], coord2[3])

        # no intersection
        if x6 - x5 <= 0 or y6 - y5 <= 0:
            return [False]

        intersection_area = (x6 - x5) * (y6 - y5)
        point1_area = (coord1[2] - coord1[0]) * (coord1[3] - coord1[1])
        point2_area = (coord2[2] - coord2[0]) * (coord2[3] - coord2[1])
        iou = (intersection_area
               / (point1_area + point2_area - intersection_area))

        # find if given 2 objects intersects or not
        if columns_group:
            if ((point1_area + point2_area - intersection_area == 0)
                    or iou > 0):
                return [True]
            return [False]

        # -if iou check is for inter object overlap removal check only for
        # intersection.
        # -if not for inter objects overlap check for iou >= threshold
        # -if the intersection area covers more than 50% of the smaller object
        if ((point1_area + point2_area - intersection_area == 0)
                or (inter_object and iou > 0)
                or (iou >= config.IOU_THRESHOLD)
                or (iou <= config.IOU_THRESHOLD
                    and
                    (intersection_area /
                     min(point1_area, point2_area)) >= 0.50)):
            return [True, point1_area, point2_area]

        return [False]

    def get_column_width_keys(self, default_config: Dict, ratio: Tuple,
                              column_set: Dict, column_number: int) -> None:
        """
        Extract the column width key from the default config which is minimum
        in distance with the given point / ratio
        @param default_config: the default host config dict for column width
        @param ratio: the point derived from the column coordinates
        @param column_set: dict of columns
        @param column_number: the position of the column
        """
        keys = list(default_config.keys())
        distances = [np.sqrt(np.sum(((np.asarray(ratio) -
                                      np.asarray(tuple(point))) ** 2)))
                     for point in keys]
        key = keys[distances.index(min(distances))]
        column_set["columns"][column_number]["width"] = default_config[key]

    def extract_column_width(self, column_set: Dict,
                             column_coords: List[List],
                             column_coords_min: List[List],
                             image: Image) -> None:
        """
        Extract column width property for the given columnset based on the
        mid point distance between 2 design objects.
        @param column_set: list of column design objects
        @param column_coords: each column's max coordinate values of a
                              column set

        @param image: input PIL image
        @param column_coords_min: each column's min coordinate values of a
                                  column set
        """
        column_xmin, column_ymin, column_xmax, column_ymax = column_coords
        (column_xmin_min, column_ymin_min,
         column_xmax_min, column_ymax_min) = column_coords_min
        for ctr, column in enumerate(column_set["columns"]):
            if ctr + 1 < len(column_set["columns"]):
                mid_point1 = np.asarray(
                    ((column_xmin[ctr] + column_xmax[ctr])/2,
                     (column_ymin[ctr] + column_ymax[ctr])/2))
                mid_point2 = np.asarray(
                    ((column_xmin_min[ctr + 1]
                      + column_xmax_min[ctr + 1]) / 2,
                     (column_ymin_min[ctr + 1]
                      + column_ymax_min[ctr + 1]) / 2))

                a = np.asarray((column_xmin[ctr], column_ymin[ctr]))
                b = np.asarray((column_xmax[ctr+1], column_ymax[ctr+1]))
                end_distance = np.sqrt(np.sum(((a - b) ** 2)))
                mid_distance = np.sqrt(np.sum(((mid_point1 - mid_point2)
                                               ** 2)))
                mid_distance = (mid_distance / end_distance) * 100
                ratio = (1, mid_distance)
                self.get_column_width_keys(
                    config.COLUMN_WIDTH_DISTANCE, ratio,
                    column_set, ctr)
            if ctr == len(column_set["columns"]) - 1:
                w, h = image.size
                last_diff = (abs(column_xmax[ctr] - w) / w) * 100
                ratio = (1, last_diff)
                self.get_column_width_keys(
                    config.LAST_COLUMN_THRESHOLD, ratio,
                    column_set, ctr)

    def column(self, columns: Dict):
        """
        Updates the horizontal alignment property for the columns,
        based on the horizontal alignment of each items inside the column
        @param columns: List of columns[for a columnset]
        """
        preference_order = ["Left", "Center", "Right"]
        for column in columns:
            alignment = list(map(operator.itemgetter('horizontalAlignment'),
                                 column["items"]))
            if len(alignment) == len(list(set(alignment))):
                alignment.sort(key=(preference_order+alignment).index)
                alignment = alignment[0]
            else:
                alignment = max(alignment, key=alignment.count)
            column.update({"horizontalAlignment": alignment})

    def columnset(self, columnset: Dict, column_coords: List[List],
                  column_coords_min: List[List],
                  image: Image) -> None:
        """
        Updates the horizontal alignment property for the columnset,
        based on the horizontal alignment of each column inside the columnset.
        @param columnset: Columnset dict
        @param image: input PIL image
        @param column_coords: each column's max coordinates values of a
                              column set

        @param column_coords_min: each column's min coordinates values of a
                                  column set
        """
        preference_order = ["Left", "Center", "Right"]
        alignment = list(map(operator.itemgetter('horizontalAlignment'),
                             columnset["columns"]))
        if len(alignment) == len(list(set(alignment))):
            alignment.sort(key=(preference_order + alignment).index)
            alignment = alignment[0]
        else:
            alignment = max(alignment, key=alignment.count)
        columnset.update({"horizontalAlignment": alignment})
        self.extract_column_width(columnset, column_coords, column_coords_min,
                                  image)
