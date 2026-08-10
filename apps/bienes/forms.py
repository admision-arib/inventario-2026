from django import forms
from .models import Bien


class BienForm(forms.ModelForm):
    class Meta:
        model = Bien
        fields = [
            #'codigo_patrimonial',
            'catalogo_siga', 'denominacion',
            'marca', 'modelo', 'serie', 'color', 'dimensiones',
            'estado_conservacion', 'observaciones',
            'tipo_adquisicion', 'numero_documento', 'valor_inicial',
            'fecha_adquisicion', 'depreciable',
            'sede', 'area', 'usuario_responsable', 'ubicacion_fisica'
        ]
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
            'valor_inicial': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'observaciones': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Detalles técnicos u observaciones adicionales...'}),
            'denominacion': forms.TextInput(attrs={'placeholder': 'Ej. ESCRITORIO DE MADERA CON CAJONES'}),
            #'codigo_patrimonial': forms.TextInput(attrs={'placeholder': 'Ej. 740899500001'}),
            'catalogo_siga': forms.TextInput(attrs={'placeholder': 'Ej. 74089950'}),
            'ubicacion_fisica': forms.TextInput(attrs={'placeholder': 'Ej. Oficina 201 - Segundo Piso'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Clase base estilizada y compacta para inputs normales y selects
        base_class = "w-full px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:bg-white focus:border-indigo-500 outline-none transition"

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs[
                    'class'] = "w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500 cursor-pointer"
            else:
                current_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{base_class} {current_classes}".strip()