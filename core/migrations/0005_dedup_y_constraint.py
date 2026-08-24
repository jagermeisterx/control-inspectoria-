from django.db import migrations

import core.dedup


def limpiar(apps, schema_editor):
    core.dedup.normalizar_cursos_todos(dry_run=False)
    core.dedup.fusionar_alumnos(dry_run=False)
    core.dedup.eliminar_registros_repetidos(dry_run=False)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_seed_role_groups"),
    ]

    operations = [
        # La constraint va en su propia migración (0006): Postgres rechaza
        # ALTER TABLE sobre una tabla con trigger events pendientes de las
        # escrituras anteriores dentro de la misma transacción.
        migrations.RunPython(limpiar, migrations.RunPython.noop),
    ]
