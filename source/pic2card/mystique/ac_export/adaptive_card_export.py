"""Module takes care for the exporting of the extracted
   design objects extracted to the expected renderer format"""
from typing import List, Dict, Union
from mystique.ac_export.adaptive_card_templates import (
    AdaptiveCardTemplate)
from mystique.card_layout.ds_templates import (DsTemplate,
                                               ContainerDetailTemplate)
from mystique.ac_export.export_templates import AcContainerExport
from mystique.ac_export.export_templates import TestStringContainersExport


class AdaptiveCardExport:
    """
    Module to export the generalized layout structure to the target platform.
    """

    def __init__(self):
        """
        Initializes the target GUI needed components
        """
        self.body = []
        self.debug_format = []
        self.final_data_structure = []

    def merge_properties(self, properties: List[Dict],
                         design_object: List[Dict]) -> None:
        """
        Merges the design objects with properties with the appropriate layout
        structure with the help of the uuid.
        @param properties: design objects with properties
        @param design_object: layout data structure
        """
        if (isinstance(design_object, dict) and
                design_object.get("object", "") not in DsTemplate().containers):
            extracted_properties = [prop for prop in properties
                                    if prop.get("uuid", "") ==
                                    design_object.get("uuid")][0]
            extracted_properties.pop("coords")
            design_object.update(extracted_properties)

        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.merge_properties(properties, design_obj)
        else:
            container_details_template = ContainerDetailTemplate(design_object)
            container_details_template_object = getattr(
                container_details_template, design_object.get("object", ""))
            self.merge_properties(properties,
                                  container_details_template_object())

    def export_card_body(self, body: List[Dict],
                         design_object: Union[List, Dict]) -> None:
        """
        Recursively generates the adaptive card's body
        from the layout structure.
        @param body: adaptive card json body
        @param design_object: design objects from the layout structure
        """
        if (isinstance(design_object, dict) and
                design_object.get("object", "") not in DsTemplate().containers):
            object_template = AdaptiveCardTemplate(design_object)
            template_object = getattr(object_template,
                                      design_object.get("object", ""))
            body.append(template_object())
        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.export_card_body(body, design_obj)
        else:
            ac_containers = AcContainerExport(design_object, self)
            ac_containers_object = getattr(ac_containers,
                                           design_object.get("object", ""))
            ac_containers_object(body)

    def build_adaptive_card(self, final_data_structure: List[Dict]) -> List:
        """
        Returns the exported adaptive card json
        @param final_data_structure: the generalized layout structure
        @return: adaptive card json body
        """

        self.export_card_body(self.body, final_data_structure)

        y_minimum_final = [c.get("coordinates")[1] for c in
                           final_data_structure]
        body = [value for _, value in sorted(zip(y_minimum_final, self.body),
                                             key=lambda value: value[0])]
        return body

    def export_debug_string(self, debug_format: List,
                            design_object: Union[List, Dict],
                            indentation=None) -> None:
        """
        Recursively generates the testing layout structure string.
        @param debug_format: testing layout structure string
        @param design_object: design objects from the layout structure
        @param indentation: indentation
        """
        if (isinstance(design_object, dict) and
                design_object.get("object", "") not in DsTemplate().containers):
            design_class = design_object.get("class", "")
            if design_object in self.final_data_structure:
                tab_space = "\t" * 0
            else:
                tab_space = "\t" * (indentation + 1)
            debug_format.append(f"{tab_space}item({design_class})\n")
        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.export_debug_string(debug_format, design_obj,
                                         indentation=indentation)
        else:
            export_testing_string_template = TestStringContainersExport(
                design_object, self.final_data_structure, self)
            export_testing_string_template_object = getattr(
                export_testing_string_template,
                design_object.get("object", ""))
            export_testing_string_template_object(debug_format, indentation)

    def build_testing_format(self, final_data_structure: List[Dict]) -> List:
        """
        Returns the exported adaptive card json
        @param final_data_structure: adaptive card body
        @return: testing data-structure format
        """
        y_minimum_final = [c.get("coordinates")[1] for c in
                           final_data_structure]
        final_data_structure = [value for _, value in
                                sorted(zip(y_minimum_final,
                                           final_data_structure),
                                       key=lambda value: value[0])]
        self.final_data_structure = final_data_structure
        self.export_debug_string(self.debug_format,
                                 final_data_structure,
                                 indentation=0)

        return self.debug_format
