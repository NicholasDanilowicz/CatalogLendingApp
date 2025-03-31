from django.apps import AppConfig

class AppConfig(AppConfig):
    name = 'sports-cataloging-lending-app'

    def ready(self):
        import app.signals
