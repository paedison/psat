from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):

    def invert_post_variable_by_bool(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        if post_variable == '':
            return ''
        else:
            post_variable_dict = {'True': True, 'False': False, 'None': False}
            return not post_variable_dict[post_variable]

    def get_post_variable_by_integer(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        if post_variable == '':
            return ''
        else:
            return int(post_variable)


class CustomUpdateViewMixIn(BaseMixIn):
    """Represent PSAT custom data update view mixin."""

    @staticmethod
    def get_option_name_by_view_type(view_type: str) -> str:
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        return option_dict[view_type]

    def get_find_filter_by_problem_id(self, problem_id: str) -> dict:
        user_id = self.request.user.id
        find_filter = {
            'problem_id': problem_id,
            'user_id': user_id,
        }
        if not user_id:
            find_filter['ip_address'] = self.request.META.get('REMOTE_ADDR')
        return find_filter

    def get_filter_dict_by_problem_id(self, view_type: str, problem_id: str):
        problem = self.get_problem_by_problem_id(problem_id)
        find_filter = self.get_find_filter_by_problem_id(problem_id)

        is_liked = self.invert_post_variable_by_bool('is_liked')
        rating = self.get_post_variable_by_integer('rating')
        answer = self.get_post_variable_by_integer('answer')
        is_correct = answer == problem.answer

        update_filter_expr = {
            'problem': {},
            'like': {'is_liked': is_liked},
            'rate': {'rating': rating},
            'solve': {
                'answer': answer,
                'is_correct': is_correct,
            },
        }
        update_filter = update_filter_expr[view_type]

        create_filter = find_filter.copy()
        create_filter.update(update_filter)

        return {
            'find': find_filter,
            'update': update_filter,
            'create': create_filter,
        }

    def get_data_instance_by_filter_dict(self, view_type: str, filter_dict: dict):
        model_dict = {
            'like': self.like_model,
            'rate': self.rate_model,
            'solve': self.solve_model,
        }
        data_model = model_dict[view_type]

        find_filter = filter_dict['find']
        update_filter = filter_dict['update']
        create_filter = filter_dict['create']
        if data_model:
            try:
                instance = data_model.objects.get(**find_filter)
                for key, item in update_filter.items():
                    setattr(instance, key, item)
                instance.save()
            except data_model.DoesNotExist:
                instance = data_model.objects.create(**create_filter)
            return instance

    def get_log_model_by_view_type(self, view_type: str):
        log_model_dict = {
            'like': self.like_log_model,
            'rate': self.rate_log_model,
            'solve': self.solve_log_model,
        }
        return log_model_dict[view_type]

    def make_log_instance_by_filter_dict(
            self, view_type: str, data_instance, filter_dict: dict):
        find_filter = filter_dict['find']
        create_filter = filter_dict['create']
        if data_instance:
            log_model = self.get_log_model_by_view_type(view_type)
            recent_log = log_model.objects.filter(**find_filter).order_by('-id').first()
            repetition = recent_log.repetition + 1 if recent_log else 1
            create_filter.update(
                {'repetition': repetition, 'data_id': data_instance.id}
            )
            log_model.objects.create(**create_filter)
