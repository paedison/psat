from django.db import transaction
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from dashboard.models.psat_data_models import PsatOpenLog
from psat.models import Open, Memo, Tag
from reference.models import PsatProblem
from .base_view_mixins import PsatCustomDataSet, PsatViewInfo


class DetailViewVariable:
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

        self.ip_address: str = request.META.get('REMOTE_ADDR')

        if request.user.is_authenticated:
            self.memo: Memo = Memo.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
            self.my_tag: Tag = Tag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
        else:
            self.memo = self.my_tag = None

    def get_find_filter(self):
        find_filter = {
            'problem_id': self.problem_id,
            'user_id': self.user_id,
        }
        if not self.user_id:
            find_filter['ip_address'] = self.ip_address
        return find_filter

    def get_open_instance(self):
        find_filter = self.get_find_filter()
        with transaction.atomic():
            instance, is_created = Open.objects.get_or_create(**find_filter)
            recent_log = PsatOpenLog.objects.filter(**find_filter).last()
            if recent_log:
                repetition = recent_log.repetition + 1
            else:
                repetition = 1
            create_filter = find_filter.copy()
            extra_filter = {
                'data_id': instance.id,
                'repetition': repetition,
            }
            create_filter.update(extra_filter)
            PsatOpenLog.objects.create(**create_filter)

    def get_prev_next_prob(self, custom_data):
        if self.request.method == 'GET':
            custom_list = list(custom_data.values_list('id', flat=True))
            prev_prob = next_prob = None
            last_id = len(custom_list) - 1
            q = custom_list.index(self.problem_id)
            if q != 0:
                prev_prob = custom_data[q - 1]
            if q != last_id:
                next_prob = custom_data[q + 1]
            return prev_prob, next_prob

    def get_list_data(self, custom_data) -> list:
        organized_dict = {}
        organized_list = []
        for prob in custom_data:
            key = prob['psat_id']
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam, subject = prob['year'], prob['exam'], prob['subject']
            problem_url = reverse_lazy(
                'psat:detail',
                kwargs={'view_type': self.view_type, 'problem_id': prob['id']}
            )
            list_item = {
                'exam_name': f"{year}년 {exam} {subject}",
                'problem_number': prob['number'],
                'problem_id': prob['id'],
                'problem_url': problem_url
            }
            organized_dict[key].append(list_item)

        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i + 5]
                organized_list.extend(row)
        return organized_list


class PsatDetailViewMixIn(
    ConstantIconSet,
    PsatViewInfo,
    # PsatProblemVariableSet,
    PsatCustomDataSet,
):
    """Represent PSAT detail view mixin."""
    @staticmethod
    def get_detail_variable(request, **kwargs):
        return DetailViewVariable(request, **kwargs)
