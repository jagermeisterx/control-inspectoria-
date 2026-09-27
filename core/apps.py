from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Inspectoría"

    def ready(self):
        # Registra el lookup unaccent_icontains y la función SQL de SQLite
        # para búsquedas insensibles a acentos (core/db_text.py).
        from django.db.backends.signals import connection_created

        from . import db_text  # noqa: F401
        from .db_text import registrar_funciones_sqlite

        connection_created.connect(
            registrar_funciones_sqlite, dispatch_uid="core.unaccent_sqlite"
        )
