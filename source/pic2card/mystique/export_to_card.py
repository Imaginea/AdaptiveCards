from typing import List, Dict, Union
from .design_objects_template import ObjectTemplate


class ExportToTargetPlatform:
    """
    Module to export the generalized layout structure to the target platform.
    """

    def __init__(self):
        """
        Initializes the target GUI format
        """
        self.gui = {
                "type": "AdaptiveCard",
                "version": "1.0",
                "body": [],
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json"
        }
        self.debug_format = []
        self.final_data_structure = []
        self.containers = ['columnset', 'column', 'imageset', 'choiceset']

    def merge_properties(self, properties: List[Dict],
                         design_object: List[Dict]):
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
            merging_template = MergingTemplate(design_object)
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

    def build_adaptive_card(self, final_data_structure: List[Dict]) -> Dict:
        """
        Returns the exported adaptive card json
        @param final_data_structure: the generalized layout structure
        @return: adaptive card json
        """

        self.export_card_body(self.gui["body"], final_data_structure)

        y_minimum_final = [c.get("coordinates")[1] for c in
                           final_data_structure]
        self.gui["body"] = [value for _, value in sorted(zip(y_minimum_final,
                                                         self.gui["body"]),
                                                         key=lambda value:
                                                             value[0])]
        return self.gui

    def export_debug_string(self, debug_format: List,
                            design_object: Union[List, Dict],
                            indentation=None):
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

    """
    def __init__(self, design_object):
        super().__init__()
        self.design_object = design_object

    def columnset(self, body):
        """

        :param body:
        :return:
        """
        object_template = ObjectTemplate(self.design_object.get(
                "properties", {}))
        template_object = getattr(object_template,
                                  self.design_object.get("properties",
                                                         {}).get("object", ""))
        body.append(template_object())
        body = body[-1].get("columns", [])
        self.export_card_body(body, self.design_object.get("row", []))

    def column(self, body):
        """

        :param body:
        :return:
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

    def imageset(self, body):
        """

        :param body:
        :return:
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

    def choiceset(self, body):
        """

        :param body:
        :return:
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

    """
    def __init__(self, design_object, final_data_structure):
        super().__init__()
        self.design_object = design_object
        self.final_data_structure = final_data_structure

    def columnset(self, debug_format, indentation):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        debug_format.append(f"{tab_space}row\n")
        self.export_debug_string(debug_format,
                                 self.design_object.get("row", []),
                                 indentation=indentation)

    def column(self, debug_format, indentation):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        debug_format.append(f"{tab_space}column\n")
        self.export_debug_string(debug_format,
                                 self.design_object.get("column", {}).get(
                                                        "items", []),
                                 indentation=indentation)

    def imageset(self, debug_format, indentation):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        debug_format.append(f"{tab_space}imageset\n")
        self.export_debug_string(debug_format,
                                 self.design_object.get("imageset", {}).get(
                                                       "images", []),
                                 indentation=indentation)

    def choiceset(self, debug_format, indentation):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        if self.design_object in self.final_data_structure:
            tab_space = "\t" * 0
        else:
            tab_space = "\t" * (indentation + 1)
            indentation = indentation + 1
        debug_format.append(f"{tab_space}choiceset\n")
        self.export_debug_string(debug_format,
                                 self.design_object.get("choiceset", {}).get(
                                                        "choices", []),
                                 indentation=indentation)


class MergingTemplate(ExportToTargetPlatform):
    """

    """
    def __init__(self, design_object):
        super().__init__()
        self.design_object = design_object

    def columnset(self):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        return self.design_object.get("row", [])

    def column(self):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        return self.design_object.get("column", {}).get("items", [])

    def imageset(self):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        return self.design_object.get("imageset", {}).get("images", [])

    def choiceset(self):
        """

        :param debug_format:
        :param indentation:
        :return:
        """
        return self.design_object.get("choiceset", {}).get("choices", [])
