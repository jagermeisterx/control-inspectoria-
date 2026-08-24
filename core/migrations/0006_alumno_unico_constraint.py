from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_dedup_y_constraint"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="alumno",
            constraint=models.UniqueConstraint(
                fields=("nombre", "apellido", "anio"),
                name="alumno_unico_nombre_anio",
            ),
        ),
    ]
