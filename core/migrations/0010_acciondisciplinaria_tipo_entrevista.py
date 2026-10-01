# Agrega el tipo de acción "Entrevista" (entre "Llamada a apoderado" y
# "Suspensión", por gravedad). Cambio solo de metadatos: mismo max_length y
# sin enum nativo, por lo que no altera el DDL ni los datos existentes.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_unaccent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acciondisciplinaria',
            name='tipo',
            field=models.CharField(choices=[('LLAMADA', 'Llamada a apoderado'), ('ENTREVISTA', 'Entrevista'), ('SUSPENSION', 'Suspensión')], default='LLAMADA', max_length=20, verbose_name='Tipo de acción'),
        ),
    ]
