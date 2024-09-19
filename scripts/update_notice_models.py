from a_board import models as new_models
from notice import models as old_models
from . import utils


def run():
    model_list = [
        (old_models.Post, new_models.Notice),
        (old_models.Comment, new_models.NoticeComment),
    ]

    for model in model_list:
        messages = utils.create_instance_get_messages(model[0], model[1])
        for message in messages.values():
            if message:
                print(message)
