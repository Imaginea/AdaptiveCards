"""
Helper module for the bleu score metric generation
"""
import collections
import copy
import re
from datetime import datetime
from typing import List, Dict

import configs


class Helper:
    """
    This is a general helper class for the metric pre-processing module.
    """

    def _change_date_expression(self, expression: str) -> str:
        """
        Convert the date expression to date string in words format
        @param expression: date expression
        @return: date string in words format
        """
        date_string = \
            re.findall(r"\b\d+\-\d+-\d+T\d+:\d+:\d+\w{1}", expression)[0]
        date_time_obj = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
        date_string = date_time_obj.strftime("%a, %d %b %Y")
        return date_string

    def factset_to_textbox(self, element: Dict) -> List:
        """
        Convert the factset element to column-sets of textboxes
        @param element: factset element
        @return: updated list column-sets of textboxes.
        """
        keys_values = element.get("facts")
        updated_element = []
        for ctr, value in enumerate(keys_values):
            item1 = {
                "type": "TextBlock",
                "text": value.get("title"),
                "size": "Default",
                "horizontalAlignment": "Left",
                "color": "Default",
                "weight": "Bolder",
                "wrap": "true"
            }
            item2 = {
                "type": "TextBlock",
                "text": value.get("value"),
                "size": "Default",
                "horizontalAlignment": "Right",
                "color": "Default",
                "weight": "Default",
                "wrap": "true"
            }
            columns = [{"type": "Column", "width": "auto", "items": [item1],
                        "horizontalAlignment": "Left"},
                       {"type": "Column", "width": "auto", "items": [item2],
                        "horizontalAlignment": "Left"}]
            columnset = {"type": "ColumnSet", "columns": columns,
                         "horizontalAlignment": "Left"}
            updated_element.append(columnset)
        return updated_element

    def remove_fields_from_element(self, element: Dict,
                                   reference_list: List) -> Dict:
        """
        Remove the extra fields from the element , i.e keep only the
        supported attributes for the element.
        @param element: adaptive card design element
        @param reference_list: list of supported attributes
        for the passed element's type.
        @return: updated element.
        """
        fields = list(element.keys())
        fields = list(set(fields) & set(reference_list))
        element = {k: element[k] for k in fields}
        return element

    def TextBlock(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Textbox
        @param element: adaptive cards design element
        @return: pre-processed textbox element
        """
        # removing extra fields
        element = self.remove_fields_from_element(element, configs.TEXTBOX)
        fields = list(element.keys())
        # add the extra fileds with default values
        if "wrap" not in fields:
            element.update({"wrap": "true"})
        if "wrap" in fields:
            element.update({"wrap": "true"})
        if "size" not in fields:
            element.update({"size": "Default"})
        if "weight" not in fields:
            element.update({"weight": "Default"})
        if "color" not in fields:
            element.update({"color": "Default"})

        if re.findall(r"{{.*}}", element.get("text", "")):
            need_to_update = self._change_date_expression(
                re.findall(r"{{.*}}", element.get("text"))[0])
            text = element.get("text")
            text = re.sub(r"{{.*}}", need_to_update, text)
            element.update({"text": text})
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def actions(self, element: Dict) -> List:
        """
        Performs all the pre-process operation related to actions inside an
        Action-set
        @param element: adaptive cards design element
        @return: pre-processed list of action elements
        """
        element = self.remove_fields_from_element(element[0],
                                                  configs.ACTION_LIST)
        fields = list(element.keys())
        if "style" not in fields:
            element.update({"style": "default"})
        element = collections.OrderedDict(sorted(element.items()))
        return [element]

    def ActionSet(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Actionset
        @param element: adaptive cards design element
        @return: pre-processed actionset element
        """
        element = self.remove_fields_from_element(element, configs.ACTIONSET)
        fields = list(element.keys())
        if "spacing" not in fields:
            element.update({"spacing": "Medium"})
        element["actions"] = self.actions(element["actions"])
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def Image(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Image
        @param element: adaptive cards design element
        @return: pre-processed image element
        """
        element = self.remove_fields_from_element(element, configs.IMAGE)
        fields = list(element.keys())
        if "altText" not in fields:
            element.update({"altText": "Image"})
        element["url"] = ""
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def Checkbox(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Checkbox
        @param element: adaptive cards design element
        @return: pre-processed checkbox element
        """
        element = self.remove_fields_from_element(element, configs.CHECKBOX)
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def choices(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Choices inside a
        Choice-Set
        @param element: adaptive cards design element
        @return: pre-processed list of choices.
        """
        element = self.remove_fields_from_element(element, configs.CHOICE_LIST)
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def ChoiceSet(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Choice-Set
        @param element: adaptive cards design element
        @return: pre-processed choice-set element
        """
        element = self.remove_fields_from_element(element, configs.CHOICESET)
        element.update({"style": "expanded"})
        element["choices"] = [self.choices(ch) for ch in element["choices"]]
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def Column(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Column inside a
        Column-Set
        @param element: adaptive cards design element
        @return: pre-processed column element
        """
        element = self.remove_fields_from_element(element, configs.COLUMN_LIST)
        element["items"] = []
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def ColumnSet(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Column-Set
        @param element: adaptive cards design element
        @return: pre-processed column-set element
        """
        element = self.remove_fields_from_element(element, configs.COLUMNSET)
        element["columns"] = []
        element = collections.OrderedDict(sorted(element.items()))
        return element

    def ImageSet(self, element: Dict) -> Dict:
        """
        Performs all the pre-process operation related to Image-Set
        @param element: adaptive cards design element
        @return: pre-processed image-set element
        """
        element = self.remove_fields_from_element(element, configs.IMAGESET)
        element["images"] = []
        element = collections.OrderedDict(sorted(element.items()))
        return element


class AcContainersTrain:
    """
    This class is responsible for fetching the appropriate design templates and
    invoke the ground truth element's
    pre-process
    """

    def __init__(self, obj):
        self.pre_process = obj
        self.helper_object = Helper()
        # self.calling_function = 'process_train'

    def ColumnSet(self, body: List, element: Dict) -> None:
        """
        Fetch the design template for the column-set element and calls the
        needed pre-processing functions.
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        backup = copy.deepcopy(element)
        template_object = getattr(self.helper_object,
                                  element.get("type", ""))
        element = template_object(element)
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
        body = body[-1].get("columns", [])
        self.pre_process.pre_process_elements(body, backup["columns"])

    def Column(self, body: List, element: Dict) -> None:
        """
        Fetch the design template for the column-set element and calls the
        needed pre-processing functions.
        @param body: design element's layout structure
        @param element: adaptive card design element
        """

        backup = copy.deepcopy(element)

        template_object = getattr(self.helper_object,
                                  element.get("type", ""))
        element = template_object(element)
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
        body = body[-1].get("items", [])
        self.pre_process.pre_process_elements(body, backup["items"])

    def ImageSet(self, body: List, element: Dict) -> None:
        """
        Fetch the design template for the column-set element and calls the
        needed pre-processing functions.
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        backup = copy.deepcopy(element)
        template_object = getattr(self.helper_object,
                                  element.get("type", ""))
        element = template_object(element)
        element = collections.OrderedDict(sorted(element.items()))

        body.append(element)
        body = body[-1].get("images", [])
        self.pre_process.pre_process_elements(body, backup["images"])

    def Choiceset(self, body: List, element: Dict) -> None:
        """
        Fetch the design template for the column-set element and calls the
        needed pre-processing functions.
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        template_object = getattr(self.helper_object, "ChoiceSet")
        element = template_object(element)
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)


class AcContainersTest:
    """
    This class is responsible for invoking the pic2card generated
    element's pre-process
    """

    def __init__(self, obj):
        self.pre_process = obj
        self.helper_object = Helper()
        # self.calling_function = 'process_test'

    def ColumnSet(self, body: List, element: Dict) -> None:
        """
        Invoke the pic2card generated element's pre-process
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
        body = body[-1].get("columns", [])
        self.pre_process.pre_process_elements(body, element["columns"])

    def Column(self, body: List, element: Dict) -> None:
        """
        Invoke the pic2card generated element's pre-process
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
        body = body[-1].get("items", [])
        self.pre_process.pre_process_elements(body, element["items"])

    def ImageSet(self, body: List, element: Dict) -> None:
        """
        Invoke the pic2card generated element's pre-process
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
        body = body[-1].get("images", [])
        self.pre_process.pre_process_elements(body, element["images"])

    def Choiceset(self, body: List, element: Dict) -> None:
        """
        Invoke the pic2card generated element's pre-process
        @param body: design element's layout structure
        @param element: adaptive card design element
        """
        element = collections.OrderedDict(sorted(element.items()))
        body.append(element)
