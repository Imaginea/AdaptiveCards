"""Module responsible for all the utilities and template classes needed for
the layout generation"""
from typing import List, Tuple, Dict

from mystique.ds_layout.group_design_objects import ImageGrouping
from mystique.ds_layout.group_design_objects import ChoicesetGrouping
from mystique import config


class DsTemplate:
    """
    Base class for layout ds utilities and template handling.
    - handles all utility functions needed for the layout generation
    """

    def __init__(self):
        self.containers = ['columnset', 'column', 'imageset', 'choiceset']

    def add_element_to_ds(self, element_type: str, layout_structure: List,
                          element=None) -> None:
        """
        Adds the design element structure to the layout data structure.
        @param element_type: type of passed design element [ individual /
                             any container]
        @param layout_structure: layout structure where the design element
                                 has to be added
        @param element: design element to be added
        """
        element_structure_templates = DsDesignTemplate(element)
        element_structure_object = getattr(element_structure_templates,
                                           element_type)
        layout_structure.append(element_structure_object())

    def build_container_coordinates(self, coordinates: List) -> Tuple:
        """
        Returns the column set or column coordinates by taking min(x minimum and
        y minimum) and max(x maximum and y maximum) of the respective
        container's element's coordinates.

        @param coordinates: container's list of coordinates
        @return: coordinates of the respective container
        """
        x_minimums = [c[0] for c in coordinates]
        y_minimums = [c[1] for c in coordinates]
        x_maximums = [c[2] for c in coordinates]
        y_maximums = [c[3] for c in coordinates]
        return (min(x_minimums),
                min(y_minimums),
                max(x_maximums),
                max(y_maximums))

    def find_iou(self, coord1, coord2, inter_object=False,
                 columns_group=False) -> List:
        """
        Finds the intersecting bounding boxes by finding
           the highest x and y ranges of the 2 coordinates
           and determine the intersection by deciding weather
           the new xmin > xmax or the new ymin > ymax.
           For non image objects, includes finding the intersection
           area to a threshold to determine intersection

        @param coord1: list of coordinates of 1st object
        @param coord2: list of coordinates of 2nd object
        @param inter_object: check for cleaning between different overlapping
                             objects.

        @param columns_group: If the intersection finding is needed in columns
                              grouping use case

        @return: [True/False, point1 area, point2 area]
        """
        x5 = max(coord1[0], coord2[0])
        y5 = max(coord1[1], coord2[1])
        x6 = min(coord1[2], coord2[2])
        y6 = min(coord1[3], coord2[3])

        # no intersection
        if x6 - x5 <= 0 or y6 - y5 <= 0:
            return [False]

        intersection_area = (x6 - x5) * (y6 - y5)
        point1_area = (coord1[2] - coord1[0]) * (coord1[3] - coord1[1])
        point2_area = (coord2[2] - coord2[0]) * (coord2[3] - coord2[1])
        iou = (intersection_area
               / (point1_area + point2_area - intersection_area))

        # find if given 2 objects intersects or not
        if columns_group:
            if ((point1_area + point2_area - intersection_area == 0)
                    or iou > 0):
                return [True, abs(x6-x5), abs(y6-y5)]
            return [True, abs(x6-x5), abs(y6-y5)]

        # -if iou check is for inter object overlap removal check only for
        # intersection.
        # -if not for inter objects overlap check for iou >= threshold
        # -if the intersection area covers more than 50% of the smaller object
        if ((point1_area + point2_area - intersection_area == 0)
                or (inter_object and iou > 0)
                or (iou >= config.IOU_THRESHOLD)
                or (iou <= config.IOU_THRESHOLD
                    and
                    (intersection_area /
                     min(point1_area, point2_area)) >= 0.50)):
            return [True, point1_area, point2_area]

        return [False]


class DsDesignTemplate:
    """
    Layout structure template for the design elements
    - Handles the template needed for the different design elements for
    the layout generation.
    """

    def __init__(self, design_element):
        self.design_element = design_element

    def item(self) -> Dict:
        """
        Returns the design structure for the individual card design elements
        @return: design structure
        """
        return {
            "object": self.design_element.get("object", ""),
            "data": self.design_element.get("data", ""),
            "class": self.design_element.get("class", ""),
            "uuid": self.design_element.get("uuid"),
            "coordinates": self.design_element.get("coords", ())
        }

    def row(self) -> Dict:
        """
        Returns the design structure for the column-set container
        @return: design structure
        """
        return {
            "object": "columnset",
            "row": [],
        }

    def column(self) -> Dict:
        """
        Returns the design structure for the column of the column-set container
        @return: design structure
        """
        return {
            "column": {"items": []},
            "object": "column"
        }

    def imageset(self) -> Dict:
        """
        Returns the design structure for the image-set container
        @return: design structure
        """
        return {
            "imageset": {"items": []},
            "object": "imageset"
        }

    def choiceset(self) -> Dict:
        """
        Returns the design structure for the choice-set container
        @return: design structure
        """
        return {
            "choiceset": {"items": []},
            "object": "choiceset"
        }


class ContainerGroupTemplate:
    """
    Class to handle different container groupings other than columnset and
    column.
    - Handles the functionalies needed for different type of container
    groupings.
    """
    def __init__(self, other_containers_group):
        self.other_containers_group = other_containers_group

    def imageset(self, layout_structure: List[Dict]) -> List[Dict]:
        """
        Groups and returns the layout structure with the respective image-sets
        @param layout_structure: Un-grouped layout structure.
        @return: Grouped layout structure
        """
        image_grouping = ImageGrouping(self)
        condition = image_grouping.imageset_condition
        self.other_containers_group.container_grouping_inside_column(
            layout_structure, 5, "imageset", image_grouping, condition, 0)
        items, _ = self.other_containers_group.collect_items_for_container(
            layout_structure, 5)
        return self.other_containers_group.merge_grouped_in_layout(
            items, layout_structure, "imageset", image_grouping, condition, 0)

    def choiceset(self, layout_structure: List[Dict]) -> List[Dict]:
        """
        Groups and returns the layout structure with the respective choice-sets
        @param layout_structure: Un-grouped layout structure.
        @return: Grouped layout structure
        """
        choice_grouping = ChoicesetGrouping(self)
        condition = choice_grouping.choiceset_condition
        self.other_containers_group.container_grouping_inside_column(
            layout_structure, 2, "choiceset", choice_grouping, condition, 1)
        items, _ = self.other_containers_group.collect_items_for_container(
            layout_structure, 2)
        return self.other_containers_group.merge_grouped_in_layout(
            items, layout_structure, "choiceset", choice_grouping, condition, 1)


class ContainerDetailTemplate:
    """
    This module is responsible for returning the inner design objects for a
    given container from the generated layout structure
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
        return self.design_object.get("imageset", {}).get("items", [])

    def choiceset(self) -> List:
        """
        Returns the design objects of a choice-set container for the given
        layout structure.
        """
        return self.design_object.get("choiceset", {}).get("items", [])
