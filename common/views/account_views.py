import vanilla

from common.constants.icon_set import ConstantIconSet


class LoginModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#login'


class LogoutModalView(vanilla.TemplateView):
    template_name = 'snippets/modal.html#logout'


class ProfileView(
    ConstantIconSet,
    vanilla.TemplateView,
):
    template_name = 'profile/v1/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        additional = {
            'icon_menu': self.ICON_MENU['profile']
        }
        context.update(additional)
        return context


class ChangePasswordModalView(vanilla.TemplateView):
    template_name = 'profile/v1/modal.html#change_password'


login_modal = LoginModalView.as_view()
logout_modal = LogoutModalView.as_view()
profile_view = ProfileView.as_view()
change_password_modal = ChangePasswordModalView.as_view()
