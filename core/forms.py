from django import forms
from .models import Alumno, Retiro, Atraso, ControlUniforme, Celular, VisitaApoderado, LlamadaApoderado


class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = ["nombre", "apellido", "curso", "rut", "apoderado_nombre", "apoderado_telefono", "apoderado_rut", "es_campo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
            "apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
            "curso": forms.Select(attrs={"class": "form-select"}),
            "rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "apoderado_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apoderado_telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "9XXXXXXXX"}),
            "apoderado_rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "es_campo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_nombre(self):
        return self.cleaned_data["nombre"].upper().strip()

    def clean_apellido(self):
        return self.cleaned_data["apellido"].upper().strip()


class RetiroForm(forms.ModelForm):
    alumno_texto = forms.CharField(
        label="Alumno/a",
        widget=forms.TextInput(attrs={"class": "form-control ac-input", "placeholder": "Escribir nombre...", "autocomplete": "off"}),
    )

    class Meta:
        model = Retiro
        fields = ["fecha", "hora", "motivo"]
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "motivo": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alumno_texto"].required = True


class AtrasoForm(forms.ModelForm):
    alumno_texto = forms.CharField(
        label="Alumno/a",
        widget=forms.TextInput(attrs={"class": "form-control ac-input", "placeholder": "Escribir nombre...", "autocomplete": "off"}),
    )

    class Meta:
        model = Atraso
        fields = ["fecha", "hora", "tipo", "motivo", "lugar", "observacion"]
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "hora": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "motivo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Motivo del atraso..."}),
            "lugar": forms.TextInput(attrs={"class": "form-control", "placeholder": "Casa, etc."}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class ControlUniformeForm(forms.ModelForm):
    alumno_texto = forms.CharField(
        label="Alumno/a",
        widget=forms.TextInput(attrs={"class": "form-control ac-input", "placeholder": "Escribir nombre...", "autocomplete": "off"}),
    )

    class Meta:
        model = ControlUniforme
        fields = ["fecha", "falta"]
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "falta": forms.Select(attrs={"class": "form-select"}),
        }


class CelularForm(forms.ModelForm):
    alumno_texto = forms.CharField(
        label="Alumno/a",
        widget=forms.TextInput(attrs={"class": "form-control ac-input", "placeholder": "Escribir nombre...", "autocomplete": "off"}),
    )

    class Meta:
        model = Celular
        fields = ["fecha", "lugar_entregado", "retiro", "aviso_apoderado", "observacion"]
        widgets = {
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
        help_text="Columnas: nombre, apellido, curso, rut (opc.), apoderado (opc.), teléfono (opc.)",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".xlsx"}),
    )


class LlamadaApoderadoForm(forms.ModelForm):
    class Meta:
        model = LlamadaApoderado
        fields = ["detalle"]
        widgets = {
            "detalle": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Ej: Se deja constancia, se amonesta, se suspende..."}),
        }
        labels = {
            "detalle": "Detalle de la llamada",
        }
