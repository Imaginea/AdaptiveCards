"""Maintains the design templates for the different adaptive card design
element type"""
from typing import Dict


class AdaptiveCardTemplate:
    """
    Design template class for the design objects.
    """

    def __init__(self, design_object):
        self.design_object = design_object

    def textbox(self) -> Dict:
        """
        Returns the design json for the textbox
        @return: design object
        """
        return {
            "type": "TextBlock",
            "text": self.design_object.get("data", ""),
            "size": self.design_object.get("size", ""),
            "horizontalAlignment": self.design_object.get(
                "horizontal_alignment", ""),
            "color": self.design_object.get("color", "Default"),
            "weight": self.design_object.get("weight", ""),
            "wrap": "true"
        }

    def actionset(self) -> Dict:
        """
        Returns the design json for the actionset
        @return: design object
        """
        return {
            "type": "ActionSet",
            # "separator": "true", # Issue in data binding if
            # separator is set to True
            "actions": [{
                "type": "Action.Submit",
                "title": self.design_object.get("data"),
                "style": self.design_object.get("style"),
            }],
            "spacing": "Medium",
            "horizontalAlignment": self.design_object.get(
                "horizontal_alignment", "")
        }

    def image(self) -> Dict:
        """
        Returns the design json for the image
        @return: design object
        """
        return {
            "type": "Image",
            "altText": "Image",
            "horizontalAlignment": self.design_object.get(
                "horizontal_alignment", ""),
            "size": self.design_object.get("size"),
            "url": self.design_object.get("data"),
        }

    def checkbox(self) -> Dict:
        """
        Returns the design json for the checkbox
        @return: design object
        """
        return {
            "type": "Input.Toggle",
            "title": self.design_object.get("data", ""),
            "horizontalAlignment": self.design_object.get(
                "horizontal_alignment", "")
        }

    def richtextbox(self) -> Dict:
        """
        Returns the design json for the richtextbox
        @return: design object
        """
        return {
            "type": "RichTextBlock",
            "inlines": [{
                "type": "TextRun",
                "text": self.design_object.get("data", ""),
                "size": self.design_object.get("size", ""),
                "horizontalAlignment": self.design_object.get(
                    "horizontal_alignment", ""),
                "color": self.design_object.get("color", "Default"),
                "weight": self.design_object.get("weight", ""),
            }]
        }

    def radiobutton(self) -> Dict:
        """
        Returns the design json for the radiobutton
        @return: design object
        """
        choice_set = {
            "type": "Input.ChoiceSet",
            "choices": [],
            "style": "expanded"
        }
        if isinstance(self.design_object, list):
            for design_obj in self.design_object:
                item = {
                    "title": design_obj.get("data", ""),
                    "value": "",
                    "horizontalAlignment": design_obj.get(
                        "horizontal_alignment", "")
                }
                choice_set["choices"].append(item)
        else:
            item = {
                "title": self.design_object.get("data", ""),
                "value": "",
                "horizontalAlignment": self.design_object.get(
                    "horizontal_alignment", "")
            }
            # choice_set["choices"].append(item)
            choice_set = item

        return choice_set

    def columnset(self) -> Dict:
        """
        Returns the design json for the column set container
        @return: design object
        """
        return {
            "type": "ColumnSet",
            "columns": []
        }

    def column(self) -> Dict:
        """
        Returns the design json for the column of the column set container
        @return: design object
        """
        return {
            "type": "Column",
            "width": self.design_object.get(
                "width", ""),

            "items": []
        }

    def imageset(self) -> Dict:
        """
        Returns the design json for the image set container
        @return: design object
        """
        return {
            "type": "ImageSet",
            "imageSize": self.design_object.get("size", ""),
            "images": []
        }

    def choiceset(self) -> Dict:
        return {
            "type": "Input.ChoiceSet",
            "choices": [],
            "style": "expanded"
        }
