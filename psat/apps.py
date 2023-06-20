from django.apps import AppConfig


class PsatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'psat'

    def ready(self):
        import log.signals
