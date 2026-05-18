from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("retiros/", views.retiros, name="retiros"),
    path("atrasos/", views.atrasos, name="atrasos"),
    path("uniformes/", views.uniformes, name="uniformes"),
    path("celulares/", views.celulares, name="celulares"),
    path("visitas/", views.visitas, name="visitas"),
    path("alumnos/", views.alumnos, name="alumnos"),
    path("alumnos/importar/", views.importar_alumnos, name="importar_alumnos"),
    path("alumnos/cargar-historico/", views.cargar_historico, name="cargar_historico"),
    path("eliminar/<str:modelo>/<int:pk>/", views.eliminar_registro, name="eliminar_registro"),
    # Reportes
    path("reportes/", views.reportes, name="reportes"),
    path("reportes/alumno/<int:pk>/", views.reporte_alumno, name="reporte_alumno"),
    path("reportes/curso/<str:curso>/", views.reporte_curso, name="reporte_curso"),
    # Exportaciones
    path("exportar/pdf/alumno/<int:pk>/", views.exportar_pdf_alumno, name="exportar_pdf_alumno"),
    path("exportar/pdf/curso/<str:curso>/", views.exportar_pdf_curso, name="exportar_pdf_curso"),
    path("exportar/pdf/todos-cursos/", views.exportar_pdf_todos_cursos, name="exportar_pdf_todos_cursos"),
    path("exportar/excel/alumno/<int:pk>/", views.exportar_excel_alumno, name="exportar_excel_alumno"),
    path("exportar/excel/curso/<str:curso>/", views.exportar_excel_curso, name="exportar_excel_curso"),
    # API
    path("api/alumnos/", views.api_buscar_alumnos, name="api_buscar_alumnos"),
]
