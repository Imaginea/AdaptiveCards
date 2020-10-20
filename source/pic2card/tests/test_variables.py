debug_string_test = [
    'item(1)\n', 'item(1)\n', 'item(1)\n', 'item(1)\n', 'item(1)\n',
    'item(1)\n', 'row\n', '\tcolumn\n', '\t\titem(1)\n', '\tcolumn\n',
    '\t\titem(1)\n', 'row\n', '\tcolumn\n', '\t\titem(1)\n', '\tcolumn\n',
    '\t\titem(5)\n', '\tcolumn\n', '\t\titem(1)\n', 'item(1)\n', 'item(1)\n',
    'item(1)\n', 'item(1)\n', 'row\n', '\tcolumn\n', '\t\titem(1)\n',
    '\tcolumn\n', '\t\titem(5)\n', '\tcolumn\n', '\t\titem(1)\n', 'row\n',
    '\tcolumn\n', '\t\titem(1)\n', '\tcolumn\n', '\t\titem(1)\n'
]
# image - training images 5.png
test_img_obj1 = {
    'object': 'image', 'xmin': 259.61538419127464, 'ymin': 93.91641104221344,
    'xmax': 363.92310082912445,
    'ymax': 198.15856432914734,
    'coords': (
        259.61538419127464, 93.91641104221344,
        363.92310082912445, 198.15856432914734
    ),
    'score': 0.9998627,
    'uuid': '15f3d921-dc8f-45d6-bd65-25078525951a',
    'class': 5
}
test_img_obj2 = {
    'object': 'image', 'xmin': 143.74213486909866,
    'ymin': 95.04049408435822,
    'xmax': 248.02349030971527, 'ymax': 197.5490162372589,
    'coords': (
        143.74213486909866, 95.04049408435822,
        248.02349030971527, 197.5490162372589
    ),
    'score': 0.9996531,
    'uuid': 'a9f27469-bc44-4a7c-a376-e12f03de7b2e',
    'class': 5
}

# Choiceset Grouping test image 100
test_cset_obj1 = {
    'object': 'radiobutton', 'xmin': 13.708709377795458,
    'ymin': 206.46938413381577,
    'xmax': 155.36615484952927,
    'ymax': 227.09414440393448,
    'coords': (
        13.708709377795458, 206.46938413381577,
        155.36615484952927, 227.09414440393448
    ),
    'score': 0.9961301,
    'uuid': '5657d5e6-fbf5-4b11-9213-05515442033b',
    'class': 2
}
test_cset_obj2 = {
    'object': 'radiobutton', 'xmin': 16.655487801879644,
    'ymin': 227.20616340637207,
    'xmax': 165.07373866438866, 'ymax': 245.98763144016266,
    'coords': (
        16.655487801879644, 227.20616340637207,
        165.07373866438866, 245.98763144016266
    ),
    'score': 0.992979,
    'uuid': '84c79742-0e5b-485a-ac59-d585ce590e9d',
    'class': 2
}
