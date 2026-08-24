from django.db import migrations, models

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
        migrations.RunPython(limpiar, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="alumno",
            constraint=models.UniqueConstraint(
                fields=("nombre", "apellido", "anio"),
                name="alumno_unico_nombre_anio",
            ),
        ),
    ]
