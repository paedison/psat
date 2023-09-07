# Python Standard Function Import

# Django Core Import
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.utils.translation import gettext_lazy as _

from taggit_templatetags2 import settings
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import GetTagForObject

# Custom App Import
from psat.models import Exam, Problem

register = Library()
exam = Exam.objects
problem = Problem.objects


@register.filter
def add_0(content):  # Convert to 2-Digit Number
    content = str(content).zfill(2)
    return content


@register.filter
def abstract(content, base):  # Abstract content from base
    return base - int(content)


@register.filter
def add_space(content):  # Add Space before 1-Digit Number
    if int(content) < 10:
        content = " " + str(content)
    return content


@register.filter()
def int2kor(value):  # Convert Integer to Korean Alphabet
    nums = [_('Sun'), _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat')]
    s = str(value)
    result = ''
    for c in s:
        result += nums[int(c)]
    return result


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
