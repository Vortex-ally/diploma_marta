from django.apps import AppConfig

class BikesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bikes'
    verbose_name = 'Велосипеди'

    def ready(self):
        import bikes.signals  # noqa: F401
