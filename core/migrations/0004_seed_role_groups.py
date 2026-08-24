from django.db import migrations

from core.roles import GRUPOS


def crear_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nombre in GRUPOS:
        Group.objects.get_or_create(name=nombre)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alumno_es_campo_atraso_motivo_llamadaapoderado"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, migrations.RunPython.noop),
    ]
