# post_extras.py
from django.template import Library, Node
import re

from django.utils.translation import gettext as _
from django.urls import reverse

from psat.models import Exam, Problem

register = Library()

exam = Exam.objects
problem = Problem.objects


@register.filter
def add_0(content):  # Convert to 2-Digit Number
    if int(content) < 10:
        content = "0" + str(content)
    return content


@register.filter
def add_space(content):  # Add Space before 1-Digit Number
    if int(content) < 10:
        content = " " + str(content)
    return content


@register.filter
def grade(target, rate_data):
    submitted_grade = 0

    if isinstance(target, Problem):
        target_problem_id = target.id
    else:
        target_problem_id = target.problem.id

    for data in rate_data:
        if data.problem_id == target_problem_id:
            submitted_grade += data.grade

    return submitted_grade


@register.filter
def get_absolute_url(problem_id, category):
    return reverse(f'psat:{category}_detail', kwargs={'problem_id': problem_id})


# @register.filter
# def is_answer(target, answer_data):  # Generate HTML Tag Related to Answer Icon
#     correct_answer = target.correct_answer()
#     submitted_answer = ''
#
#     if isinstance(target, Problem):
#         target_problem_id = target.id
#     else:
#         target_problem_id = target.problem.id
#
#     for data in answer_data:
#         if data.problem_id == target_problem_id:
#             submitted_answer = data.answer
#
#     if submitted_answer == correct_answer:
#         result = True
#     else:
#         result = False
#
#     return result


@register.filter
def add_hyphen(content):  # Add Hyphens between Year, Ex, Sub
    pattern = r'(\d{4})(\w{2})(\w{2})'
    return re.sub(pattern, r'\1-\2-\3', content)


@register.filter()
def int2kor(value):  # Convert Integer to Korean Alphabet
    kor_nums = [_('일'), _('월'), _('화'), _('수'), _('목'), _('금'), _('토')]
    s = str(value)
    result = ''
    for c in s:
        result += kor_nums[int(c)]
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


# @register.filter
# def exam_year(content):  # Return Exam Year
#     if isinstance(content, Exam):
#         _year = content.year
#     elif isinstance(content, Problem):
#         _year = content.exam.year
#     else:
#         _year = content.problem.exam.year
#     return _year
#
#
# @register.filter
# def exam_ex(content):  # Return Exam Ex
#     if isinstance(content, Exam):
#         _ex = content.ex
#     elif isinstance(content, Problem):
#         _ex = content.exam.ex
#     else:
#         _ex = content.problem.exam.ex
#     return _ex
#
#
# @register.filter
# def exam_exam(content):  # Return Exam Exam
#     if isinstance(content, Exam):
#         _exam = content.exam
#     elif isinstance(content, Problem):
#         _exam = content.exam.exam
#     else:
#         _exam = content.problem.exam.exam
#     return _exam
#
#
# @register.filter
# def exam_sub(content):  # Return Exam Sub
#     if isinstance(content, Exam):
#         _sub = content.sub
#     elif isinstance(content, Problem):
#         _sub = content.exam.sub
#     else:
#         _sub = content.problem.exam.sub
#     return _sub
#
#
# @register.filter
# def exam_subject(content):  # Return Exam Subject
#     if isinstance(content, Exam):
#         _subject = content.subject
#     elif isinstance(content, Problem):
#         _subject = content.exam.subject
#     else:
#         _subject = content.problem.exam.subject
#     return _subject
#
#
# @register.filter
# def problem_id(content):  # Return Problem ID
#     if isinstance(content, Problem):
#         _id = content.id
#     else:
#         _id = content.problem.id
#     return _id
#
#
# @register.filter
# def problem_number(content):  # Return Problem Number
#     if isinstance(content, Problem):
#         _number = content.number
#     else:
#         _number = content.problem.number
#     return _number
#
#
# @register.filter
# def problem_question(content):  # Return Problem Question
#     if isinstance(content, Problem):
#         _question = content.question
#     else:
#         _question = content.problem.question
#     return _question
#
#
# @register.filter
# def find_url(content):
#     if isinstance(content, Problem):  # Return URL for Problem / Like / Rate / Answer Detail
#         _url = reverse('psat:detail', kwargs={'problem_id': content.id})
#     elif isinstance(content, Like):
#         _url = reverse('psat:like_detail', kwargs={'problem_id': content.problem.id})
#     elif isinstance(content, Rate):
#         _url = reverse('psat:rate_detail', kwargs={'problem_id': content.problem.id})
#     elif isinstance(content, PsatAnswer):
#         _url = reverse('psat:answer_detail', kwargs={'problem_id': content.problem.id})
#     else:
#         _url = reverse('psat:base')
#     return _url


# @register.filter
# def like_icon(content, like_list):
#     if isinstance(content, Problem):
#         target_id = content.id
#     else:
#         target_id = content.problem.id
#
#     if target_id in like_list:
#         result_heart_icon = f'<i id="psatLike{target_id}" class="fa-solid fa-heart like-button" data-problem-id="{target_id}"></i>'
#     else:
#         result_heart_icon = f'<i id="psatLike{target_id}" class="fa-regular fa-heart like-button" data-problem-id="{target_id}"></i>'
#
#     return result_heart_icon


