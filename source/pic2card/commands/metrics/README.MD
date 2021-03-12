## Thins to pre-process manually while collecting the ground truth adaptive card json
 1. Filter out the elements not supported by pic2card except factset elements 
    - The supported elements are: **TextBlock, ChoiceSet, ImageSet, CheckBox, 
                                    ColumnSet, Image, ActionSet**
 2. Update the action elements as separate set of ActionSets with Submit action.
 3. Update the un-supported column width properties like **Weighted** and 
    **Pixels** to supported formats ( **Stretch**, **Automatic** )
 4. Template data binding is not supported in metric collection.

## Command Usage:

```shell
python3 -m mystique/commands/generate_bleu_score.py \
        --images_path=/image_path \
        --ground_truths_path=/ground_truth_json_path \
        --api_url=url_of_the_service
```