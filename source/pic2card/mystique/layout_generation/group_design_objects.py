"""Module for grouping deisgn objects into different containers"""
from operator import itemgetter
from typing import List, Dict, Callable, Tuple, Optional, Any

from mystique import config
from mystique.extract_properties import CollectProperties


class GroupObjects:
    """
    Handles the grouping of given list of objects for any set conditions that
    is passed.
    """
    def max_min_difference(self, coordinates_1: Any,
                           coordinates_2: Any, way: str) -> float:
        """
        Returns the ymax-ymin difference of the 2 deisgn objects

        @param coordinates_1: design object one's coordinates
        @param coordinates_2: design object two's coordinates
        @param way: xmax-xmin or ymax-ymin difference

        @return: max-min difference ratios
        """
        if isinstance(coordinates_1, dict) and isinstance(coordinates_2, dict):
            coordinates_1 = [coordinates_1.get("xmin"),
                             coordinates_1.get("ymin"),
                             coordinates_1.get("xmax"),
                             coordinates_1.get("ymax")]
            coordinates_2 = [coordinates_2.get("xmin"),
                             coordinates_2.get("ymin"),
                             coordinates_2.get("xmax"),
                             coordinates_2.get("ymax")]
        mid_point1_y = abs(coordinates_1[3] -
                           coordinates_1[1]) / 2 + coordinates_1[1]
        mid_point1_x = abs(coordinates_1[2] -
                           coordinates_1[0]) / 2 + coordinates_1[0]

        mid_point2_y = abs(coordinates_2[3] -
                           coordinates_2[1]) / 2 + coordinates_2[1]
        mid_point2_x = abs(coordinates_2[2] -
                           coordinates_2[0]) / 2 + coordinates_2[0]

        mid_point_y = abs(mid_point1_y - mid_point2_y)
        mid_point_x = abs(mid_point1_x - mid_point2_x)

        max_way = 3
        min_way = 1
        mid_size = mid_point_y
        if way == "x":
            max_way = 2
            min_way = 0
            mid_size = mid_point_x
        if coordinates_1[max_way] < coordinates_2[min_way]:
            value = round(
                abs(coordinates_2[min_way] - coordinates_1[max_way]))
        else:
            value = round(
                abs(coordinates_1[min_way] - coordinates_2[max_way]))
        if mid_size > 0:
            return value / mid_size
        else:
            return 0

    def object_grouping(self, design_objects: List[Dict],
                        condition: Callable[[Dict, Dict],
                                            bool]) -> List[List[Dict]]:
        """
        Groups the given List of design objects for the any given condition.
        @param design_objects: objects
        @param condition: Grouping condition function
        @return: Grouped list of design objects.
        """
        groups = []
        grouped_positions = []
        for ctr1, design_object1 in enumerate(design_objects):
            temp_list = []
            for ctr2, design_object2 in enumerate(design_objects):
                if condition(design_object1, design_object2):
                    present = False
                    present_position = -1
                    append_object = False
                    append_position = -1
                    for ctr, gr in enumerate(groups):
                        if design_object2 in gr:
                            present = True
                            present_position = ctr
                        if design_object1 in gr:
                            append_object = True
                            append_position = ctr
                    if not present and not append_object:
                        temp_list.append(design_object2)
                        grouped_positions.append(ctr2)
                    elif not present and append_object:
                        groups[append_position].append(design_object2)
                        grouped_positions.append(ctr2)
                    elif present and not append_object:
                        groups[present_position].append(design_object1)
                        grouped_positions.append(ctr1)
                    elif (present and append_object and
                          present_position != append_position):
                        groups[present_position] += groups[append_position]
                        del groups[append_position]
            if temp_list:
                groups.append(temp_list)

        for ctr, design_object in enumerate(design_objects):
            if ctr not in grouped_positions:
                groups.append([design_object])
        return groups


