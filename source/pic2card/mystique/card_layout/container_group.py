"""Module responsible for the grouping of other containers [ other than
column-set]"""
from typing import List, Dict, Union

from mystique.card_layout.objects_group import ChoicesetGrouping
from mystique.card_layout.objects_group import ImageGrouping
from mystique.card_layout.ds_templates import DsTemplate, ContainerGroupTemplate


class ContainerGroup:
    """
    Helps in grouping a set of similar design elements inside a column of
    or in the root level of the card layout design
    """

    def collect_items_for_container(self, layout_structure: List[Dict],
                                    object_class: int) -> [List, List]:
        """
        Gets the list of individual design items of a given type of container
        from the passed layout structure.
        @param layout_structure: Container of design elements
        @param object_class: type of the design elements to be returned

        @return: The list design elements of given type and the list of
                 other elements inside the passed container
        """
        items = []
        for design_object in layout_structure:
            if design_object.get("class", 0) == object_class:
                items.append(design_object)
        remaining_items = [design_object for design_object in layout_structure
                           if design_object not in items]
        return items, remaining_items

    def merge_grouped_in_layout(self, design_items: List[Dict],
                                layout_structure: List[Dict],
                                object_type: str,
                                grouping_object: Union[ImageGrouping,
                                                       ChoicesetGrouping],
                                grouping_condition: bool,
                                order_key: int) -> List[Dict]:
        """
        Returns the grouped layout structure for the given grouping object type
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

        groups = grouping_object.object_grouping(design_items,
                                                 grouping_condition)
        ds_template = DsTemplate()
        for group in groups:
            if len(group) > 1:
                sorted_group = []
                for item in group:
                    if group.count(item) == 1:
                        sorted_group.append(item)
                    elif group.count(item) > 1 and item not in sorted_group:
                        sorted_group.append(item)
                group = sorted_group
                ds_template.add_element_to_ds(object_type, layout_structure)
                coordinates = []
                key = [key for key, values in
                       layout_structure[-1][object_type].items()
                       if isinstance(values, list)][0]
                for item in group:
                    layout_structure[-1][
                        object_type][key].append(item)
                    coordinates.append(item.get("coordinates", []))

                container_coords = [c.get("coordinates")
                                    for c in layout_structure[-1][
                                        object_type][key]]
                layout_structure[-1][
                    "coordinates"] = ds_template.build_container_coordinates(
                        container_coords)
                order_values = [c[order_key] for c in coordinates]
                layout_structure[-1][object_type][key] = [
                    value for _, value in sorted(
                        zip(order_values,
                            layout_structure[-1][object_type][key]),
                        key=lambda value: value[0])]

                layout_structure = [item for item in
                                    layout_structure if item not in group]
        return layout_structure

    def container_grouping_inside_column(self, layout_structure: List[Dict],
                                         object_class: int,
                                         grouping_type: str,
                                         grouping_object: Union[
                                             ImageGrouping, ChoicesetGrouping],
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
            if design_object.get("object") == "columnset":
                columns = design_object.get("row", [])
                for column_counter, column_item in enumerate(columns):
                    items, remaining_items = self.collect_items_for_container(
                        column_item.get("column", {}).get("items", []),
                        object_class)
                    remaining_items = [
                        remaining_item
                        for remaining_item in remaining_items
                        if design_object.get("object") == "columnset"]

                    row_columns = layout_structure[row_counter]["row"]
                    layout_structure[row_counter]["row"][column_counter][
                        "column"]["items"] = self.merge_grouped_in_layout(
                            items, row_columns[column_counter][
                                "column"]["items"],
                            grouping_type, grouping_object,
                            grouping_condition,
                            order_key)
                    column_y_minimums = [c.get("coordinates")[1]
                                         for c in row_columns[column_counter][
                                             "column"]["items"]]
                    layout_structure[row_counter]["row"][
                        column_counter]["column"]["items"] = [
                            value for _, value in sorted(
                                zip(column_y_minimums,
                                    row_columns[column_counter]["column"][
                                        "items"]),
                                key=lambda value: value[0])]

                    if remaining_items:
                        self.container_grouping_inside_column(
                            row_columns[column_counter]["column"]["items"],
                            object_class,
                            grouping_type,
                            grouping_object,
                            grouping_condition,
                            order_key)

    def containers_grouping(self, layout_structure: List[Dict]) -> List[Dict]:
        """
        Calls the object grouping for list of design element in the root level
        of the design.
        @param layout_structure: the generated layout structure
        @return: Grouped layout structure
        """
        other_containers = DsTemplate().containers
        other_containers = [container_name
                            for container_name in other_containers
                            if container_name not in ['columnset', 'column']]
        other_template_grouping = ContainerGroupTemplate(self)
        for container_name in other_containers:
            other_template_grouping_object = getattr(other_template_grouping,
                                                     container_name)
            layout_structure = other_template_grouping_object(layout_structure)

        return layout_structure
