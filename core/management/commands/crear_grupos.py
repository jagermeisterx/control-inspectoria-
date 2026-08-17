from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.roles import GRUPOS


class Command(BaseCommand):
    help = "Crea los grupos de roles de la plataforma (inspector_general, inspector, profesor, director)"

    def handle(self, *args, **options):
        for nombre in GRUPOS:
            grupo, creado = Group.objects.get_or_create(name=nombre)
            estado = "creado" if creado else "ya existía"
            self.stdout.write(self.style.SUCCESS(f"Grupo '{nombre}' {estado}."))
