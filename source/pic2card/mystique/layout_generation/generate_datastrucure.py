"""Module responsible for the hierarchical layout structure generation from the
   extracted design objects with the help of the spatial details from the
   image model"""
from typing import List, Dict, Tuple, Union

from .group_design_objects import ColumnsGrouping
from .group_design_objects import ImageGrouping
from .group_design_objects import ChoicesetGrouping
from mystique.export_to_target.design_objects_template import (
    ElementStructureTemplate)


class GenerateLayoutDataStructure:
    """
    Module to generate a layout structure for the GUI design.
    - Handles all grouping of elements into the respective containers.
    - Generating a generalized data structure for the layout representation
      containing all the positional information of each design element.
    """
    same_iteration = False

    def group_column_set(self, design_objects: List[Dict]) -> List[List[Dict]]:
        """
        Returns the grouped column set objects
        @param design_objects: design objects to be grouped
        @return: grouped list of design objects
        """
        columns_grouping = ColumnsGrouping(self)
        column_sets = columns_grouping.object_grouping(
                design_objects,
                columns_grouping.columns_condition)
        return column_sets

    def group_columns(self, design_objects: List[Dict]) -> List[List[Dict]]:
        """
        Returns the grouped column objects
        @param design_objects: design objects to be grouped
        @return: grouped list of design objects
        """

        columns_grouping = ColumnsGrouping(self)

        columns = columns_grouping.object_grouping(
                design_objects,
                columns_grouping.columns_row_condition
        )
        return columns

    def extract_coordinates(self, layout_structure: List[Dict]) -> Tuple:
        """
        Returns the column set or column coordinates by taking min(x minimum and
        y minimum) and max(x maximum and y maximum) of the respective
        container's element's coordinates.

        @param layout_structure: container's list of elements
        @return: coordinates of the respective container
        """

        coordinates = [c.get("coordinates") for c in layout_structure]
        x_minimums = [c[0] for c in coordinates]
        y_minimums = [c[1] for c in coordinates]
        x_maximums = [c[2] for c in coordinates]
        y_maximums = [c[3] for c in coordinates]
        return (min(x_minimums),
                min(y_minimums),
                max(x_maximums),
                max(y_maximums))

    def add_element(self, element_type: str, layout_structure: List,
                    element=None) -> None:
        """
        Adds the design element structure to the layout data structure.
        @param element_type: type of passed design element [ individual /
                             any container]
        @param layout_structure: layout structure where the design element
                                 has to be added
        @param element: design element to be added
        """
        element_structure_templates = ElementStructureTemplate(element)
        element_structure_object = getattr(element_structure_templates,
                                           element_type)
        layout_structure.append(element_structure_object())

    def check_equals(self, previous: List[Dict], current: List[Dict]) -> bool:
        """
        Checks the if the previous and current grouped column have same
        objects or not.
        @param previous: Previous column objects
        @param current: Current column objects
        @return: Boolean value of the check
        """
        if not previous:
            return False
        same = True
        for item in current:
            if item not in previous:
                same = False
                break
        return same

    def column_set_container_grouping(self, design_objects,
                                      layout_data_structure:
                                      List[Dict],
                                      previous_column=None
                                      ) -> None:
        """
        Group the detected design elements recursively
        into columns and column_sets and individual objects, considering each
        columns as smallest unit [i.e. a separate card hierarchy].
        @param design_objects: list of detected design objects
        @param layout_data_structure: layout data structure
        @param previous_column: previous grouped column objects to check for
                                same grouping happening repeatedly 
        """
        column_sets = self.group_column_set(design_objects)
        for ctr, column_set in enumerate(column_sets):
            if len(column_set) == 1:
                self.add_element("individual", layout_data_structure,
                                 element=column_set[0])
            if len(column_set) > 1:
                columns = self.group_columns(column_set)
                self.add_element("column_set", layout_data_structure)
                row_counter = len(layout_data_structure) - 1
                for ctr1, column in enumerate(columns):
                    if len(column) == 1:
                        self.add_element("column",
                                         layout_data_structure[row_counter][
                                             "row"])
                        self.add_element("individual",
                                         layout_data_structure[row_counter][
                                          "row"][-1].get("column",
                                                         {}).get("items", []),
                                         element=column[0])
                        layout_data_structure[row_counter]["row"][-1][
                            "coordinates"] = column[0].get("coords")
                    else:
                        if not self.check_equals(previous_column, column):
                            self.add_element("column",
                                             layout_data_structure[row_counter][
                                                 "row"])
                            column_counter = len(layout_data_structure[
                                                  row_counter]["row"]) - 1
                            self.column_set_container_grouping(
                                    column,
                                    layout_data_structure[row_counter]["row"][
                                        column_counter]["column"]["items"],
                                    previous_column=column)
                            if self.same_iteration:
                                layout_data_structure[row_counter]["row"][
                                    column_counter]["column"][
                                    "items"] = layout_data_structure[
                                                row_counter]["row"][
                                                column_counter]["column"][
                                                "items"][:-1]
                                for item in column:
                                    self.add_element("individual",
                                                     layout_data_structure[
                                                         row_counter][
                                                         "row"][
                                                         column_counter][
                                                         "column"].get("items",
                                                                       []),
                                                     element=item)

                                self.same_iteration = False
                            layout_data_structure[row_counter]["row"][
                                column_counter][
                                "coordinates"] = self.extract_coordinates(
                                    layout_data_structure[row_counter]["row"][
                                        column_counter]["column"]["items"])

                            column_y_minimums = [c.get("coordinates")[1]
                                                 for c in layout_data_structure[
                                                     row_counter]["row"][
                                                     column_counter]["column"][
                                                     "items"]]

                            layout_data_structure[row_counter]["row"][
                                column_counter]["column"]["items"] = [
                                    value for _, value in sorted(
                                            zip(column_y_minimums,
                                                layout_data_structure[
                                                    row_counter]["row"][
                                                    column_counter][
                                                    "column"]["items"]),
                                            key=lambda value: value[0])]
                        else:
                            self.same_iteration = True

                    if not self.same_iteration:
                        layout_data_structure[row_counter][
                            "coordinates"] = self.extract_coordinates(
                                layout_data_structure[row_counter]["row"])
                        row_counter = len(layout_data_structure) - 1
                        row_x_minimums = [c.get("coordinates")[0] for c in
                                          layout_data_structure[row_counter][
                                              "row"]]
                        layout_data_structure[row_counter]["row"] = [
                                value for _, value in sorted(
                                        zip(row_x_minimums,
                                            layout_data_structure[
                                              row_counter]["row"]),
                                        key=lambda value: value[0])]

    def get_items(self, layout_structure: List[Dict],
                  object_class: int) -> [List, List]:
        """
        Gets the list of individual design items of a given container
        @param layout_structure: Container of design elements
        @param object_class: type of the design elements to be returned

        @return: The list design elements of given type and the list of
                 other elements inside the passed container
        """
        items = []
        for design_object in layout_structure:
            if design_object.get("properties", {}).get(
                    "class", 0) == object_class:
                items.append(design_object)
        remaining_items = [design_object for design_object in layout_structure
                           if design_object not in items]
        return items, remaining_items

    def group_objects(self, design_items: List[Dict],
                      layout_structure: List[Dict], object_type: str,
                      grouping_object: Union[ImageGrouping,
                                             ChoicesetGrouping],
                      grouping_condition: bool,
                      order_key: int) -> List[Dict]:
        """
        Returns the grouped layout structure for the given grouping object
        @param design_items: list of design items to be grouped.
        @param layout_structure: the container structure where the design
                                 elements needs to be grouped
        @param object_type: type of grouping
        @param grouping_object: grouping logic object
        @param grouping_condition: grouping condition for the given type
        @param order_key: positional key for the container by which it has to
                          be sorted [ x-way or y-way ]
        @return: The new layout structure after grouping
        """

        groups = grouping_object.object_grouping(
                design_items, grouping_condition)
        for group in groups:
            if len(group) > 1:
                sorted_group = []
                for item in group:
                    if group.count(item) == 1:
                        sorted_group.append(item)
                    elif group.count(item) > 1 and item not in sorted_group:
                        sorted_group.append(item)
                group = sorted_group
                self.add_element(object_type, layout_structure)
                coordinates = []
                key = [key for key, values in
                       layout_structure[-1][object_type].items()
                       if isinstance(values, list)][0]
                for item in group:
                    layout_structure[-1][
                        object_type][key].append(item)
                    coordinates.append(item.get("coordinates", []))

                layout_structure[-1][
                    "coordinates"] = self.extract_coordinates(
                        layout_structure[-1][object_type][key])
                order_values = [c[order_key] for c in coordinates]
                layout_structure[-1][object_type][key] = [
                        value for _, value in sorted(
                                zip(order_values,
                                    layout_structure[-1][object_type][key]),
                                key=lambda value: value[0])]

                layout_structure = [item for item in
                                    layout_structure if item not in group]
        return layout_structure

    def other_grouping_for_columns(self, layout_structure: List[Dict],
                                   object_class: int,
                                   grouping_type: str,
                                   grouping_object: Union[ImageGrouping,
                                                          ChoicesetGrouping],
                                   grouping_condition: bool,
                                   order_key: int
                                   ) -> None:
        """
        Calls the object grouping for list of design element inside a particular
        column.
        @param layout_structure: the generated layout structure
        @param object_class: The class value of the grouping container
        @param grouping_type: The name of the container type
        @param grouping_object: The object of the respective grouping class
        @param grouping_condition: The condition needed for the respective
                                   container grouping
        @param order_key:positional key for the container by which it has to
                          be sorted [ x-way or y-way ]
        """

        for row_counter, design_object in enumerate(layout_structure):
            if design_object.get("properties", {}).get("object") == "columnset":
                columns = design_object.get("row", [])
                for column_counter, column_item in enumerate(columns):
                    items, remaining_items = self.get_items(
                        column_item.get("column", {}).get("items", []),
                        object_class)
                    remaining_items = [remaining_item
                                       for remaining_item in remaining_items
                                       if design_object.get("properties",
                                                            {}).get(
                                        "object") == "columnset"]
                    layout_structure[row_counter][
                        "row"][column_counter][
                        "column"]["items"] = self.group_objects(
                            items, layout_structure[row_counter][
                             "row"][column_counter]["column"]["items"],
                            grouping_type, grouping_object, grouping_condition,
                            order_key)
                    column_y_minimums = [c.get("coordinates")[1]
                                         for c in layout_structure[
                                             row_counter]["row"][
                                             column_counter]["column"][
                                             "items"]]
                    layout_structure[row_counter]["row"][
                        column_counter]["column"]["items"] = [
                            value for _, value in sorted(
                                    zip(column_y_minimums,
                                        layout_structure[
                                                row_counter]["row"][
                                                column_counter][
                                                "column"]["items"]),
                                    key=lambda value: value[0])]

                    if remaining_items:
                        self.other_grouping_for_columns(layout_structure[
                            row_counter]["row"][column_counter]["column"][
                            "items"], object_class, grouping_type,
                                grouping_object, grouping_condition, order_key)

    def other_containers_grouping(self,
                                  layout_structure: List[Dict]) -> List[Dict]:
        """
        Calls the object grouping for list of design element in the root level
        of the design.
        @param layout_structure: the generated layout structure
        @return: Grouped layout structure
        """

        # image set grouping
        image_grouping = ImageGrouping(self)
        condition = image_grouping.imageset_condition
        self.other_grouping_for_columns(layout_structure, 5, "imageset",
                                        image_grouping, condition, 0)
        items, _ = self.get_items(layout_structure, 5)
        layout_structure = self.group_objects(items, layout_structure,
                                              "imageset",
                                              image_grouping, condition, 0)
        # choice set grouping
        choice_grouping = ChoicesetGrouping(self)
        condition = choice_grouping.choiceset_condition
        self.other_grouping_for_columns(layout_structure, 2, "choiceset",
                                        choice_grouping, condition, 1)
        items, _ = self.get_items(layout_structure, 2)
        layout_structure = self.group_objects(items, layout_structure,
                                              "choiceset",
                                              choice_grouping, condition, 1)

        return layout_structure
