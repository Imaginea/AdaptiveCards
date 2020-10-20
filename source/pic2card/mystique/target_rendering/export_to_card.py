"""Module takes care for the exporting of the extracted
   design objects extracted to the expected renderer format"""
from typing import List, Dict, Union
from mystique.target_rendering.design_objects_template import ObjectTemplate


class ExportToTargetPlatform:
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
        self.containers = ['columnset', 'column', 'imageset', 'choiceset']

    def merge_properties(self, properties: List[Dict],
                         design_object: List[Dict]) -> None:
        """
        Merges the design objects with properties with the appropriate layout
        structure with the help of the uuid.
        @param properties: design objects with properties
        @param design_object: layout data structure
        """
        if isinstance(design_object, dict) and design_object.get(
                "properties", {}).get("object", "") not in self.containers:
            extracted_properties = [prop for prop in properties if
                                    prop.get("uuid", "") == design_object.get(
                                        "properties", {}).get("uuid")][0]
            design_object.get("properties", {}).update(extracted_properties)

        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.merge_properties(properties, design_obj)
        else:
            merging_template = ContainerDetailTemplate(design_object)
            merging_template_object = getattr(merging_template,
                                              design_object.get(
                                                  "properties", {}).get(
                                                      "object", ""))
            self.merge_properties(properties, merging_template_object())

    def export_card_body(self, body: List[Dict],
                         design_object: Union[List, Dict]) -> None:
        """
        Recursively generates the adaptive card's body
        from the layout structure.
        @param body: adaptive card json body
        @param design_object: design objects from the layout structure
        """
        if isinstance(design_object, dict) and design_object.get(
                "properties", {}).get("object", "") not in self.containers:
            object_template = ObjectTemplate(design_object.get(
                "properties", {}))
            template_object = getattr(object_template, design_object.get(
                "properties", {}).get("object", ""))
            body.append(template_object())
        elif isinstance(design_object, list):
            for design_obj in design_object:
                self.export_card_body(body, design_obj)
        else:
            export_template = ExportingCardTemplate(design_object)
            export_template_object = getattr(export_template, design_object.get(
                "properties", {}).get("object", ""))
            export_template_object(body)

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
        if isinstance(design_object, dict) and design_object.get(
                "properties", {}).get("object", "") not in self.containers:
            design_class = design_object.get("properties", {}).get("class", "")
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
            export_testing_string_template = ExportingTestingStringTemplate(
                design_object, self.final_data_structure)
            export_testing_string_template_object = getattr(
                export_testing_string_template,
                design_object.get("properties", {}).get("object", ""))
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


class ExportingCardTemplate(ExportToTargetPlatform):
    """
    This class is responsible for calling the appropriate design templates
    for the container structure.
    """
    def __init__(self, design_object):
        super().__init__()
        self.design_object = design_object

    def columnset(self, body) -> None:
        """
        Returns the design element template for the column-set container
        @param body: design element's layout structure
        """
        object_template = ObjectTemplate(self.design_object.get(
            "properties", {}))
        template_object = getattr(object_template,
                                  self.design_object.get("properties",
                                                         {}).get("object", ""))
        body.append(template_object())
        body = body[-1].get("columns", [])
        self.export_card_body(body, self.design_object.get("row", []))

    def column(self, body) -> None:
        """
        Returns the design element template for the column container
        @param body: design element's layout structure
        """
        object_template = ObjectTemplate(self.design_object.get(
            "properties", {}))
        template_object = getattr(object_template,
                                  self.design_object.get("properties",
                                                         {}).get("object", ""))
        body.append(template_object())
        body = body[-1].get("items", [])
        self.export_card_body(body, self.design_object.get("column",
                                                           {}).get("items", []))

    def imageset(self, body) -> None:
        """
        Returns the design element template for the image-set container
        @param body: design element's layout structure
        """
        object_template = ObjectTemplate(self.design_object.get(
            "properties", {}))
        template_object = getattr(object_template,
                                  self.design_object.get("properties",
                                                         {}).get("object", ""))
        body.append(template_object())
        body = body[-1].get("images", [])
        self.export_card_body(body, self.design_object.get("imageset",
                                                           {}).get("images",
                                                                   []))

    def choiceset(self, body) -> None:
        """
        Returns the design element template for the choice-set container
        @param body: design element's layout structure
        """
        object_template = ObjectTemplate(self.design_object.get(
            "properties", {}))
        template_object = getattr(object_template,
                                  self.design_object.get("properties",
                                                         {}).get("object", ""))
        body.append(template_object())
        body = body[-1].get("choices", [])
        self.export_card_body(body, self.design_object.get("choiceset",
                                                           {}).get("choices",
                                                                   []))


class ExportingTestingStringTemplate(ExportToTargetPlatform):
    """
    This class is responsible for calling the appropriate testing templates
    for the container structure.
    """
    def __init__(self, design_object, final_data_structure):
        super().__init__()
        self.design_object = design_object
        self.final_data_structure = final_data_structure

    def columnset(self, testing_string, indentation) -> None:
        """
        Returns the testing string for the column-set container
        @param testing_string: list of testing string for the given design
        @param indentation: needed indentation for design element in the
                            testing string
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        testing_string.append(f"{tab_space}row\n")
        self.export_debug_string(testing_string,
                                 self.design_object.get("row", []),
                                 indentation=indentation)

    def column(self, testing_string, indentation) -> None:
        """
        Returns the testing string for the column container
        @param testing_string: list of testing string for the given design
        @param indentation: needed indentation for design element in the
                            testing string
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        testing_string.append(f"{tab_space}column\n")
        self.export_debug_string(testing_string,
                                 self.design_object.get("column", {}).get(
                                     "items", []),
                                 indentation=indentation)

    def imageset(self, testing_string, indentation) -> None:
        """
        Returns the testing string for the image-set container
        @param testing_string: list of testing string for the given design
        @param indentation: needed indentation for design element in the
                            testing string
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        testing_string.append(f"{tab_space}imageset\n")
        self.export_debug_string(testing_string,
                                 self.design_object.get("imageset", {}).get(
                                     "images", []),
                                 indentation=indentation)

    def choiceset(self, testing_string, indentation) -> None:
        """
        Returns the testing string for the image-set container
        @param testing_string: list of testing string for the given design
        @param indentation: needed indentation for design element in the
                            testing string
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        testing_string.append(f"{tab_space}choiceset\n")
        self.export_debug_string(testing_string,
                                 self.design_object.get("choiceset", {}).get(
                                     "choices", []),
                                 indentation=indentation)


class ContainerDetailTemplate(ExportToTargetPlatform):
    """
    This module is responsible for returning the inner design objects for a
    given container
    """
    def __init__(self, design_object):
        super().__init__()
        self.design_object = design_object

    def columnset(self) -> List:
        """
        Returns the design objects of a column-set container for the given
        layout structure.
        """
        return self.design_object.get("row", [])

    def column(self) -> List:
        """
        Returns the design objects of a column container for the given
        layout structure.
        """
        return self.design_object.get("column", {}).get("items", [])

    def imageset(self) -> List:
        """
        Returns the design objects of a image-set container for the given
        layout structure.
        """
        return self.design_object.get("imageset", {}).get("images", [])

    def choiceset(self) -> List:
        """
        Returns the design objects of a choice-set container for the given
        layout structure.
        """
        return self.design_object.get("choiceset", {}).get("choices", [])
