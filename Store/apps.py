from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Store'
    verbose_name = "Store"

    def ready(self):
        # import the signals module to register signal handlers
        import Store.signals
