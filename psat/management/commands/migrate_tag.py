from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from psat.models import ProblemTag, Tag
from reference.models import PsatProblem
from taggit.models import TaggedItem


class Command(BaseCommand):
    help = 'Setup PSAT Tag model from old ProblemTag model'

    def handle(self, *args, **kwargs):
        update_count = create_count = {
            'tag': 0,
            'taggeditem': 0,
        }

        tag_instances = ProblemTag.objects.all()

        for instance in tag_instances:
            problem = PsatProblem.objects.get(
                psat__year=instance.problem.year,
                psat__exam__abbr=instance.problem.ex,
                psat__subject__abbr=instance.problem.sub,
                number=instance.problem.problem_number,
            )

            with transaction.atomic():
                try:
                    Tag.objects.get(id=instance.id)
                except ObjectDoesNotExist:
                    Tag.objects.create(
                        id=instance.id,
                        user_id=instance.user.id,
                        problem=problem,
                    )
                    create_count['tag'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'Tag: {create_count["tag"]} instances created, {update_count["tag"]} instances updated'))

        old_content_type = ContentType.objects.get(app_label='psat', model='problemtag')
        new_content_type = ContentType.objects.get(app_label='psat', model='tag')

        old_taggeditem_instances = TaggedItem.objects.filter(content_type=old_content_type)

        for instance in old_taggeditem_instances:
            with transaction.atomic():
                try:
                    TaggedItem.objects.get(
                        object_id=instance.object_id,
                        content_type=new_content_type,
                        tag=instance.tag,
                    )
                except ObjectDoesNotExist:
                    TaggedItem.objects.create(
                        object_id=instance.object_id,
                        content_type=new_content_type,
                        tag=instance.tag,
                    )
                    create_count['taggeditem'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'TaggedItem: {create_count["taggeditem"]} instances created, {update_count["taggeditem"]} instances updated'))
