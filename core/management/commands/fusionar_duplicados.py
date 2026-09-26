from django.core.management.base import BaseCommand

from core.dedup import (
    eliminar_registros_repetidos,
    fusionar_alumnos,
    fusionar_alumnos_fuzzy,
    fusionar_alumnos_por_subset,
    normalizar_cursos_todos,
)


class Command(BaseCommand):
    help = (
        "Detecta duplicados (alumnos y registros idénticos) y cursos mal escritos. "
        "Por defecto SOLO muestra el reporte; usa --aplicar para ejecutar la limpieza."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Ejecuta los cambios dentro de una transacción (sin esto solo reporta).",
        )

    def handle(self, *args, **options):
        aplicar = options["aplicar"]
        modo = "APLICANDO CAMBIOS" if aplicar else "MODO REPORTE (no se modifica nada; usa --aplicar)"
        self.stdout.write(self.style.MIGRATE_HEADING(f"=== Limpieza de duplicados — {modo} ==="))

        r1 = normalizar_cursos_todos(dry_run=not aplicar)
        self.stdout.write(self.style.HTTP_INFO(f"\n-- Cursos normalizados: {len(r1['cambios'])}"))
        for pk, nombre, apellido, antes, despues in r1["cambios"]:
            self.stdout.write(f"   [{pk}] {nombre} {apellido}: '{antes}' -> '{despues}'")
        if r1["desconocidos"]:
            self.stdout.write(self.style.WARNING(f"   Cursos NO reconocidos (corregir a mano): {r1['desconocidos']}"))

        informe = fusionar_alumnos(dry_run=not aplicar)
        self.stdout.write(self.style.HTTP_INFO(f"\n-- Alumnos duplicados: {len(informe)} grupos"))
        total_borrados = 0
        for g in informe:
            movs = ", ".join(f"{k}:{v}" for k, v in g["movidos"].items() if v)
            perds = ", ".join(str(a.pk) for a in g["perdedores"])
            total_borrados += len(g["perdedores"])
            self.stdout.write(
                f"   Conserva [{g['keeper'].pk}] {g['keeper'].nombre_completo} ({g['keeper'].curso})"
                f" | absorbe [{perds}] año {g['anio']}"
                + (f" | mueve {movs}" if movs else "")
            )
        if total_borrados:
            self.stdout.write(f"   Alumnos a eliminar: {total_borrados}")

        informe2, pendientes = fusionar_alumnos_por_subset(dry_run=not aplicar)
        self.stdout.write(self.style.HTTP_INFO(
            f"\n-- Fusión de alumnos cortos -> nombre completo (mismo curso): {len(informe2)} grupos"
        ))
        total_borrados2 = 0
        for g in informe2:
            perds = ", ".join(str(a.pk) for a in g["perdedores"])
            movs = ", ".join(f"{k}:{v}" for k, v in g["movidos"].items() if v)
            total_borrados2 += len(g["perdedores"])
            self.stdout.write(
                f"   Conserva [{g['keeper'].pk}] {g['keeper'].nombre_completo} ({g['keeper'].curso})"
                f" | absorbe [{perds}] año {g['anio']}"
                + (f" | mueve {movs}" if movs else "")
            )
        if total_borrados2:
            self.stdout.write(f"   Alumnos cortos a eliminar: {total_borrados2}")
        if pendientes:
            self.stdout.write(self.style.WARNING(
                f"   Cortos SIN canónico de su mismo curso (cross-course, revisar a mano): "
                f"{len(pendientes)} -> {pendientes}"
            ))

        r3 = eliminar_registros_repetidos(dry_run=not aplicar)

        auto5, manual5 = fusionar_alumnos_fuzzy(dry_run=not aplicar)
        self.stdout.write(self.style.HTTP_INFO(
            f"\n-- Fusión fuzzy por similitud (typos/variantes, mismo curso): {len(auto5)} grupos"
        ))
        total_borrados5 = 0
        for g in auto5:
            perds = ", ".join(str(a.pk) for a in g["perdedores"])
            movs = ", ".join(f"{k}:{v}" for k, v in g["movidos"].items() if v)
            total_borrados5 += len(g["perdedores"])
            self.stdout.write(
                f"   Conserva [{g['keeper'].pk}] {g['keeper'].nombre_completo} ({g['keeper'].curso})"
                f" | absorbe [{perds}] año {g['anio']}"
                + (f" | mueve {movs}" if movs else "")
            )
        if total_borrados5:
            self.stdout.write(f"   Alumnos fuzzy a eliminar: {total_borrados5}")
        if manual5:
            self.stdout.write(self.style.WARNING(
                f"   Grupos para REVISIÓN MANUAL (género o igual cantidad de tokens): {len(manual5)}"
            ))
            for g in manual5:
                self.stdout.write(
                    "   " + " | ".join(f"[{a.pk}] {a.nombre_completo} ({a.curso})" for a in g)
                )

        self.stdout.write(self.style.HTTP_INFO("\n-- Registros idénticos repetidos:"))
        for fila in r3:
            self.stdout.write(f"   {fila['modelo']}: {fila['grupos']} grupos, {fila['borrados']} filas sobrantes")

        if not aplicar and (r1["cambios"] or informe or any(f["borrados"] for f in r3)):
            self.stdout.write(self.style.NOTICE("\nRevisa el reporte y ejecuta de nuevo con --aplicar para limpiar."))
        elif aplicar:
            self.stdout.write(self.style.SUCCESS("\nLimpieza aplicada correctamente."))
