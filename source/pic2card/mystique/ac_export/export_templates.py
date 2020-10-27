"""Module maintains the needed design and exporting templates and utilities
 for target rendering"""
from mystique.ac_export.adaptive_card_templates import AdaptiveCardTemplate


class AcContainerExport:
    """
    This class is responsible for calling the appropriate design templates
    for the container structure.
    """
    def __init__(self, design_object, export_object):
        self.design_object = design_object
        self.export_object = export_object

    def columnset(self, body) -> None:
        """
        Returns the design element template for the column-set container
        @param body: design element's layout structure
        """
        object_template = AdaptiveCardTemplate(self.design_object)
        template_object = getattr(object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object())
        body = body[-1].get("columns", [])
        self.export_object.export_card_body(body,
                                            self.design_object.get("row", []))

    def column(self, body) -> None:
        """
        Returns the design element template for the column container
        @param body: design element's layout structure
        """
        object_template = AdaptiveCardTemplate(self.design_object)
        template_object = getattr(object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object())
        body = body[-1].get("items", [])
        self.export_object.export_card_body(
            body, self.design_object.get("column", {}).get("items", []))

    def imageset(self, body) -> None:
        """
        Returns the design element template for the image-set container
        @param body: design element's layout structure
        """
        object_template = AdaptiveCardTemplate(self.design_object)
        template_object = getattr(object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object())
        body = body[-1].get("images", [])
        self.export_object.export_card_body(
            body, self.design_object.get("imageset", {}).get("items", []))

    def choiceset(self, body) -> None:
        """
        Returns the design element template for the choice-set container
        @param body: design element's layout structure
        """
        object_template = AdaptiveCardTemplate(self.design_object)
        template_object = getattr(object_template,
                                  self.design_object.get("object", ""))
        body.append(template_object())
        body = body[-1].get("choices", [])
        self.export_object.export_card_body(
            body, self.design_object.get("choiceset", {}).get("items", []))


class TestStringContainersExport:
    """
    This class is responsible for calling the appropriate testing templates
    for the container structure.
    """
    def __init__(self, design_object, final_data_structure, export_object):
        self.design_object = design_object
        self.final_data_structure = final_data_structure
        self.export_object = export_object

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
        self.export_object.export_debug_string(
            testing_string,
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
        self.export_object.export_debug_string(
            testing_string,
            self.design_object.get("column", {}).get("items", []),
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
        self.export_object.export_debug_string(
            testing_string,
            self.design_object.get("imageset", {}).get("items", []),
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
        self.export_object.export_debug_string(
            testing_string,
            self.design_object.get("choiceset", {}).get("items", []),
            indentation=indentation)
