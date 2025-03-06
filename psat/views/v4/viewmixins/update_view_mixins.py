from . import base_mixins

from psat.models import psat_data_models


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):

    def invert_post_variable_by_bool(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        post_variable_dict = {'True': True, 'False': False, 'None': False}
        if post_variable == '':
            return ''
        return not post_variable_dict[post_variable]

    def get_post_variable_by_integer(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        if post_variable == '':
            return ''
        return int(post_variable)


class CustomUpdateViewMixIn(BaseMixIn):
    """Represent PSAT custom data update view mixin."""
    option_dict = {
        'like': 'is_liked',
        'rate': 'rating',
        'solve': 'is_correct'
    }
    data_model_dict = {
        'like': psat_data_models.Like,
        'rate': psat_data_models.Rate,
        'solve': psat_data_models.Solve,
    }
    log_model_dict = {
        # 'like': psat_log_models.PsatLikeLog,
        # 'rate': psat_log_models.PsatRateLog,
        # 'solve': psat_log_models.PsatSolveLog,
    }

    def get_update_filter_by_problem(self, view_type, problem):
        is_liked = self.invert_post_variable_by_bool('is_liked')
        rating = self.get_post_variable_by_integer('rating')
        answer = self.get_post_variable_by_integer('answer')
        is_correct = answer == problem.answer
        update_filter_expr = {
            'like': {'is_liked': is_liked},
            'rate': {'rating': rating},
            'solve': {
                'answer': answer,
                'is_correct': is_correct,
            },
        }
        return update_filter_expr[view_type]
