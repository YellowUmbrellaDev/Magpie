from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Default app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
