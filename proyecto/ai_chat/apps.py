from django.apps import AppConfig


class AiChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_chat'

    def ready(self):
        # Conectar el Observer de señales Django
        import ai_chat.signals
