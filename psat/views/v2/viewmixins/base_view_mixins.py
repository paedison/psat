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
        }
        return {
            'menu': 'psat',
            'view_type': view_type,
            'color': color_dict[view_type],
        }


class PsatCustomVariableSet:
    """Represent PSAT custom data variable."""
    request: any
    kwargs: dict
    problem: PsatProblem
    user_id: int
    view_type: str
    problem_id: int

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def problem_id(self) -> int:
        return int(self.kwargs.get('problem_id'))

    @property
    def problem(self):
        return (
            PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .get(id=self.problem_id)
        )

    @property
    def view_type(self) -> str:
        """Get view type from [ problem, like, rate, solve ]. """
        return self.kwargs.get('view_type', 'problem')

    def get_problem_data(self):
        return PsatProblem.objects.filter(psat_id=self.problem.psat_id).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number',
        )

    def get_like_data(self):
        return (
            PsatProblem.objects.filter(likes__user_id=self.user_id, likes__is_liked=True)
            .prefetch_related('likes').order_by('-psat__year', 'id')
            .values(
                'id', 'psat_id', 'psat__year', 'psat__exam__name',
                'psat__subject__name', 'number', 'likes__is_liked',
            )
        )

    def get_rate_data(self):
        return (
            PsatProblem.objects.filter(rates__user_id=self.user_id)
            .prefetch_related('rates').order_by('-psat__year', 'id')
        ).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number', 'rates__rating',
        )

    def get_solve_data(self):
        return (
            PsatProblem.objects.filter(solves__user_id=self.user_id)
            .prefetch_related('solves').order_by('-psat__year', 'id')
        ).values(
            'id', 'psat_id', 'psat__year', 'psat__exam__name',
            'psat__subject__name', 'number', 'solves__is_correct',
        )

    def get_custom_data(self, view_type):
        custom_data_dict = {
            'problem': self.get_problem_data(),
            'like': self.get_like_data(),
            'rate': self.get_rate_data(),
            'solve': self.get_solve_data(),
        }
        return custom_data_dict[view_type]