class ImageGrouping(GroupObjects):
    """
    Groups the image objects of the adaptive card objects into a imagesets or
    individual image objects.
    """

    def __init__(self, card_arrange):
        self.card_arrange = card_arrange

    def imageset_condition(self, coordinates_1: Any,
                           coordinates_2: Any) -> bool:
        """
        Returns a condition boolean value for grouping image objects into
        imagesets
        @param coordinates_1: image object one's coordinates
        @param coordinates_2: image object two's coordinates
        @return: boolean value
        """
        if not coordinates_1.get("properties", {}) and not coordinates_1.get(
                "properties", {}):
            coordinates_1 = [coordinates_1.get("xmin"),
                             coordinates_1.get("ymin"),
                             coordinates_1.get("xmax"),
                             coordinates_1.get("ymax")]
            coordinates_2 = [coordinates_2.get("xmin"),
                             coordinates_2.get("ymin"),
                             coordinates_2.get("xmax"),
                             coordinates_2.get("ymax")]
        else:
            coordinates_1 = coordinates_1.get("properties", {}).get(
                "coordinates", [])
            coordinates_2 = coordinates_2.get("properties", {}).get(
                "coordinates", [])

        y_min_difference = abs(coordinates_1[1] - coordinates_2[1])

        if coordinates_1[1] < coordinates_2[1]:
            y_min_difference = y_min_difference / (abs(coordinates_1[1] -
                                                       coordinates_2[3]))
        else:
            y_min_difference = y_min_difference / (
                abs(coordinates_2[1] - coordinates_1[3]))
        x_diff = self.max_min_difference(coordinates_1,
                                         coordinates_2, way="x")
        return (y_min_difference <= config.CONTAINER_GROUPING.get(
            "ymin_difference")
                and x_diff <= config.CONTAINER_GROUPING.get(
                    "xmax-xmin_difference"))

    def group_image_objects(self, image_objects, body, objects, ymins=None,
                            is_column=None) -> [List, Optional[Tuple]]:
        """
        Groups the image objects into imagesets which are in
        closer ymin range.
        @param image_objects: list of image objects
        @param body: list card deisgn elements.
        @param ymins: list of ymins of card design
                                  elements
        @param objects: list of all design objects
        @param is_column: boolean value to check if an object is inside a
        columnset or not
        @return: List of remaining image objects after the grouping if the
                 grouping is done outside the columnset container
                 else returned list of remaining image objects along
                 with its coordinate values.
        """
        # group the image objects based on ymin
        groups = self.object_grouping(image_objects, self.imageset_condition)
        delete_positions = []
        design_object_coords = []
        for group in groups:
            group = [dict(t) for t in {tuple(d.items()) for d in group}]
            # group = self.remove_duplicates(group)
            if len(group) > 1:
                group = sorted(group, key=lambda i: i["xmin"])
                image_set = {
                    "type": "ImageSet",
                    "imageSize": "Auto",
                    "images": []
                }
                sizes = []
                alignment = []
                image_xmins = []
                for ctr, design_object in enumerate(group):
                    index = objects.index(design_object)
                    if index not in delete_positions:
                        delete_positions.append(index)
                    sizes.append(design_object.get("size", "Auto"))
                    alignment.append(design_object.get(
                        "horizontal_alignment", "Left"))
                    image_xmins.append(design_object.get("xmin"))
                    self.card_arrange.append_objects(design_object,
                                                     image_set["images"])
                image_set["images"] = [x for _, x in sorted(
                    zip(image_xmins,
                        image_set["images"]),
                    key=lambda x: x[0])]
                # Assign the imageset's size and alignment property based on
                # each image's alignment and size properties inside the imgaeset
                image_set["imageSize"] = max(set(sizes), key=sizes.count)
                preference_order = ["Left", "Center", "Right"]
                if len(alignment) == len(list(set(alignment))):
                    alignment.sort(key=(preference_order + alignment).index)
                    image_set["horizontalAlignment"] = alignment[0]
                else:
                    image_set["horizontalAlignment"] = max(set(alignment),
                                                           key=alignment.count)
                image_set["coords"] = str(group[0].get("coords"))
                body.append(image_set)
                if ymins:
                    ymins.append(design_object.get("ymin"))
                if is_column:
                    design_object_coords.append(group[0].get("xmin"))
                    design_object_coords.append(group[0].get("ymin"))
                    design_object_coords.append(group[0].get("xmax"))
                    design_object_coords.append(group[0].get("ymax"))
        objects = [design_objects for ctr, design_objects in enumerate(objects)
                   if ctr not in delete_positions]
        if is_column:
            return objects, design_object_coords
        else:
            return objects


