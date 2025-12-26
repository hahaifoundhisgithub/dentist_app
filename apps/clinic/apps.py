from django.apps import AppConfig


class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clinic'
    
    def ready(self):
        """
        當應用程式準備就緒時，載入信號處理器
        """
        import apps.clinic.signals  # noqa