# @register.filter
# def heart_icon(content, like_list):
#     empty_heart = 'fa-regular'
#     solid_heart = 'fa-solid'
#
#     if isinstance(content, Problem):
#         target_problem_id = content.id
#     else:
#         target_problem_id = content.problem.id
#
#     if target_problem_id in like_list:
#         return solid_heart
#     else:
#         return empty_heart


# @register.filter
# def star_icon(content, rate_data):
#     empty_star = '<i class="fa-regular fa-star"></i>'
#     solid_star = '<i class="fa-solid fa-star"></i>'
#     total_star = ''
#     grade = 0
#
#     if isinstance(content, Problem):
#         target_problem_id = content.id
#     else:
#         target_problem_id = content.problem.id
#
#     for data in rate_data:
#         if data.problem.id == target_problem_id:
#             grade += data.grade
#
#     if grade:
#         for num in range(0, grade):
#             total_star += solid_star
#         for num in range(grade, 5):
#             total_star += empty_star
#     else:
#         for num in range(0, 5):
#             total_star += empty_star
#
#     return total_star


# @register.simple_tag
# def other_problem(target, arrow_type):  # Return Previous or Next Problem
#     html = ''
#     if arrow_type == 'up':
#         _type = 'prev'
#         _icon = '<i class="fa-solid fa-arrow-up"></i>'
#         _margin = ' mx-1'
#     else:
#         _type = 'next'
#         _icon = '<i class="fa-solid fa-arrow-down"></i>'
#         _margin = ''
#
#     if target:
#         _url = find_url(target)
#         html = f'<a href="{_url}" id="{_type}-page" class="btn btn-circle btn-secondary btn-sm{_margin}">\n' \
#                f'{_icon}\n' \
#                f'</a>'
#
#     return mark_safe(html)


# @register.filter
# def all_other_problem(content, offset):  # Return Previous or Next Problem
#     _url = ''
#     if isinstance(content, Problem):
#         other_id = content.id + offset
#         try:
#             _url = reverse('psat:detail', kwargs={'problem_id': other_id})
#         except Problem.DoesNotExist:
#             _url = ''
#     elif isinstance(content, Like):
#         other_id = content.problem.id + offset
#         try:
#             _url = reverse('psat:detail', kwargs={'problem_id': other_id})
#         except Problem.DoesNotExist:
#             _url = ''
#
#     return _url


# @register.simple_tag
# def like_icon(user, target, like_list):  # Generate HTML Tag Related to Like Icon
#     if isinstance(target, Problem):
#         target_id = target.id
#     else:
#         target_id = target.problem.id
#
#     if not user.is_authenticated:
#         _icon = '<i class="fa-regular fa-heart like-button" href="#" data-toggle="modal" data-target="#loginModal"></i>'
#     else:
#         if target_id in like_list:
#             _icon = f'<i id="psatLike{target_id}" class="fa-solid fa-heart like-button" data-problem-id="{target_id}"></i>'
#         else:
#             _icon = f'<i id="psatLike{target_id}" class="fa-regular fa-heart like-button" data-problem-id="{target_id}"></i>'
#
#     return mark_safe(_icon)


# @register.simple_tag
# def rate_icon(user, target, rate_data):  # Generate HTML Tag Related to Rate Icon
#     empty_star = '<i class="fa-regular fa-star"></i>'
#     solid_star = '<i class="fa-solid fa-star"></i>'
#     _icon = ''
#     grade = 0
#
#     if isinstance(target, Problem):
#         target_id = target.id
#     else:
#         target_id = target.problem.id
#
#     for data in rate_data:
#         if data.problem.id == target_id:
#             grade += data.grade
#
#     if grade:
#         for num in range(0, grade):
#             _icon += solid_star
#         for num in range(grade, 5):
#             _icon += empty_star
#     else:
#         for num in range(0, 5):
#             _icon += empty_star
#
#     if not user.is_authenticated:
#         html = f'<a class="rate-button" href="#" data-toggle="modal" data-target="#loginModal">\n' \
#                f'{_icon}\n' \
#                f'</a>'
#     else:
#         html = f'<a id="psatRate{target_id}" class="rate-button" href="#" data-toggle="modal" data-target="#rateModal" data-problem-id="{target_id}">\n' \
#                f'{_icon}\n' \
#                f'</a>'
#
#     return mark_safe(html)


# @register.filter
# def answer_icon(content, answer_data):  # Generate HTML Tag Related to Answer Icon
#     correct_icon = '<i class="fa-solid fa-circle-check"></i>'
#     wrong_icon = '<i class="fa-solid fa-circle-xmark"></i>'
#
#     if isinstance(content, Problem):
#         target_problem_id = content.id
#         correct_answer = content.answer
#     else:
#         target_problem_id = content.problem.id
#         correct_answer = content.problem.answer
#
#     submitted_answer = ''
#     for data in answer_data:
#         if data.problem.id == target_problem_id:
#             submitted_answer = data.answer
#
#     if submitted_answer:
#         if submitted_answer == correct_answer:
#             _icon = correct_icon
#         else:
#             _icon = wrong_icon
#     else:
#         _icon = ''
#
#     return _icon


# @register.filter
# def _range(start, end):
#     return range(start, end+1)


