from django.db import transaction
from django.db.models import F
from django.urls import reverse_lazy

from dashboard.models.psat_data_models import PsatOpenLog
from psat.models import Open, Memo
from psat.models import Tag as PsatTag
from reference.models import PsatProblem
from .base_view_mixins import BaseViewMixin


class PsatDetailViewMixIn(BaseViewMixin):
    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)

        self.problem_id: int = int(self.kwargs.get('problem_id'))
        self.problem: PsatProblem = (
            PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=self.problem_id)
        )

        if request.user.is_authenticated:
            self.memo: Memo = Memo.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
            self.my_tag: PsatTag = PsatTag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
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
            try:
                q = custom_list.index(self.problem_id)
                if q != 0:
                    prev_prob = custom_data[q - 1]
                    prev_prob['icon'] = f'{self.ICON_NAV["prev_prob"]}'
                if q != last_id:
                    next_prob = custom_data[q + 1]
                    next_prob['icon'] = f'{self.ICON_NAV["next_prob"]}'
                return prev_prob, next_prob
            except ValueError:
                return None, None

    def get_list_data(self, custom_data) -> list:
        def get_view_list_data():
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

        if self.view_type == 'problem':
            return get_view_list_data()
        elif self.view_type == 'like' and self.is_liked is not None:
            return get_view_list_data()
        elif self.view_type == 'rate' and self.rating is not None:
            return get_view_list_data()
        elif self.view_type == 'solve' and self.is_correct is not None:
            return get_view_list_data()
        elif self.view_type == 'memo' and self.has_memo:
            return get_view_list_data()
        elif self.view_type == 'tag' and self.has_tag:
            return get_view_list_data()
