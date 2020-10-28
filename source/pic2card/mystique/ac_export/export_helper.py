"""Module maintains the needed design and exporting templates and utilities
 for target rendering"""
from typing import List, Dict

from .adaptive_card_templates import AdaptiveCardTemplate
from mystique.card_layout.ds_helper import DsHelper
from ..card_layout.ds_helper import ContainerDetailTemplate


def merge_properties(properties: List[Dict],
                     design_object: List[Dict],
                     container_details_object: ContainerDetailTemplate) -> None:
    """
    Merges the design objects with properties with the appropriate layout
    structure with the help of the uuid.
    @param properties: design objects with properties
    @param design_object: layout data structure
    @param container_details_object: ContainerDetailsTemplate object
    """
    if (isinstance(design_object, dict) and
            design_object.get("object", "") not in DsHelper().containers):
        extracted_properties = [prop for prop in properties
                                if prop.get("uuid", "") ==
                                design_object.get("uuid")][0]
        extracted_properties.pop("coords")
        design_object.update(extracted_properties)

    elif isinstance(design_object, list):
        for design_obj in design_object:
            merge_properties(properties, design_obj, container_details_object)
    else:
        container_details_template_object = getattr(
            container_details_object, design_object.get("object", ""))
        merge_properties(properties,
                         container_details_template_object(design_object),
                         container_details_object)


class AcContainerExport:
    """
    This class is responsible for calling the appropriate design templates
    for the container structure.
    """
    def __init__(self, design_object, export_object):
        self.design_object = design_object
        self.export_object = export_object
        self.object_template = AdaptiveCardTemplate()

    def columnset(self, body) -> None:
        """
        Returns the design element template for the column-set container
        @param body: design element's layout structure
        """
        template_object = getattr(self.object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object(self.design_object))
        body = body[-1].get("columns", [])
        self.export_object.export_card_body(body,
                                            self.design_object.get("row", []))

    def column(self, body) -> None:
        """
        Returns the design element template for the column container
        @param body: design element's layout structure
        """
        template_object = getattr(self.object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object(self.design_object))
        body = body[-1].get("items", [])
        self.export_object.export_card_body(
            body, self.design_object.get("column", {}).get("items", []))

    def imageset(self, body) -> None:
        """
        Returns the design element template for the image-set container
        @param body: design element's layout structure
        """
        template_object = getattr(self.object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object(self.design_object))
        body = body[-1].get("images", [])
        self.export_object.export_card_body(
            body, self.design_object.get("imageset", {}).get("items", []))

    def choiceset(self, body) -> None:
        """
        Returns the design element template for the choice-set container
        @param body: design element's layout structure
        """
        template_object = getattr(self.object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object(self.design_object))
        body = body[-1].get("choices", [])
        self.export_object.export_card_body(
            body, self.design_object.get("choiceset", {}).get("items", []))