class ColumnsGrouping(GroupObjects):
    """
    Groups the design objects into different columns of a columnset
    """
    def __init__(self, card_arrange):
        self.card_arrange = card_arrange

    def horizontal_inclusive(self, object_one: Dict, object_two: Dict) -> bool:
        """
        Returns the horizonral inclusive condition
        @param object_one: design object one
        @param object_two: design object two
        @return: the boolean value of the inclusive condition
        """

        return (((object_one and object_two) and (
            (object_one.get("xmin") <= object_two.get(
                "xmin") <= object_one.get("xmax")
             and object_one.get("xmin") <= object_two.get(
                 "xmax") <= object_one.get("xmax"))
            or (object_two.get("xmin") <= object_one.get(
                "xmin") <= object_two.get("xmax") <= object_one.get("xmax")
                and object_two.get("xmax") <= object_one.get("xmax"))
            or (object_one.get("xmin") <= object_two.get(
                "xmin") <= object_one.get(
                    "xmax") <= object_two.get(
                        "xmax") and object_two.get(
                            "xmax") >= object_one.get("xmin"))))
                or ((object_two and object_one)
                    and ((object_two.get("xmin") <= object_one.get(
                        "xmin") <= object_two.get("xmax")
                          and object_two.get("xmin") <= object_one.get(
                              "xmax") <= object_two.get("xmax"))
                         or (object_one.get("xmin") <= object_one.get("xmin")
                             and object_one.get("xmax") <= object_two.get(
                                 "xmax")
                             and object_two.get("xmin") <= object_one.get("xmax")
                             <= object_two.get("xmax"))
                         or (object_two.get("xmin")
                             <= object_one.get("xmin")
                             <= object_two.get("xmax")
                             <= object_one.get("xmax")
                             and object_one.get("xmax")
                             >= object_two.get("xmin"))))
                )

    def vertical_inclusive(self, object_one: Dict, object_two: Dict) -> bool:
        """
        Returns the vertical inclusive condition

        @param object_one: design object one
        @param object_two: design object two
        @return: the boolean value of the inclusive condition
        """
        return (
            ((object_one and object_two) and
             ((object_one.get("ymin")
               <= object_two.get("ymin") <= object_one.get("ymax")
               and object_one.get("ymin") <= object_two.get("ymax")
               <= object_one.get("ymax"))
              or (object_two.get("ymin") <= object_one.get(
                  "ymin") <= object_two.get(
                      "ymax") <= object_one.get("ymax")
                  and object_two.get("ymax") <= object_one.get("ymax"))
              or (object_one.get("ymin") <= object_two.get("ymin")
                  <= object_one.get("ymax") <= object_two.get("ymax")
                  and object_two.get("ymax") >= object_one.get("ymin"))))
            or ((object_two and object_one)
                and ((object_two.get("ymin") <= object_one.get("ymin")
                      <= object_two.get("ymax") and object_two.get("ymin")
                      <= object_one.get("ymax") <= object_two.get("ymax"))
                     or (object_one.get("ymin") <= object_one.get("ymin")
                         and object_one.get("ymax")
                         <= object_two.get("ymax")
                         and object_two.get("ymin")
                         <= object_one.get("ymax")
                         <= object_two.get("ymax"))
                     or (object_two.get("ymin") <= object_one.get("ymin")
                         <= object_two.get("ymax")
                         <= object_one.get("ymax")
                         and object_one.get("ymax")
                         >= object_two.get("ymin"))))
        )

    def columns_condition(self, design_object1: Dict,
                          design_object2: Dict) -> bool:
        """
        Returns a condition boolean value for grouping objects into
        columnsets
        @param design_object1: design object
        @param design_object2: design object
        @return: boolean value
        """

        y_diff = self.max_min_difference(design_object1, design_object2,
                                         way="y")
        y_min_difference = abs(design_object1.get(
            "ymin", 0) - design_object2.get("ymin", 0))
        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2, "ymin",
                                                    "ymax")
        y_min_difference = y_min_difference / (
            abs(object_two.get("ymin") - object_one.get("ymax")))

        object_one = None
        object_two = None
        if (design_object1.get("object") == "image"
                and design_object2.get("object") != "image"):
            object_one = design_object1
            object_two = design_object2
        elif (design_object2.get("object") == "image"
              and design_object1.get("object") != "image"):
            object_one = design_object2
            object_two = design_object1
        elif (design_object2.get("object") == "image"
              and design_object1.get("object") == "image"):
            object_one = design_object1
            object_two = design_object2
        return (design_object1 != design_object2 and (
            (y_min_difference
             <= config.CONTAINER_GROUPING.get("ymin_difference", ""))
            or self.vertical_inclusive(object_one, object_two)
            or (y_diff <
                config.CONTAINER_GROUPING.get("ymax-ymin_difference", "")
                and self.horizontal_inclusive(object_one, object_two)
                )))

    def check_greater(self, design_object1: Dict, design_object2: Dict,
                      min_way: str, max_way: str) -> Tuple[Dict, Dict]:
        """
        Returns the (greater, lesser) design objects based on the given x or y
        range
        @param design_object1: design object one
        @param design_object2: design object two
        @param min_way: x or y way minimum
        @param max_way: x or y way maximum
        @return: Tuple(greater , lesser) among the design objects
        """

        if (design_object1.get(max_way) - design_object1.get(min_way)) >= (
                design_object2.get(max_way) - design_object2.get(min_way)):
            return design_object1, design_object2
        else:
            return design_object2, design_object1

    def check_overlap_ties(self, design_object1: Dict, design_object2: Dict,
                           x_way_overlap_distance: float,
                           y_way_overlap_distance: float) -> bool:
        """
        Checks which way of overlap is greatest and return true i.e should be
        inside a column of x-way overlap percentage is greater than y-way
        overlap between the 2 design objects.
        @param design_object1: design object one
        @param design_object2: design object two
        @param x_way_overlap_distance: overlapping region's width
        @param y_way_overlap_distance: overlapping region's height
        @return: a boolean value
        """
        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2,
                                                    "xmin", "xmax")
        width = abs(object_one.get("xmax") - object_one.get("xmin"))
        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2,
                                                    "ymin", "ymax")
        height = abs(object_one.get("ymax") - object_one.get("ymin"))

        if x_way_overlap_distance / width >= y_way_overlap_distance / height:
            return True

    def columns_row_condition(self, design_object1: Dict,
                              design_object2: Dict) -> bool:
        """
        Returns a condition boolean value for grouping columnset grouped
        objects into different columns.
        @param design_object1: design object
        @param design_object2: design object
        @return: boolean value
        """
        extract_properites = CollectProperties()
        x_diff = self.max_min_difference(design_object1, design_object2,
                                         way="x")
        y_min_difference = abs(design_object1.get(
            "ymin", 0) - design_object2.get("ymin", 0))

        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2, "ymin",
                                                    "ymax")
        y_min_difference = y_min_difference / (
            abs(object_two.get("ymin") - object_one.get("ymax")))

        point1 = (design_object1.get("xmin"), design_object1.get("ymin"),
                  design_object1.get("xmax"), design_object1.get("ymax"))
        point2 = (design_object2.get("xmin"), design_object2.get("ymin"),
                  design_object2.get("xmax"), design_object2.get("ymax"))

        if design_object1.get("ymin") < design_object2.get("ymin"):
            object_one = design_object1
            object_two = design_object2
        else:
            object_one = design_object2
            object_two = design_object1

        condition = (design_object1 != design_object2
                     and ((design_object1.get("object") == "image"
                           and design_object2.get("object") == "image"
                           and y_min_difference
                           <= config.CONTAINER_GROUPING.get("ymin_difference")
                           and x_diff <= config.CONTAINER_GROUPING.get(
                               "xmax-xmin_difference", ""))
                          or self.horizontal_inclusive(object_one, object_two)
                          )
                     )

        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2,
                                                    "ymin", "ymax")
        x_way_overlap = (
            object_one.get("ymin") <= object_two.get("ymin") <=
            object_one.get("ymax")
            or object_one.get("ymin") <= object_two.get("ymax") <=
            object_one.get("ymax"))
        object_one, object_two = self.check_greater(design_object1,
                                                    design_object2,
                                                    "xmin", "xmax")
        y_way_overlap = (
            object_one.get("xmin") <= object_two.get("xmin") <=
            object_one.get("xmax")
            or object_one.get("xmin") <= object_two.get("xmax") <=
            object_one.get("xmax"))
        intersection = extract_properites.find_iou(point1, point2,
                                                   columns_group=True)
        if intersection[0] and point1 != point2:
            if x_way_overlap and y_way_overlap:
                x_way_overlap_distance = intersection[1]
                y_way_overlap_distance = intersection[2]
                condition = self.check_overlap_ties(
                    design_object1, design_object2, x_way_overlap_distance,
                    y_way_overlap_distance)
            else:
                condition = condition and y_way_overlap
        return condition


