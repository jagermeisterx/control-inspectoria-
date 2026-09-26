# Renombra LlamadaApoderado -> AccionDisciplinaria (conserva datos) +
# renombra detalle -> observaciones, agrega tipo de acción.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_configuracionregistro'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LlamadaApoderado',
            new_name='AccionDisciplinaria',
        ),
        migrations.RenameField(
            model_name='acciondisciplinaria',
            old_name='detalle',
            new_name='observaciones',
        ),
        migrations.AlterField(
            model_name='acciondisciplinaria',
            name='observaciones',
            field=models.TextField(verbose_name='Observaciones'),
        ),
        migrations.AlterField(
            model_name='acciondisciplinaria',
            name='alumno',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='acciones',
                to='core.alumno',
            ),
        ),
        migrations.AlterModelOptions(
            name='acciondisciplinaria',
            options={
                'ordering': ['-fecha', '-hora'],
                'verbose_name': 'Acción disciplinaria',
                'verbose_name_plural': 'Acciones disciplinarias',
            },
        ),
        migrations.AddField(
            model_name='acciondisciplinaria',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('LLAMADA', 'Llamada a apoderado'),
                    ('SUSPENSION', 'Suspensión'),
                ],
                default='LLAMADA',
                max_length=20,
                verbose_name='Tipo de acción',
            ),
        ),
    ]
