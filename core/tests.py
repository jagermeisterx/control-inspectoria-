from datetime import date, time

from django.test import TestCase

from .comparativo_generator import obtener_datos_comparativo
from .models import Alumno, Atraso, Celular, ControlUniforme


class ComparativoCursosTests(TestCase):
    """Regresiones del cuadro comparativo de faltas por curso."""

    def setUp(self):
        self.ana = Alumno.objects.create(nombre="ANA", apellido="PEREZ", curso="1° BÁSICO")
        self.beto = Alumno.objects.create(nombre="BETO", apellido="SOTO", curso="1° BÁSICO")
        self.carla = Alumno.objects.create(nombre="CARLA", apellido="DIAZ", curso="1° BÁSICO")
        self.diego = Alumno.objects.create(nombre="DIEGO", apellido="ROJAS", curso="2° BÁSICO")
        self.inactiva = Alumno.objects.create(
            nombre="ELENA", apellido="MUÑOZ", curso="1° BÁSICO", activo=False
        )

        # 1° BÁSICO: 2 atrasos válidos (uno de Ana es CAMPO y no cuenta).
        self._atraso(self.ana, motivo="ATRASO")
        self._atraso(self.ana, motivo="CAMPO")
        self._atraso(self.beto)
        # 2° BÁSICO: 1 atraso.
        self._atraso(self.diego)
        # Alumno inactivo: no debe contabilizarse.
        self._atraso(self.inactiva)

        ControlUniforme.objects.create(
            alumno=self.carla, fecha=date(2026, 8, 12), falta="SIN UNIFORME"
        )
        Celular.objects.create(
            alumno=self.diego, fecha=date(2026, 8, 12), lugar_entregado="DIRECCIÓN"
        )

    def _atraso(self, alumno, motivo="ATRASO"):
        Atraso.objects.create(
            alumno=alumno,
            fecha=date(2026, 8, 10),
            hora=time(8, 0),
            tipo="LLEGADA",
            motivo=motivo,
        )

    def test_una_fila_por_curso_y_totales_reales(self):
        datos = obtener_datos_comparativo(mes=8, anio=2026)

        # Antes del fix, Meta.ordering de Alumno hacía que .distinct() devolviera
        # una fila por alumno y todos los totales se multiplicaran.
        self.assertEqual(len(datos["filas"]), 2)
        self.assertEqual(
            len({f["curso"] for f in datos["filas"]}), len(datos["filas"])
        )

        filas = {f["curso"]: f for f in datos["filas"]}
        primero = filas["1° BÁSICO"]
        self.assertEqual(primero["atrasos"], 2)
        self.assertEqual(primero["uniformes"], 1)
        self.assertEqual(primero["celulares"], 0)
        self.assertEqual(primero["total"], 3)

        segundo = filas["2° BÁSICO"]
        self.assertEqual(segundo["atrasos"], 1)
        self.assertEqual(segundo["uniformes"], 0)
        self.assertEqual(segundo["celulares"], 1)
        self.assertEqual(segundo["total"], 2)

        self.assertEqual(datos["totales"], {
            "cursos": 2,
            "atrasos": 3,
            "uniformes": 1,
            "celulares": 1,
            "total": 5,
        })

    def test_excluye_alumnos_inactivos_y_motivo_campo(self):
        datos = obtener_datos_comparativo(mes=8, anio=2026)
        self.assertEqual(datos["totales"]["atrasos"], 3)

    def test_periodo_sin_registros_devuelve_vacio(self):
        datos = obtener_datos_comparativo(mes=9, anio=2026)
        self.assertEqual(datos["filas"], [])
        self.assertEqual(datos["totales"]["total"], 0)
