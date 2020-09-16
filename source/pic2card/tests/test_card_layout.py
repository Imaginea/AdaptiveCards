import unittest
import json
import pandas as pd
import numpy as np
from pprint import pprint
from mystique.card_layout import (collect_rows, print_layout,
                                  print_layout_list_flat, pretty_print_layout, filter_similar_bboxes)


class TestCardLayout(unittest.TestCase):
    def setUp(self):
        with open("od_result_16.json") as f:
            od_result = {k: np.array(v)
                         for k, v in json.loads(f.read()).items()}
        box_df = pd.DataFrame(
                [(ind, *i) for
                 ind, i in enumerate(od_result['detection_boxes'])],
                columns=["ind", "x1", "y1", "x2", "y2"]
        )
        box_df["class"] = od_result["detection_classes"]

        self.bbox_list = [(int(t2), t1) for (*t1, t2) in
                          box_df.sort_values(
                              by=["y1", "x1"]).to_numpy()[:, 1:]]

    def test_collect_rows(self):
        boxes, removed = filter_similar_bboxes(self.bbox_list)
        card_layout = collect_rows(boxes)
        # import IPython; IPython.embed()
        card = print_layout_list_flat(card_layout)
        print(pretty_print_layout(card))
