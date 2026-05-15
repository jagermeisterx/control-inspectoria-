from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Crea el superusuario inicial si no existe"

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("admin", "admin@inspectoria.cl", "admin1234")
            self.stdout.write(self.style.SUCCESS("Superusuario creado: admin / admin1234"))
        else:
            self.stdout.write("Ya existe un superusuario.")