class ChoicesetGrouping(GroupObjects):
    """
    Groups the radiobutton objects of the adaptive card objects into a
    choiceset or individual radiobuttion objects.
    """

    def __init__(self, card_arrange):
        self.card_arrange = card_arrange

    def choiceset_condition(self, coordinates_1: Dict,
                            coordinates_2: Dict) -> bool:
        """
        Returns a condition boolean value for grouping radio buttion objects
        into choiceset
        @param coordinates_1: choiceset object's coordinates
        @param coordinates_2: choiceset object's coordinates
        @return: boolean value
        """
        if not coordinates_1.get("properties", {}) and not coordinates_1.get(
                "properties", {}):
            coordinates_1 = [coordinates_1.get("xmin"),
                             coordinates_1.get("ymin"),
                             coordinates_1.get("xmax"),
                             coordinates_1.get("ymax")]
            coordinates_2 = [coordinates_2.get("xmin"),
                             coordinates_2.get("ymin"),
                             coordinates_2.get("xmax"),
                             coordinates_2.get("ymax")]
        else:
            coordinates_1 = coordinates_1.get("properties", {}).get(
                "coordinates", [])
            coordinates_2 = coordinates_2.get("properties", {}).get(
                "coordinates", [])
        y_min_difference = abs(coordinates_1[1] - coordinates_2[1])

        if coordinates_1[1] < coordinates_2[1]:
            y_min_difference = y_min_difference / (abs(coordinates_1[1] -
                                                       coordinates_2[3]))
        else:
            y_min_difference = y_min_difference / (
                abs(coordinates_2[1] - coordinates_1[3]))
        y_diff = self.max_min_difference(coordinates_1,
                                         coordinates_2, way="y")

        return (abs(y_diff) <= config.CONTAINER_GROUPING.get(
            "choiceset_ymax-ymin_difference")
                and y_min_difference <= config.CONTAINER_GROUPING.get(
                    "choiceset_y_min_difference"))

    def group_choicesets(self, radiobutton_objects: Dict, body: List[Dict],
                         ymins=None) -> None:
        """
        Groups the choice elements into choicesets based on
        the closer ymin range
        @param radiobutton_objects: list of individual choice
                                                 elements
        @param body: list of card deisgn elements
        @param ymins: list of ymin of deisgn elements
        """
        groups = []
        radio_buttons = []
        if isinstance(radiobutton_objects, dict):
            for key, values in radiobutton_objects.items():
                radio_buttons.append(values)
            radiobutton_objects = radio_buttons
        if len(radiobutton_objects) == 1:
            # radiobutton_objects = [radiobutton_objects]
            groups = [radiobutton_objects]
        if not groups:
            groups = self.object_grouping(radiobutton_objects,
                                          self.choiceset_condition)
        for group in groups:
            group = sorted(group, key=itemgetter("ymin"))
            choice_set = {
                "type": "Input.ChoiceSet",
                "choices": [],
                "style": "expanded"
            }
            alignment = []
            for design_object in group:
                self.card_arrange.append_objects(design_object,
                                                 choice_set["choices"])
                alignment.append(design_object.get("horizontal_alignment",
                                                   "Left"))
            preference_order = ["Left", "Center", "Right"]
            if len(alignment) == len(list(set(alignment))):
                alignment.sort(key=(preference_order + alignment).index)
                choice_set["horizontalAlignment"] = alignment[0]
            else:
                choice_set["horizontalAlignment"] = max(set(alignment),
                                                        key=alignment.count)

            body.append(choice_set)
            if ymins is not None and len(group) > 0:
                ymins.append(design_object.get("ymin"))
