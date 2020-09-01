import sys
import os
from typing import List


os.environ["CUDA_VISIBLE_DEVICES"] = ""


class CardLayout:
    pass


# card_layout.copy?
def print_layout(layout_array):
    layouts = []
    for row in layout_array:
        lout_row = "row {"

        if isinstance(row, tuple):
            lout_row += f" item({row[0]})"
        elif isinstance(row, dict):
            cols = row["columns"]
            for col in cols:
                lout_row += "col {"
                lout_row += print_layout(col)
                lout_row += "}"
        else:
            print("not supported.")

        lout_row += "}"
        layouts.append(lout_row)

    return "".join(layouts)


def print_layout_list(layout_array):
    layouts = []
    for row in layout_array:
        lout_row = ["row", "{"]

        if isinstance(row, tuple):
            lout_row.append(f" item({row[0]})")
        elif isinstance(row, dict):
            cols = row["columns"]
            for col in cols:
                lout_row.extend(["col", "{"])
                lout_row.extend(print_layout_list(col))
                lout_row.append("}")
        else:
            print("not supported.")

        lout_row.append("}")
        layouts.append(lout_row)

    return layouts


def bbox_area(x1, y1, x2, y2):
    return abs(x2 - x1) * abs(y2 - y1)


def iou_bbox(box1, box2):
    "bbox intersection of two bboxes. return [0, 0, 0, 0] if no intersection."
    x1, y1, x2, y2 = box1
    xx1, yy1, xx2, yy2 = box2

    x = max([x1, xx1])
    y = max([y1, yy1])
    xx = min([x2, xx2])
    yy = min([y2, yy2])

    # No intersection at all.
    if x >= xx or y >= yy:
        box = [0, 0, 0, 0]
    else:
        box = [x, y, xx, yy]
    return box


def filter_similar_bboxes(bboxs):
    """
    Filter out bboxes if they are intersecting more than 90% with other bboxes.
    """
    bboxs_filtered = []
    indi = 0
    while indi < len(bboxs):
        indj = indi + 1
        while indj < len(bboxs):
            box1 = bboxs[indi][1]
            box2 = bboxs[indj][1]
            if min_area_iou(box1, box2):
                # Remove the max one.
                box1_area = bbox_area(**box1)
                box2_area = bbox_area(**box2)
                if box2_area > box1_area:
                    bboxs_filtered.append(bboxs[indi])
                else:
                    bboxs_filtered.append(bboxs[indj])


def min_ylen_iou(box1, box2) -> float:
    """
    Get the fraction of y-cord intersects, calculated against the min y-cord
    of both boxes. return zero if no intersection.
    """
    # import pdb; pdb.set_trace()
    box = iou_bbox(box1, box2)
    y_len = box[3] - box[1]
    min_box_y = min([box1[3] - box1[1], box2[3] - box2[1]])
    # print(y_len, min_box_y)
    return float(y_len / min_box_y)


def min_xlen_iou(box1: List[float], box2: List[float]) -> float:
    """
    Get the fraction of x-cord intersects, calculated against the min x-cord
    of both boxes. return zero if no intersection.
    """
    box = iou_bbox(box1, box2)
    x_len = box[2] - box[0]
    min_box_x = min([box1[2] - box1[0], box2[2] - box2[0]])
    return float(x_len / min_box_x)


def min_area_iou(box1, box2, threshold=0.9):
    """check box1 and box2 intersecting and its area is
        not greater than the 90% of min area of box1 and box2.
    """
    box = iou_bbox(box1, box2)
    box_area = bbox_area(*box)
    if box_area == 0:
        return False
    else:
        min_box_area = min([bbox_area(*box1), bbox_area(*box2)])
        return box_area >= threshold * min_box_area


def check_same_row(box1, box2, min_y_iou=0.3):
    """
    Check box1 and box2 are in same row.
    if there are slight intersection, still treat it as different row.

    @param min_y_iou: The line iou ratio is higher than the threshold then
                      treat them as same row or not.
    """
    x1, y1, x2, y2 = box1
    xx1, yy1, xx2, yy2 = box2

    # check any intersection chances.
    y_intrsect = min_ylen_iou(box1, box2)
    if y_intrsect == 0:
        # no intersection so, this check is skipped.
        y_intrsect = sys.maxsize
    y_aligned = min([y2, yy2]) > max([y1, yy1])

    return y_aligned and y_intrsect > min_y_iou


def check_same_col(box1, box2, min_x_iou=0.3):
    "Two boxes are aligned x-axis or not"
    x1, y1, x2, y2 = box1
    xx1, yy1, xx2, yy2 = box2

    x_intrsect = min_xlen_iou(box1, box2)
    if x_intrsect == 0:
        x_intrsect = sys.maxsize
    x_aligned = min([x2, xx2]) > max([x1, xx1])
    return x_aligned and x_intrsect > min_x_iou


def merge_box_coords(box1, box2):
    "Merge two box coordinates and create the enclosed box coordinate."
    x1 = min(box1[0], box2[0])
    y1 = min(box1[1], box2[1])
    x2 = max(box1[2], box2[2])
    y2 = max(box1[3], box2[3])
    return [x1, y1, x2, y2]


def collect_rows(bbox_list):
    """
    @param bbox_list: sorted bbox_list with "y1", also
                      includes item label.
    """
    rows = []
    row = []
    bbox_list = sorted(bbox_list, key=lambda x: x[1][1])
    while bbox_list:
        label, box = bbox_list.pop(0)
        if not row:
            row.append((label, box))
            box_coord = box
            continue
        elif check_same_row(box_coord, box):
            row.append((label, box))
            # update the row coordinate
            box_coord = merge_box_coords(box, box_coord)
        else:
            # Found a full row, the new item is part of
            # next element.
            rows.append(parse_row(row))
            row = [(label, box)]
            box_coord = box
    else:
        row and rows.append(parse_row(row))
    return rows


def parse_row(row):
    # print("Row size: ", len(row))

    if len(row) == 1:
        return row[0]
    else:
        item_set = {
            "type": "ItemSet",
            "columns": []
        }
        # Sort items based on x1 axis.
        row = sorted(row, key=lambda x: x[1][0])

        col = []
        has_nested_col = False

        while row:
            label, box = row.pop(0)
            # print(f"box poped: {box}")
            if not col:
                col.append((label, box))
                col_coord = box
                continue
            elif check_same_col(col_coord, box):
                # Mark the column has multiple row or not.
                if min_area_iou(box, col_coord):
                    has_nested_col = True
                    print("nesting.")

                col.append((label, box))
                col_coord = merge_box_coords(col_coord, box)
                # print(f"box: {box}, col Cord: {col_coord}")
            else:
                # Reached end of current column.
                # print("----- found a col ----")
                if has_nested_col:
                    item_set["columns"].append(collect_rows(col))
                    # item_set["columns"].append(col)
                else:
                    item_set["columns"].append(col)

                col = [(label, box)]
                col_coord = box
                # Reset for next column aggregation.
                has_nested_col = False
        else:
            # Handle last column
            if has_nested_col:
                item_set["columns"].append(collect_rows(col))
                # item_set["columns"].append(col)
            else:
                item_set["columns"].append(col)
        return item_set
