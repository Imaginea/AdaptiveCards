"""
Command to collect the bleu score metric for the layout generation

Usage :
python3 -m mystique/commands/generate_bleu_score.py --images_path=/image_path \
    --ground_truths_path=/ground_truth_json_path \
    --api_url=url_of_the_service
"""

import argparse
import base64
import collections
import json
import os
import re
from typing import List, Dict

import requests
from nltk import translate
from nltk.translate.bleu_score import sentence_bleu

import configs
from metrics_helper import Helper, AcContainersTrain, AcContainersTest


class Preprocess:
    """
    This class Handles the pre-processing for both ground truth adaptive card
    json and pi2card generated adaptive card json
    """
    helper_object = Helper()

    def pre_process_elements(self, body: List, design_object: Dict) -> None:
        """
        Pre-process the passed adaptive card design element
        @param body: adaptive card json body
        @param design_object: element to be pre-processed
        """

        if (isinstance(design_object, dict) and
                design_object.get("type", "") not in configs.CONTAINERS):
            template_object = None
            if design_object.get("type") == "FactSet":
                design_objects = Helper.factset_to_textbox(self.helper_object,
                                                           design_object)
                body += design_objects
            elif design_object.get("type") == "Input.Toggle":
                template_object = getattr(self.helper_object, "Checkbox")
            else:
                template_object = getattr(self.helper_object,
                                          design_object.get("type"))
            if template_object:
                design_object = template_object(design_object)
                body.append(design_object)
        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.pre_process_elements(body, design_obj)
        else:
            ac_containers = AcContainersTrain(self)
            if design_object.get("type") == "Input.ChoiceSet":
                ac_containers_object = getattr(ac_containers,
                                               "Choiceset")
            else:
                ac_containers_object = getattr(ac_containers,
                                               design_object.get("type", ""))
            ac_containers_object(body, design_object)

    def process_elements_test(self, body: List, design_object: Dict) -> None:
        """
        Process the pic2card generated adaptive card json for pre-processing
        @param body: adaptive card json body
        @param design_object: element to be processed
        """

        if (isinstance(design_object, dict) and
                design_object.get("type", "") not in configs.CONTAINERS):
            if design_object.get("type") == "Image":
                design_object["url"] = ""
            del design_object["horizontalAlignment"]
            design_object = collections.OrderedDict(
                sorted(design_object.items()))
            body.append(design_object)
        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.pre_process_elements(body, design_obj)
        else:
            ac_containers = AcContainersTest(self)
            if design_object.get("type") == "Input.ChoiceSet":
                del design_object["horizontalAlignment"]
                ac_containers_object = getattr(ac_containers,
                                               "Choiceset")
            else:
                del design_object["horizontalAlignment"]
                ac_containers_object = getattr(ac_containers,
                                               design_object.get("type", ""))
            ac_containers_object(body, design_object)

    def _get_card_json(self, image_path: str, api_url: str) -> Dict:
        """
        Fetch the pic2card generated adaptive card json
        @param image_path: image full path
        @param api_url: pic2card api url
        @return: adaptive card json
        """
        base64_string = ""
        with open(image_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode()

        headers = {"Content-Type": "application/json"}
        response = requests.post(url=api_url,
                                 data=json.dumps({"image": base64_string}),
                                 headers=headers)
        response.raise_for_status()
        return response.json().get("card_json").get("card")

    def main(self, api_url=None, images_path=None,
             ground_truths_path=None) -> None:
        """
        Collect and log bleu_score metric for the set of images with their
        ground truths passed.
        @param api_url: pic2card api url
        @param images_path: images path [ directory / image ]
        @param ground_truths_path:  ground truth jsons path
        [ directory / single json file ]
        """

        if ".png" in images_path:
            images = [images_path]
            ground_truths = [ground_truths_path]
        else:
            images = list(sorted(os.listdir(images_path)))
            images = [f"{images_path}/{image}" for image in images]
            ground_truths = list(sorted(os.listdir(ground_truths_path)))
            ground_truths = [f"{ground_truths_path}/{item}"
                             for item in ground_truths]

        avg_score = 0.0
        for ctr, train_image in enumerate(images):
            print(f"\nMetric collection for image: {train_image}..")

            # preprocess train
            print(f"Ground Truth file: {ground_truths[ctr]} ...")
            train = json.loads(open(ground_truths[ctr], "r").read())
            body = []
            self.pre_process_elements(body, train["body"])
            train["body"] = body
            train = collections.OrderedDict(sorted(train.items()))
            train["version"] = "1.3"

            print("Getting pic2card generated adaptive card json....")
            test = self._get_card_json(train_image, api_url)

            # preprocess test
            body = []
            self.process_elements_test(body, test["body"])
            test["body"] = body
            test = collections.OrderedDict(sorted(test.items()))
            test["version"] = "1.3"
            train_corpus = json.dumps(train)
            train_corpus = re.sub(r"[^\w\s\{\}]", "", train_corpus)
            test_corpus = json.dumps(test)
            test_corpus = re.sub(r"[^\w\s\{\}]", "", test_corpus)

            # Get metric
            smoothing = translate.bleu_score.SmoothingFunction().method7
            score = sentence_bleu([train_corpus.lower().split()],
                                  test_corpus.lower().split(),
                                  smoothing_function=smoothing,
                                  weights=(0.5, 0.5))
            if score > 1:
                smoothing = translate.bleu_score.SmoothingFunction().method3
                score = sentence_bleu([train_corpus.lower().split()],
                                      test_corpus.lower().split(),
                                      smoothing_function=smoothing,
                                      weights=(0.5, 0.5))

            print(f"Similarity score for {train_image} is : {score}\n")
            avg_score += score
        print(f"average score = {(avg_score / len(images)) * 100}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect the blue score metric"
                                                 "for layout generation")
    parser.add_argument("--images_path", required=True,
                        help="Enter Image path/ Images directory path")
    parser.add_argument("--ground_truths_path", required=True,
                        help="Enter ground truth card json path/ ground truth "
                             "card json directory path")
    parser.add_argument("--api_url",
                        help="Enter the endpoint of pic2card server, this does "
                             "not support template binding of data",
                        default=None)
    args = parser.parse_args()
    pre_process = Preprocess()
    pre_process.main(images_path=args.images_path,
                     ground_truths_path=args.ground_truths_path,
                     api_url=args.api_url)
