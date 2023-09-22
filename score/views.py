from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db.models import Max
from django.shortcuts import render, redirect

from . import models as score_models
from psat import models as psat_models
from .forms import TemporaryAnswerForm


exam_list = [
        {'year': 2023, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2023, 'ex': '칠급', 'exam2': '7급공채'},
        {'year': 2023, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2022, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2022, 'ex': '칠급', 'exam2': '7급공채'},
        {'year': 2022, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2021, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2021, 'ex': '칠급', 'exam2': '7급공채'},
        {'year': 2021, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2021, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2020, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2020, 'ex': '칠급', 'exam2': '7급공채'},
        {'year': 2020, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2020, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2019, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2019, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2019, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2018, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2018, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2018, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2017, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2017, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2017, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2016, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2016, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2016, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2015, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2015, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2015, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2014, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2014, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2014, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2013, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2013, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2013, 'ex': '외시', 'exam2': '외교원/외무고시'},
        {'year': 2013, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2012, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2012, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2012, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2011, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2011, 'ex': '민경', 'exam2': '민간경력'},
        {'year': 2011, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2010, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2010, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2009, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2009, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2008, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2008, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2007, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2007, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2006, 'ex': '행시', 'exam2': '5급공채/행정고시'},
        {'year': 2006, 'ex': '견습', 'exam2': '견습'},
        {'year': 2006, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2005, 'ex': '견습', 'exam2': '견습'},
        {'year': 2005, 'ex': '외시', 'exam2': '외교원/외무고시'},
        {'year': 2005, 'ex': '입시', 'exam2': '입법고시'},
        {'year': 2004, 'ex': '외시', 'exam2': '외교원/외무고시'},
]


class ScoreTemplate:
    """ Represent the appropriate templates. """
    list_base = 'score/score_list.html'  # score_list_view w/ GET and no htmx
    list_content = f'{list_base}#content'  # score_list_view w/ GET and htmx
    list_main = f'{list_base}#list_main'  # score_list_view w/ POST

    detail_base = 'score/score_detail.html'  # score_detail_view w/ no htmx
    detail_content = f'{detail_base}#content'  # score_detail_view w/ htmx

    initial_form = f'{detail_base}#initial_form'  # score_form w/ POST and not form.is_valid
    scored_form = f'{detail_base}#scored_form'  # score_form w/ form.is_valid or temporary_ans

    score_confirmed_base = 'score/score_confirmed.html'  # score_confirm w/ GET and no htmx
    score_confirmed_content = f'{score_confirmed_base}#content'  # score_confirm w/ GET and htmx
    score_confirmed_modal = 'snippets/modal.html#score_confirmed'  # score_confirm w/ POST


class TargetAnswer:
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    def __init__(self, request, problem=None, exam=None):
        self.request: WSGIRequest = request
        self.problem: psat_models.Problem = problem
        self.exam: psat_models.Exam = exam

    @property
    def user(self):
        """ Return current user. """
        return self.request.user

    def get_exam_ids(self, boolean: bool) -> set[int] | None:
        """
        Return the exam ids for the appropriate purpose.
            boolean = False -> return 'temporary_exam_ids'
            boolean = True -> return 'confirmed_exam_ids'
        """
        return set(score_models.TemporaryAnswer.objects.filter(
            user=self.request.user, is_confirmed=boolean).order_by(
            'problem__id').values_list('problem__exam__id', flat=True))

    @property
    def temporary_exam_ids(self) -> set[int] | None:
        """ Return temporary exam ids for checking '작성 중'. """
        return self.get_exam_ids(False)

    @property
    def confirmed_exam_ids(self) -> set[int] | None:
        """ Return confirmed exam ids for checking '제출 완료'. """
        return self.get_exam_ids(True)

    @property
    def temporary_ans(self) -> score_models.TemporaryAnswer | None:
        """ Return the one TemporaryAnswer object. """
        if self.problem:
            return score_models.TemporaryAnswer.objects.filter(
                user=self.user, problem=self.problem, is_confirmed=False).first()

    @property
    def temporary_answers(self) -> score_models.TemporaryAnswer.objects:
        """ Return the TemporaryAnswer objects. """
        if self.exam:
            return score_models.TemporaryAnswer.objects.filter(
                user=self.user, problem__exam=self.exam, is_confirmed=False
            ).order_by('problem__id')

    @property
    def temporary_answers_problem_ids(self) -> list | None:
        """ Return the TemporaryAnswer objects problem ids. """
        if self.temporary_answers:
            return self.temporary_answers.values_list('problem', flat=True)

    @property
    def confirmed_answers(self) -> score_models.ConfirmedAnswer.objects:
        """ Return the ConfirmedAnswer objects. """
        if self.exam is not None:
            confirmed_times = score_models.ConfirmedAnswer.objects.filter(
                user=self.user, problem__exam=self.exam).aggregate(
                Max('confirmed_times'))['confirmed_times__max']
            return score_models.ConfirmedAnswer.objects.filter(
                user=self.user, problem__exam=self.exam, confirmed_times=confirmed_times
            ).order_by('problem__id')


