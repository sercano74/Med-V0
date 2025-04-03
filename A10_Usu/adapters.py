from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse



# class NoNewUsersAccountAdapter(DefaultAccountAdapter):
#     def is_open_for_signup(self, request):
#         return False


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        path = reverse('completar_perfil_paciente')
        return path
