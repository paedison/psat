from django.core.exceptions import ObjectDoesNotExist

from common.constants.icon_set import ConstantIconSet
from dashboard.models.psat_data_models import PsatLikeLog, PsatRateLog, PsatSolveLog
from psat.models import Like, Rate, Solve
from reference.models.psat_models import PsatProblem


class UpdateViewVariable:
    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs

        self.user_id: int | None = request.user.id if request.user.is_authenticated else None
        self.view_type: str = kwargs.get('view_type', 'problem')

        self.problem_id: int = int(self.kwargs.get('problem_id'))
        self.problem: PsatProblem = (
            PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .get(id=self.problem_id)
        )

        is_liked: str = request.POST.get('is_liked', '')
        is_liked_dict: dict = {'True': True, 'False': False, 'None': False}
        self.is_liked: str | bool = '' if is_liked == '' else not is_liked_dict[is_liked]

        rating: str = request.POST.get('rating', '')
        self.rating: str | int = '' if rating == '' else int(rating)

        answer: str = self.request.POST.get('answer', '')
        self.answer: int = '' if answer == '' else int(answer)

        self.ip_address: str = request.META.get('REMOTE_ADDR')

    def get_find_filter(self) -> dict:
        find_filter = {
            'problem_id': self.problem_id,
            'user_id': self.user_id,
        }
        if not self.user_id:
            find_filter['ip_address'] = self.ip_address
        return find_filter

    def get_update_filter(self) -> dict:
        filter_expr = {
            'problem': {},
            'like': {'is_liked': self.is_liked},
            'rate': {'rating': self.rating},
            'solve': {
                'answer': self.answer,
                'is_correct': self.answer == self.problem.answer,
            },
        }
        return filter_expr[self.view_type]

    def get_create_filter(self, find_filter) -> dict:
        create_filter = find_filter.copy()
        update_expr = {
            'problem': {},
            'like': {'is_liked': self.is_liked},
            'rate': {'rating': self.rating},
            'solve': {
                'answer': self.answer,
                'is_correct': self.answer == self.problem.answer,
            },
        }
        create_filter.update(update_expr[self.view_type])
        return create_filter

    def get_data_instance(self, find_filter):
        model_dict = {
            'like': Like,
            'rate': Rate,
            'solve': Solve,
        }
        data_model = model_dict[self.view_type]

        if data_model:
            try:
                instance = data_model.objects.get(**find_filter)
                update_filter = self.get_update_filter()
                for key, item in update_filter.items():
                    setattr(instance, key, item)
                instance.save()
            except ObjectDoesNotExist:
                create_filter = self.get_create_filter(find_filter)
                instance = data_model.objects.create(**create_filter)
            return instance

    def make_log_instance(self, data_instance, find_filter):
        create_filter = self.get_create_filter(find_filter)
        if data_instance:
            model_dict = {
                'like': PsatLikeLog,
                'rate': PsatRateLog,
                'solve': PsatSolveLog,
            }
            model = model_dict[self.view_type]
            data_id = data_instance.id
            recent_log = model.objects.filter(**find_filter).order_by('-id').first()
            repetition = recent_log.repetition + 1 if recent_log else 1
            create_filter.update(
                {'repetition': repetition, 'data_id': data_id}
            )
            model.objects.create(**create_filter)

    def get_option_name(self) -> str:
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        return option_dict[self.view_type]


class PsatCustomUpdateViewMixIn(ConstantIconSet):
    """Represent PSAT custom data update view mixin."""
    @staticmethod
    def get_update_variable(request, **kwargs):
        return UpdateViewVariable(request, **kwargs)


class SolveModalViewVariable:
    def __init__(self, request):
        self.request = request
        self.problem_id = int(self.request.POST.get('problem_id'))

        answer = self.request.POST.get('answer')
        self.answer = int(answer) if answer else None

        problem = PsatProblem.objects.get(id=self.problem_id)
        self.is_correct = None if self.answer is None else (self.answer == problem.answer)


class PsatSolveModalViewMixIn(ConstantIconSet):
    """Represent PSAT Solve data update modal view mixin."""
    @staticmethod
    def get_solve_modal_variable(request):
        return SolveModalViewVariable(request)
