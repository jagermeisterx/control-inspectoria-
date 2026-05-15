from django import forms
from .models import Alumno, Retiro, Atraso, ControlUniforme, Celular, VisitaApoderado


class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ["nombre", "apellido", "curso", "rut", "apoderado_nombre", "apoderado_telefono", "apoderado_rut"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
            "apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
            "curso": forms.Select(attrs={"class": "form-select"}),
            "rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "apoderado_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apoderado_telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "9XXXXXXXX"}),
            "apoderado_rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
        }

    def clean_nombre(self):
        return self.cleaned_data["nombre"].upper().strip()

    def clean_apellido(self):
        return self.cleaned_data["apellido"].upper().strip()


class RetiroForm(forms.ModelForm):
    class Meta:
        model = Retiro
        fields = ["alumno", "fecha", "hora", "motivo", "persona_retira", "rut_retira", "observacion"]
        widgets = {
            "alumno": forms.Select(attrs={"class": "form-select select-alumno"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "motivo": forms.Select(attrs={"class": "form-select"}),
            "persona_retira": forms.TextInput(attrs={"class": "form-control"}),
            "rut_retira": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class AtrasoForm(forms.ModelForm):
    class Meta:
        model = Atraso
        fields = ["alumno", "fecha", "hora", "tipo", "lugar", "observacion"]
        widgets = {
            "alumno": forms.Select(attrs={"class": "form-select select-alumno"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "lugar": forms.TextInput(attrs={"class": "form-control", "placeholder": "Casa, etc."}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class ControlUniformeForm(forms.ModelForm):
    class Meta:
        model = ControlUniforme
        fields = ["alumno", "fecha", "falta", "tiene_uniforme_comprado", "detalle", "contacto_apoderado", "llamado", "determinacion"]
        widgets = {
            "alumno": forms.Select(attrs={"class": "form-select select-alumno"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "falta": forms.Select(attrs={"class": "form-select"}),
            "tiene_uniforme_comprado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "detalle": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "contacto_apoderado": forms.TextInput(attrs={"class": "form-control"}),
            "llamado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "determinacion": forms.TextInput(attrs={"class": "form-control"}),
        }


class CelularForm(forms.ModelForm):
    class Meta:
        model = Celular
        fields = ["alumno", "fecha", "lugar_entregado", "retiro", "aviso_apoderado", "observacion"]
        widgets = {
            "alumno": forms.Select(attrs={"class": "form-select select-alumno"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "lugar_entregado": forms.Select(attrs={"class": "form-select"}),
            "retiro": forms.Select(attrs={"class": "form-select"}),
            "aviso_apoderado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VisitaApoderadoForm(forms.ModelForm):
    class Meta:
        model = VisitaApoderado
        fields = ["fecha", "hora", "destino", "funcionario", "observacion"]
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "destino": forms.Select(attrs={"class": "form-select"}),
            "funcionario": forms.TextInput(attrs={"class": "form-control"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class ImportAlumnosForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel (.xlsx)",
        help_text="El archivo debe tener columnas: nombre, apellido, curso, rut (opcional), apoderado_nombre (opcional), apoderado_telefono (opcional)",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".xlsx"}),
    )
