from typing import List, Dict, Callable
from operator import itemgetter


class GroupObjects:
    """
    Handles the grouping of given list of objects for any set conditions that is
    passed.
    """

    def object_grouping(self, design_objects: List[Dict],
                        condition: Callable[[Dict, Dict], bool]):
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
                    elif present and append_object and present_position != append_position:
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

    def imageset_condition(self, design_object1: Dict, design_object2: Dict):
        """
        Returns a condition boolean value for grouping image objects into
        imagesets

        @param design_object1: image object
        @param design_object2: image object
        @return: boolean value
        """
        if design_object1.get("xmin") < design_object2.get("xmin"):
            xmax = design_object1.get("xmax")
            xmin = design_object2.get("xmin")
        else:
            xmax = design_object2.get("xmax")
            xmin = design_object1.get("xmin")
        ymin_diff = abs(design_object1.get("ymin") - design_object2.get("ymin"))
        x_diff = abs(xmax - xmin)
        return ymin_diff <= 10 and x_diff <= 100

    def group_image_objects(self, image_objects, body, objects, ymins=None,
                            is_column=None):
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
        """
        # group the image objects based on ymin
        groups = self.object_grouping(image_objects, self.imageset_condition)
        delete_positions = []
        xmin = None
        for group in groups:
            group = sorted(group, key=lambda i: i["xmin"])
            if len(group) > 1:
                image_set = {
                        "type": "ImageSet",
                        "imageSize": "Auto",
                        "images": []
                }
                sizes = []
                for ctr, design_object in enumerate(group):
                    index = objects.index(design_object)
                    if index not in delete_positions:
                        delete_positions.append(index)
                    sizes.append(design_object.get("size", "Auto"))
                    self.card_arrange.append_objects(design_object,
                                                     image_set["images"])
                image_set["imageSize"] = max(set(sizes), key=sizes.count)
                body.append(image_set)
                if ymins:
                    ymins.append(design_object.get("ymin"))
                if is_column:
                    xmin = group[0].get("xmin")
        objects = [design_objects for ctr, design_objects in enumerate(objects)
                   if ctr not in delete_positions]
        if is_column:
            return objects, xmin
        else:
            return objects


class ColumnsGrouping(GroupObjects):
    """
    Groups the radiobutton objects of the adaptive card objects into a choiceset
    or individual radiobuttion objects.
    """

    def __init__(self, card_arrange):
        self.card_arrange = card_arrange

    def columns_condition(self, design_object1, design_object2):
        """
        Returns a condition boolean value for grouping objects into
        columnsets

        @param design_object1: design object
        @param design_object2: design object
        @return: boolean value
        """
        if design_object1.get("ymin") < design_object2.get("ymin"):
            ymax = design_object1.get("ymax")
            ymin = design_object2.get("ymin")
        else:
            ymax = design_object2.get("ymax")
            ymin = design_object1.get("ymin")
        y_diff = round(abs(ymin - ymax))
        xmin_diff = abs(
                design_object1.get("xmin") - design_object2.get("xmin"))

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
                (abs(design_object1.get("ymin", 0) - design_object2.get("ymin",
                                                                        0)) <= 11.0)
                or (y_diff <= 15 and xmin_diff <= 100)
                or ((object_one and object_two) and (
                (object_one.get("ymin") <= object_two.get(
                        "ymin") <= object_one.get("ymax") and object_one.get(
                        "ymin") <= object_two.get("ymax") <= object_one.get(
                        "ymax"))
                or (object_two.get("ymin") <= object_one.get(
                "ymin") and object_two.get("ymax") <= object_one.get(
                "ymax") and object_one.get("ymin") <= object_two.get(
                "ymax") <= object_one.get("ymax"))
                or (object_one.get("ymin") <= object_two.get(
                "ymin") <= object_one.get("ymax") <= object_two.get(
                "ymax") and object_two.get("ymax") >= object_one.get("ymin"))
        ))))

    def columns_row_condition(self, design_object1: Dict, design_object2: Dict):
        """
        Returns a condition boolean value for grouping columnset grouped objects
        into different columns.

        @param design_object1: design object
        @param design_object2: design object
        @return: boolean value
        """
        if design_object1.get("ymin") < design_object2.get("ymin"):
            ymax = design_object1.get("ymax")
            ymin = design_object2.get("ymin")
        else:
            ymax = design_object2.get("ymax")
            ymin = design_object1.get("ymin")
        y_diff = round(abs(ymin - ymax))
        xmin_diff = abs(design_object1.get("xmin") - design_object2.get("xmin"))
        return (design_object1 != design_object2 and (
                (y_diff <= 25 and xmin_diff <= 100)
                or (design_object1.get("object",
                                       "") == "image" and y_diff <= 100 and xmin_diff <= 100)
                or (y_diff <= 100 and xmin_diff <= 25)
        ))


class ChoicesetGrouping(GroupObjects):
    def __init__(self, card_arrange):
        self.card_arrange = card_arrange

    def choiceset_condition(self, design_object1: Dict, design_object2: Dict):
        """
        Returns a condition boolean value for grouping radio buttion objects into
        choiceset

        @param design_object1: image object
        @param design_object2: image object
        @return: boolean value
        """
        design_object1_ymin = float(design_object1.get("ymin"))
        design_object2_ymin = float(design_object2.get("ymin"))
        difference_in_ymin = abs(design_object1_ymin - design_object2_ymin)
        if design_object1_ymin > design_object2_ymin:
            difference_in_y = float(
                    design_object2.get("ymax")) - design_object1_ymin
        else:
            difference_in_y = float(
                    design_object1.get("ymax")) - design_object2_ymin

        return abs(difference_in_y) <= 10 and difference_in_ymin <= 30

    def group_choicesets(self, radiobutton_objects, body, ymins=None):
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
            for design_object in group:
                self.card_arrange.append_objects(design_object,
                                                 choice_set["choices"])

            body.append(choice_set)
            if ymins is not None and len(group) > 0:
                ymins.append(design_object.get("ymin"))
