from django.contrib import admin
from .models import Alumno, Retiro, Atraso, ControlUniforme, Celular, VisitaApoderado

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ["apellido", "nombre", "curso", "rut", "apoderado_nombre", "activo"]
    list_filter = ["curso", "activo", "anio"]
    search_fields = ["nombre", "apellido", "rut"]

@admin.register(Retiro)
class RetiroAdmin(admin.ModelAdmin):
    list_display = ["alumno", "fecha", "hora", "motivo", "persona_retira"]
    list_filter = ["motivo", "fecha"]
    search_fields = ["alumno__nombre", "alumno__apellido"]

@admin.register(Atraso)
class AtrasoAdmin(admin.ModelAdmin):
    list_display = ["alumno", "fecha", "hora", "tipo"]
    list_filter = ["tipo", "fecha"]

@admin.register(ControlUniforme)
class ControlUniformeAdmin(admin.ModelAdmin):
    list_display = ["alumno", "fecha", "falta", "tiene_uniforme_comprado", "llamado"]
    list_filter = ["falta", "fecha"]

@admin.register(Celular)
class CelularAdmin(admin.ModelAdmin):
    list_display = ["alumno", "fecha", "lugar_entregado", "retiro", "aviso_apoderado"]
    list_filter = ["fecha", "retiro"]

@admin.register(VisitaApoderado)
class VisitaApoderadoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "destino", "funcionario", "hora"]
    list_filter = ["destino", "fecha"]