def score_list(request) -> render:
    """ Represent score list view sorted by the exam year. """
    # Get the template name
    if request.method == 'POST':
        template_name = ScoreTemplate.list_main
    else:
        template_name = ScoreTemplate.list_main if request.htmx else ScoreTemplate.list_base

    # Get the temporary and confirmed answers list
    target_answer = TargetAnswer(request)  # Get TargetAnswer class instance
    temporary_exam_ids = target_answer.temporary_exam_ids
    confirmed_exam_ids = target_answer.confirmed_exam_ids

    # Get paginator for total exam list
    paginate_by = 10
    paginator = Paginator(exam_list, paginate_by)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=3, on_ends=1)

    # Return the current status of the target exam
    def get_status(target_exam):
        try:
            if target_exam.id in temporary_exam_ids:
                return False  # 작성 중
            elif target_exam.id in confirmed_exam_ids:
                return True  # 제출 완료
            else:
                return None  # 작성 전
        except AttributeError:
            return 'N/A'  # 해당 사항 없음(시험에서 제외된 과목)

    # Get exam_id and status of page_obj
    exams = psat_models.Exam.objects.all()
    for obj in page_obj:
        exam_eoneo = exams.filter(year=obj['year'], ex=obj['ex'], sub='언어').first()
        exam_jaryo = exams.filter(year=obj['year'], ex=obj['ex'], sub='자료').first()
        exam_sanghwang = exams.filter(year=obj['year'], ex=obj['ex'], sub='상황').first()
        obj['eoneo'] = {
            'sub': '언어',
            'exam_id': exam_eoneo.id if exam_eoneo else None,
            'status': get_status(exam_eoneo),
        }
        obj['jaryo'] = {
            'sub': '자료',
            'exam_id': exam_jaryo.id if exam_jaryo else None,
            'status': get_status(exam_jaryo),
        }
        obj['sanghwang'] = {
            'sub': '상황',
            'exam_id': exam_sanghwang.id if exam_sanghwang else None,
            'status': get_status(exam_sanghwang),
        }

    # Get context data
    info = {
        'menu': 'score',
        'title': 'Score',
        'icon': '<i class="fa-solid fa-circle-check fa-fw"></i>',
    }
    context = {
        'info': info,
        'page_obj': page_obj,
        'exams': exams,
        'page_range': page_range,
    }
    return render(request, template_name, context)


def score_detail(request, exam_id: int) -> render:
    """ Represent score detail view for forms before submit. """
    # Get the template name
    template_name = ScoreTemplate.detail_content if request.htmx else ScoreTemplate.detail_base

    # Get temporary answer problem ids
    exam = psat_models.Exam.objects.get(id=exam_id)
    target_answer = TargetAnswer(request, exam=exam)  # Get TargetAnswer class instance
    temporary_answers_problem_ids = target_answer.temporary_answers_problem_ids

    # Get submitted answer for each target problem
    problems = exam.problems.all()
    for problem in problems:
        if temporary_answers_problem_ids:
            if problem.id in temporary_answers_problem_ids:
                target_answer2 = TargetAnswer(
                    request, exam=exam, problem=problem)  # Get TargetAnswer class instance
                problem.submitted_answer = target_answer2.temporary_ans.answer

    # Get context data
    info = {
        'menu': 'score',
        'title': f'{exam.full_title} 답안 제출',
        'exam_id': exam_id,
        'icon': '<i class="fa-solid fa-circle-check fa-fw"></i>',
    }
    context = {
        'info': info,
        'problems': problems,
    }
    return render(request, template_name, context)


