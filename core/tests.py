from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .comparativo_generator import obtener_datos_comparativo
from .escpos_generator import generar_escpos_comunicado, generar_escpos_pase
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


class TicketEscposTests(TestCase):
    """El ticket ESC/POS es la vía principal de impresión en la POS-58."""

    def setUp(self):
        self.alumno = Alumno.objects.create(
            nombre="ANA MARÍA", apellido="MUÑOZ", curso="1° BÁSICO"
        )
        self.atraso = Atraso.objects.create(
            alumno=self.alumno,
            fecha=date(2026, 11, 17),
            hora=time(8, 5),
            tipo="LLEGADA",
            motivo="ATRASO",
            lugar="PORTÓN",
            observacion="LA APODERADA AVISA QUE LLEGA TARDE POR CONTROL MÉDICO",
        )

    def test_pase_empieza_sin_salto_de_linea(self):
        datos = generar_escpos_pase(self.atraso)
        # ESC @ y luego margen/ancho: nada de alimentar papel antes del logo.
        self.assertTrue(datos.startswith(b"\x1b@"))
        self.assertNotIn(b"\x1b@\n", datos[:4])

    def test_fija_margen_izquierdo_y_ancho_de_58_mm(self):
        datos = generar_escpos_pase(self.atraso)
        cabecera = datos[:32]
        self.assertIn(b"\x1dL\x00\x00", cabecera)      # margen izquierdo 0
        self.assertIn(b"\x1dW\x80\x01", cabecera)      # 384 puntos = 48 mm
        self.assertIn(b"\x1bM\x00", cabecera)          # Fuente A (32 columnas)
        self.assertIn(b"\x1b \x00", cabecera)          # espaciado 0

    def test_cada_linea_se_ancla_al_borde_izquierdo(self):
        from .escpos_generator import POS_IZQUIERDA

        datos = generar_escpos_pase(self.atraso)
        # Sin ESC a: el centrado es manual y no depende del firmware.
        self.assertNotIn(b"\x1ba", datos)
        self.assertIn(POS_IZQUIERDA, datos)
        self.assertIn(POS_IZQUIERDA + b"FECHA:", datos)
        self.assertIn(POS_IZQUIERDA + b"NOMBRE ALUMNO:", datos)

    def test_titulo_centrado_con_espacios(self):
        datos = generar_escpos_pase(self.atraso)
        titulo = "AUTORIZACION INGRESO A CLASES"
        self.assertIn(titulo.center(32).encode("cp850"), datos)
        self.assertIn(("-" * 32).encode("cp850"), datos)

    def test_logo_se_posiciona_dentro_de_los_384_puntos(self):
        from .escpos_generator import _ancho_logo, _posicion_logo

        with open("static/img/logo_pase_escpos.bin", "rb") as fh:
            logo = fh.read()
        self.assertEqual(_ancho_logo(logo), 80)
        self.assertEqual(_posicion_logo(logo), b"\x1b$\x98\x00")  # 152 dots

    def test_pase_incluye_campos_y_acentos_en_cp850(self):
        datos = generar_escpos_pase(self.atraso)
        self.assertIn(b"AUTORIZACION INGRESO A CLASES", datos)
        self.assertIn("ANA MARÍA MUÑOZ".encode("cp850"), datos)
        self.assertIn("MÉDICO".encode("cp850"), datos)

    def test_pase_termina_con_avance_y_corte(self):
        datos = generar_escpos_pase(self.atraso)
        self.assertTrue(datos.endswith(b"\x1bd\x04\x1dV\x00"))

    def test_lineas_respetan_las_32_columnas(self):
        from .escpos_generator import _envolver

        lineas = _envolver(
            "LA APODERADA AVISA QUE LLEGA TARDE POR CONTROL MÉDICO EN EL CESFAM",
            max_lineas=5,
        )
        self.assertTrue(lineas)
        self.assertTrue(all(len(linea) <= 32 for linea in lineas))
        self.assertLessEqual(len(lineas), 5)

    def test_comunicado_tambien_se_genera(self):
        uniforme = ControlUniforme.objects.create(
            alumno=self.alumno,
            fecha=date(2026, 11, 17),
            falta="SIN UNIFORME",
            detalle="SIN POLERÓN",
        )
        datos = generar_escpos_comunicado(uniforme)
        self.assertIn(b"COMUNICACION FALTA DE UNIFORME", datos)
        self.assertIn("SIN POLERÓN".encode("cp850"), datos)

    def test_ficha_pdf_usa_bobina_de_58_mm(self):
        from .pase_generator import ANCHO_MM, generar_pdf_ficha

        self.assertEqual(ANCHO_MM, 58)
        pdf = generar_pdf_ficha("TITULO", [{"rotulo": "CAMPO:", "valor": "VALOR"}]).getvalue()
        self.assertIn(b"/MediaBox", pdf)
        self.assertIn(b"164.409", pdf)  # 58 mm en puntos (58 / 25.4 * 72)


class ImpresionViewsTests(TestCase):
    """Las vistas de impresión exponen el ticket y el HTML de respaldo."""

    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.cl", "clave")
        self.client.force_login(self.user)
        self.alumno = Alumno.objects.create(
            nombre="ANA", apellido="MUÑOZ", curso="1° BÁSICO"
        )
        self.atraso = Atraso.objects.create(
            alumno=self.alumno,
            fecha=date(2026, 11, 17),
            hora=time(8, 5),
            tipo="LLEGADA",
            motivo="ATRASO",
        )
        self.uniforme = ControlUniforme.objects.create(
            alumno=self.alumno,
            fecha=date(2026, 11, 17),
            falta="SIN UNIFORME",
        )

    def test_pase_ui_ofrece_el_endpoint_escpos(self):
        resp = self.client.get(reverse("imprimir_pase_ui", args=[self.atraso.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("escpos_pase", args=[self.atraso.pk]))
        self.assertContains(resp, "http://127.0.0.1:9110")

    def test_escpos_pase_devuelve_bytes_crudos(self):
        resp = self.client.get(reverse("escpos_pase", args=[self.atraso.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/octet-stream")
        self.assertTrue(resp.content.startswith(b"\x1b@"))

    def test_comunicado_ui_y_escpos(self):
        resp = self.client.get(
            reverse("imprimir_comunicado_uniforme_ui", args=[self.uniforme.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("escpos_comunicado_uniforme", args=[self.uniforme.pk]))

        resp = self.client.get(
            reverse("escpos_comunicado_uniforme", args=[self.uniforme.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"COMUNICACION FALTA DE UNIFORME", resp.content)
