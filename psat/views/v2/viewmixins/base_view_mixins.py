from django.db.models import F

from reference.models.psat_models import PsatProblem


class PsatViewInfo:
    """Represent PSAT common variable."""
    @staticmethod
    def get_info(view_type) -> dict:
        """ Get the meta-info for the current view. """
        color_dict = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
            'tag': 'primary',
        }
        return {
            'menu': 'psat',
            'view_type': view_type,
            'color': color_dict[view_type],
        }


class PsatCustomDataSet:
    """Represent PSAT custom data variable."""
    request: any
    kwargs: dict

    def get_custom_data(self):
        problem_id = self.kwargs.get('problem_id')

        is_authenticated = self.request.user.is_authenticated
        user_id = self.request.user.id if is_authenticated else None

        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        custom_data = (
            PsatProblem.objects
            .annotate(year=F('psat__year'), exam=F('psat__exam__name'), subject=F('psat__subject__name'))
            .order_by('-psat__year', 'id'))

        if problem_id:
            problem = PsatProblem.objects.get(id=problem_id)
            problem_data = (
                custom_data.filter(psat_id=problem.psat_id)
                .values(*values_list_keys))
        else:
            problem_data = None

        if user_id:
            like_data = (
                custom_data.filter(likes__user_id=user_id, likes__is_liked=True)
                .annotate(is_liked=F('likes__is_liked'))
                .values(*values_list_keys, 'is_liked'))
            rate_data = (
                custom_data.filter(rates__user_id=user_id)
                .annotate(rating=F('rates__rating'))
                .values(*values_list_keys, 'rating'))
            solve_data = (
                custom_data.filter(solves__user_id=user_id)
                .annotate(user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
                .values(*values_list_keys, 'user_answer', 'is_correct'))
            memo_data = (
                custom_data.filter(memos__user_id=user_id)
                .values(*values_list_keys))
            tag_data = (
                custom_data.filter(tags__user_id=user_id)
                .values(*values_list_keys))
        else:
            like_data = rate_data = solve_data = memo_data = tag_data = None

        return {
            'problem': problem_data,
            'like': like_data,
            'rate': rate_data,
            'solve': solve_data,
            'memo': memo_data,
            'tag': tag_data,
        }
