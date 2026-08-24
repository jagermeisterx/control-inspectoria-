from django.db import models
from django.conf import settings

CURSOS = [
    ("PRE-KINDER", "Pre-Kinder"),
    ("KINDER", "Kinder"),
    ("1° BÁSICO", "1° Básico"),
    ("2° BÁSICO", "2° Básico"),
    ("3° BÁSICO", "3° Básico"),
    ("4° BÁSICO", "4° Básico"),
    ("5° BÁSICO", "5° Básico"),
    ("6° BÁSICO", "6° Básico"),
    ("7° BÁSICO", "7° Básico"),
    ("8° BÁSICO", "8° Básico"),
    ("I° MEDIO", "I° Medio"),
    ("II° MEDIO", "II° Medio"),
    ("III° MEDIO", "III° Medio"),
    ("IV° MEDIO", "IV° Medio"),
]


class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    curso = models.CharField(max_length=20, choices=CURSOS)
    rut = models.CharField("RUT", max_length=12, blank=True)
    apoderado_nombre = models.CharField("Nombre apoderado", max_length=200, blank=True)
    apoderado_telefono = models.CharField("Teléfono apoderado", max_length=15, blank=True)
    apoderado_rut = models.CharField("RUT apoderado", max_length=12, blank=True)
    es_campo = models.BooleanField("Campo", default=False)
    activo = models.BooleanField(default=True)
    anio = models.PositiveIntegerField("Año escolar", default=2026)

    class Meta:
        ordering = ["apellido", "nombre"]
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        indexes = [
            models.Index(fields=["nombre", "apellido", "anio"], name="alumno_busqueda_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "apellido", "anio"], name="alumno_unico_nombre_anio"),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def etiqueta_campo(self):
        return "Campo" if self.es_campo else ""


class Retiro(models.Model):
    MOTIVOS = [
        ("ENFERMO/A", "Enfermo/a"),
        ("CONTROL MÉDICO", "Control médico"),
        ("PERSONAL", "Personal"),
        ("TRÁMITES", "Trámites"),
        ("ACC. ESCOLAR", "Accidente escolar"),
        ("LOCOMOCIÓN", "Locomoción"),
        ("FAMILIAR", "Familiar"),
        ("PERIODO ADAPTACIÓN", "Periodo adaptación"),
        ("DEPORTE", "Deporte"),
        ("ENTRENAMIENTO", "Entrenamiento"),
        ("ALMUERZO", "Almuerzo"),
        ("VIAJE", "Viaje"),
        ("TERAPIA", "Terapia"),
        ("KINESIÓLOGO", "Kinesiólogo"),
        ("OTRO", "Otro"),
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="retiros")
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.CharField(max_length=30, choices=MOTIVOS)
    persona_retira = models.CharField("Persona que retira", max_length=200)
    rut_retira = models.CharField("RUT persona que retira", max_length=12, blank=True)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-hora"]
        verbose_name = "Retiro"
        verbose_name_plural = "Retiros"

    def __str__(self):
        return f"{self.alumno} - {self.fecha} {self.motivo}"


class Atraso(models.Model):
    TIPOS = [
        ("LLEGADA", "Llegada"),
        ("RECREO", "Recreo"),
        ("ALMUERZO", "Almuerzo"),
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="atrasos")
    fecha = models.DateField()
    hora = models.TimeField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default="LLEGADA")
    motivo = models.CharField("Motivo", max_length=50, default="ATRASO", blank=True)
    lugar = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-hora"]
        verbose_name = "Atraso"
        verbose_name_plural = "Atrasos"

    def __str__(self):
        return f"{self.alumno} - {self.fecha} {self.tipo}"


class ControlUniforme(models.Model):
    FALTAS = [
        ("SIN UNIFORME", "Sin uniforme"),
        ("SIN POLERÓN", "Sin polerón"),
        ("SIN POLERA NI POLERÓN", "Sin polera ni polerón"),
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="uniformes")
    fecha = models.DateField()
    falta = models.CharField(max_length=30, choices=FALTAS)
    tiene_uniforme_comprado = models.BooleanField("¿Tiene uniforme comprado?", default=True)
    detalle = models.TextField(blank=True)
    contacto_apoderado = models.CharField("Teléfono contacto", max_length=15, blank=True)
    llamado = models.BooleanField("¿Se llamó?", default=False)
    determinacion = models.CharField("Determinación", max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Control de uniforme"
        verbose_name_plural = "Control de uniformes"

    def __str__(self):
        return f"{self.alumno} - {self.fecha} {self.falta}"


class Celular(models.Model):
    LUGARES = [
        ("DIRECCIÓN", "Dirección"),
        ("INSPECTORÍA 1ER PISO", "Inspectoría 1er piso"),
        ("INSPECTORÍA 2DO PISO", "Inspectoría 2do piso"),
    ]
    RETIRO_CHOICES = [
        ("AL FINAL DEL DÍA", "Al final del día"),
        ("RETIRA APODERADO", "Retira apoderado"),
        ("PENDIENTE", "Pendiente"),
    ]

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="celulares")
    fecha = models.DateField()
    lugar_entregado = models.CharField("Lugar de entrega", max_length=30, choices=LUGARES)
    retiro = models.CharField(max_length=20, choices=RETIRO_CHOICES, default="AL FINAL DEL DÍA")
    aviso_apoderado = models.BooleanField("¿Aviso a apoderado?", default=False)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Celular requisado"
        verbose_name_plural = "Celulares requisados"

    def __str__(self):
        return f"{self.alumno} - {self.fecha}"


class VisitaApoderado(models.Model):
    DESTINOS = [
        ("INSPECTORÍA GENERAL", "Inspectoría General"),
        ("PIE", "PIE"),
        ("UTP", "UTP"),
        ("PROFESOR/A", "Profesor/a"),
        ("CONV. ESCOLAR", "Convivencia Escolar"),
        ("DIRECCIÓN", "Dirección"),
    ]

    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    destino = models.CharField(max_length=30, choices=DESTINOS)
    funcionario = models.CharField(max_length=200)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-hora"]
        verbose_name = "Visita de apoderado"
        verbose_name_plural = "Visitas de apoderados"

    def __str__(self):
        return f"{self.destino} - {self.funcionario} ({self.fecha})"


class LlamadaApoderado(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="llamadas")
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    detalle = models.TextField("Detalle de la llamada")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-hora"]
        verbose_name = "Llamada a apoderado"
        verbose_name_plural = "Llamadas a apoderados"

    def __str__(self):
        return f"{self.alumno} - {self.fecha} {self.detalle[:50]}"