def score_submit(request, problem_id: int) -> render:
    problem = psat_models.Problem.objects.get(id=problem_id)  # Get target problem for context

    if request.method == 'GET':
        return redirect('score:detail', exam_id=problem.exam_id)
    else:
        submitted_answer: int = int(request.POST.get('answer'))  # Get submitted answer
        target_answer = TargetAnswer(request, problem=problem)  # Get TargetAnswer class instance
        temporary_ans = target_answer.temporary_ans  # Get the one TemporaryAnswer object
        if temporary_ans is None:
            form = TemporaryAnswerForm(request.POST)  # Get the submitted form
            form.user = request.user.id
            if form.is_valid():
                template_name = ScoreTemplate.scored_form  # Get template name
                scored = form.save()
                context = {'scored': scored}  # Get context data
            else:
                template_name = ScoreTemplate.initial_form  # Get template name
                context = {'problem': problem}  # Get context data
        else:
            template_name = ScoreTemplate.scored_form  # Get template name
            temporary_ans.answer = submitted_answer
            temporary_ans.save()
            scored = temporary_ans
            context = {'scored': scored}  # Get context data
    # return render(request, template_name, context)
    return render(request, template_name, '')


def score_confirmed(request, exam_id: int):
    """
    Represent score confirm modal in POST method or
        score confirmed detail view after submit in GET method.
    """
    # Get the template name
    if request.method == 'POST':
        template_name = ScoreTemplate.score_confirmed_modal
    else:
        if request.htmx:
            template_name = ScoreTemplate.score_confirmed_content
        else:
            template_name = ScoreTemplate.score_confirmed_base

    exam = psat_models.Exam.objects.get(id=exam_id)
    target_answer = TargetAnswer(request, exam=exam)  # Get TargetAnswer class instance

    if request.method == 'POST':
        temporary_answers = target_answer.temporary_answers
        if exam.problems.count() != temporary_answers.count():
            all_confirmed = False
        else:
            for obj in temporary_answers:
                obj.is_confirmed = True
                obj.save()
                score_models.ConfirmedAnswer.objects.get_or_create(
                    user=request.user, problem=obj.problem, answer=obj.answer)
            all_confirmed = True
        context = {
            'all_confirmed': all_confirmed,
            'exam_id': exam_id,
        }
        return render(request, template_name, context)
    else:
        confirmed_answers = target_answer.confirmed_answers
        info = {
            'menu': 'score',
            'title': f'{exam.full_title} 성적 확인',
            'exam_id': exam_id,
            'icon': '<i class="fa-solid fa-circle-check fa-fw"></i>',
        }
        context = {
            'info': info,
            'confirmed_answers': confirmed_answers,
        }
        return render(request, template_name, context)


def score_modal(request):
    template_name = ScoreTemplate.score_confirmed_modal
    if request.method == 'GET':
        all_confirmed = exam_id = None
        message = '이미 제출한 답안은<br/>수정할 수 없습니다.'
    else:
        exam_id = request.POST.get('exam')
        exam = psat_models.Exam.objects.get(id=exam_id)
        target_answer = TargetAnswer(request, exam=exam)  # Get TargetAnswer class instance
        temporary_answers = target_answer.temporary_answers
        if exam.problems.count() != temporary_answers.count():
            all_confirmed = False
            message = '모든 문제의 정답을<br/>제출해주세요.'
        else:
            for obj in temporary_answers:
                obj.is_confirmed = True
                obj.save()
                score_models.ConfirmedAnswer.objects.get_or_create(
                    user=request.user, problem=obj.problem, answer=obj.answer)
            all_confirmed = True
            message = '정답이 정상적으로<br/>제출되었습니다.'
    context = {
        'all_confirmed': all_confirmed,
        'exam_id': exam_id,
        'message': message,
    }
    return render(request, template_name, context)
