from django.db import migrations


def crear_extension_unaccent(apps, schema_editor):
    # Solo Postgres; en SQLite la función equivalente (django_unaccent)
    # la registra core.db_text en la señal connection_created.
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_acciones_disciplinarias"),
    ]

    operations = [
        migrations.RunPython(crear_extension_unaccent, migrations.RunPython.noop),
    ]
