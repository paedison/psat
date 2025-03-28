from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.utils.translation import gettext_lazy as _
from taggit_templatetags2 import settings
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import GetTagForObject

from reference.models import UnitDepartment

register = Library()


@register.filter
def digit_of_one(content) -> str:  # Convert to 2-Digit Number
    digit = abs(content) % 10
    if digit == 0:
        return digit + 10
    return digit


@register.filter
def add_0(content) -> str:  # Convert to 2-Digit Number
    return str(content).zfill(2)


@register.filter
def subtract(content, base) -> int:  # Subtract content from base
    return base - int(content)


@register.filter
def divide(content, base) -> float:  # Divide content by base
    return content / base


@register.filter
def mod(value, divisor):
    try:
        return value % divisor
    except (TypeError, ValueError, ZeroDivisionError):
        return None


@register.filter
def percentage(content) -> float:  # Abstract content from base
    if content:
        return content * 100
    return 0


@register.filter()
def int2kor(value):  # Convert Integer to Korean Alphabet
    nums = [_('Sun'), _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat')]
    s = str(value)
    result = ''
    for c in s:
        result += nums[int(c)]
    return result


@register.filter()
def round_number(content):
    number_dict = {
        '1': '①',
        '2': '②',
        '3': '③',
        '4': '④',
        '5': '⑤',
    }
    if content is None or content == 0:
        return ''
    if content in range(1, 6):
        return number_dict[str(content)]
    else:
        number_list = [number_dict[digit] for digit in str(content)]
        return ''.join(number_list)


@register.filter()
def get_status(problem, data: list[dict]):
    key_list = ['is_liked', 'rating', 'is_correct']
    try:
        problem_id = getattr(problem, 'problem_id')
    except AttributeError:
        problem_id = getattr(problem, 'id')
    if data:
        for instance in data:
            if instance['id'] == problem_id:
                target_key = None
                for key in instance.keys():
                    target_key = key if key in key_list else None
                if target_key:
                    return instance[target_key]
                return True
    else:
        for key in key_list:
            try:
                return getattr(problem, key)
            except AttributeError:
                pass


@register.filter()
def get_range(content):
    last_number = content + 1 if isinstance(content, int) else int(content) + 1
    return range(1, last_number)


@register.filter()
def get_department(content):
    return UnitDepartment.objects.get(id=content).name


@register.tag
def lineless(parser, token):  # Delete Blank Lines
    nodelist = parser.parse(('endlineless',))
    parser.delete_first_token()
    return LinelessNode(nodelist)


class LinelessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        input_str = self.nodelist.render(context)
        output_str = ''
        for line in input_str.splitlines():
            if line.strip():
                output_str = '\n'.join((output_str, line))
        return output_str


@register.tag
class GetSortedTagForObject(GetTagForObject):
    name = 'get_sorted_tags_for_object'

    def get_value(self, context, source_object, varname=''):
        """
        Args:
            source_object - <django model object>

        Return:
            queryset tags
        """

        tag_model = settings.TAG_MODEL
        app_label = source_object._meta.app_label

        try:
            model = source_object._meta.model_name
        except AttributeError:
            model = source_object._meta.module_name.lower()

        content_type = ContentType.objects.get(app_label=app_label,
                                               model=model)

        try:
            tags = tag_model.objects.filter(
                taggit_taggeditem_items__object_id=source_object,
                taggit_taggeditem_items__content_type=content_type).order_by(
                'taggit_taggeditem_items__tag__name'
            )
        except:
            tags = tag_model.objects.filter(
                taggit_taggeditem_items__object_id=source_object.pk,
                taggit_taggeditem_items__content_type=content_type).order_by(
                'taggit_taggeditem_items__tag__name'
            )

        if varname:
            context[varname]
            return ''
        else:
            return tags
