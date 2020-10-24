"""Module responsible for grouping the related row of elements and to it's
respective columns"""
from typing import List, Dict

from mystique.ds_layout.group_design_objects import ColumnsGrouping
from mystique.ds_layout.ds_templates import DsTemplate
from mystique.extract_properties import CollectProperties


class RowColumnGroup:
    """
    Groups the predicted design elements into it's related rows and columns
    and generates a hiearchical data structure of grouped elements
    i.e into a column-set container as per adaptive card's notation
    """
    same_iteration = False

    def __init__(self):
        self.collect_properties = CollectProperties()

    def check_same_iteration(self, previous: List[Dict],
                             current: List[Dict]) -> bool:
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
        columns_grouping = ColumnsGrouping(
            collect_properties=CollectProperties())
        column_sets = columns_grouping.object_grouping(
            design_objects, columns_grouping.columns_condition)
        ds_template = DsTemplate()
        for column_set in column_sets:
            if len(column_set) == 1:
                ds_template.add_element_to_ds("item", layout_data_structure,
                                              element=column_set[0])
            if len(column_set) > 1:
                columns = columns_grouping.object_grouping(
                    column_set, columns_grouping.columns_row_condition)
                ds_template.add_element_to_ds("row", layout_data_structure)
                row_counter = len(layout_data_structure) - 1
                for column in columns:
                    if len(column) == 1:
                        row_columns = layout_data_structure[row_counter]["row"]
                        ds_template.add_element_to_ds("column", row_columns)
                        ds_template.add_element_to_ds(
                            "item",
                            row_columns[-1]["column"]["items"],
                            element=column[0])
                        layout_data_structure[row_counter]["row"][-1][
                            "coordinates"] = column[0].get("coords")
                    else:
                        row_columns = layout_data_structure[row_counter]["row"]
                        if not self.check_same_iteration(previous_column,
                                                         column):
                            ds_template.add_element_to_ds("column", row_columns)
                            column_counter = len(row_columns) - 1
                            self.column_set_container_grouping(
                                column,
                                row_columns[column_counter]["column"]["items"],
                                previous_column=column)
                            if self.same_iteration:
                                layout_data_structure[row_counter][
                                    "row"][column_counter]["column"][
                                        "items"] = row_columns[column_counter][
                                            "column"]["items"][:-1]
                                for item in column:
                                    ds_template.add_element_to_ds(
                                        "item",
                                        row_columns[column_counter]
                                        ["column"].get("items", []),
                                        element=item)

                                self.same_iteration = False

                            coordinates = [c.get("coordinates") for c in
                                           row_columns[column_counter][
                                               "column"]["items"]
                                           ]
                            layout_data_structure[row_counter]["row"][
                                column_counter]["coordinates"] = \
                                ds_template.build_container_coordinates(
                                    coordinates)

                            column_y_minimums = [c.get("coordinates")[1]
                                                 for c in row_columns[
                                                     column_counter][
                                                         "column"]["items"]]

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
                        coordinates = [c.get("coordinates") for c in
                                       layout_data_structure[row_counter]["row"]
                                       ]
                        layout_data_structure[row_counter]["coordinates"] = \
                            ds_template.build_container_coordinates(
                                coordinates)
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
