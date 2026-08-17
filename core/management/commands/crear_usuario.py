from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from core.roles import GRUPOS


class Command(BaseCommand):
    help = "Crea un usuario y lo asigna a un rol (inspector_general | inspector | profesor | director)"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--grupo", required=True, choices=GRUPOS)
        parser.add_argument("--password", required=True)
        parser.add_argument("--nombre", default="")
        parser.add_argument("--apellido", default="")

    def handle(self, *args, **options):
        grupo, _ = Group.objects.get_or_create(name=options["grupo"])
        user, creado = User.objects.get_or_create(
            username=options["username"],
            defaults={
                "first_name": options["nombre"],
                "last_name": options["apellido"],
            },
        )
        if creado:
            user.set_password(options["password"])
            self.stdout.write(self.style.SUCCESS(
                f"Usuario '{user.username}' creado y asignado a '{grupo.name}'."
            ))
        else:
            user.first_name = options["nombre"]
            user.last_name = options["apellido"]
            if options["password"]:
                user.set_password(options["password"])
            self.stdout.write(self.style.WARNING(
                f"Usuario '{user.username}' ya existía; se actualizaron sus datos y grupo."
            ))
        user.groups.add(grupo)
        user.save()
