from a_psat.models import problem_models as new_models
from psat.models import psat_data_models as old_models
from . import utils


def run():
    model_list = [
        (old_models.Open, new_models.ProblemOpen),
        (old_models.Like, new_models.ProblemLike),
        (old_models.Rate, new_models.ProblemRate),
        (old_models.Solve, new_models.ProblemSolve),
        (old_models.Memo, new_models.ProblemMemo),
        (old_models.Collection, new_models.ProblemCollection),
        (old_models.CollectionItem, new_models.ProblemCollectionItem),
    ]

    for model in model_list:
        messages = utils.create_instance_get_messages(model[0], model[1])
        for message in messages.values():
            if message:
                print(message)

    tag_counts = tagged_item_counts = 0

    old_tags = old_models.Tag.objects.all()
    for old_tag in old_tags:
        tag_name_list = old_tag.tags.names()
        for tag_name in tag_name_list:
            problem_tag, created = new_models.ProblemTag.objects.get_or_create(name=tag_name)
            if created:
                tag_counts += 1

            problem_tagged_item, created = new_models.ProblemTaggedItem.objects.get_or_create(
                tag=problem_tag, user_id=old_tag.user_id, content_object_id=old_tag.problem_id)
            if created:
                tagged_item_counts += 1

    if tag_counts:
        print(f'Successfully created {tag_counts} ProblemTag instances.')
    else:
        print(f'No changes were made to ProblemTag instances.')

    if tagged_item_counts:
        print(f'Successfully created {tagged_item_counts} ProblemTaggedItem instances.')
    else:
        print(f'No changes were made to ProblemTaggedItem instances.')
