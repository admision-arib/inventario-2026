from django import forms
from django.core.exceptions import ValidationError
from .models import MovimientoBien
from apps.bienes.models import Bien

TAILWIND_INPUT_CLASS = (
    "w-full py-2.5 px-3.5 bg-slate-50 border border-slate-300 text-slate-800 text-xs rounded-xl "
    "focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition duration-200"
)

class TransferenciaForm(forms.ModelForm):
    bien = forms.ModelChoiceField(
        queryset=Bien.objects.none(),
        widget=forms.Select(attrs={
            'id': 'select-bien',
            'class': 'w-full'
        }),
        label="Bien a Transferir"
    )

    class Meta:
        model = MovimientoBien
        fields = [
            'bien',
            'area_destino',
            'usuario_destino',
            'documento_autorizacion',
            'observaciones'
        ]
        widgets = {
            'area_destino': forms.Select(attrs={'class': TAILWIND_INPUT_CLASS}),
            'usuario_destino': forms.Select(attrs={'class': TAILWIND_INPUT_CLASS}),
            'documento_autorizacion': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'placeholder': 'Ej. MEMO N° 045-2026-ADMIN / PAPELETA N° 012'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': TAILWIND_INPUT_CLASS,
                'rows': 3,
                'placeholder': 'Motivo o detalles del traslado...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'bien' in self.data:
            try:
                bien_id = int(self.data.get('bien'))
                self.fields['bien'].queryset = Bien.objects.filter(id=bien_id, activo=True)
            except (ValueError, TypeError):
                pass
        elif self.initial.get('bien'):
            bien_obj = self.initial.get('bien')
            bien_id = bien_obj.id if hasattr(bien_obj, 'id') else bien_obj
            self.fields['bien'].queryset = Bien.objects.filter(id=bien_id, activo=True)

    def clean(self):
        cleaned_data = super().clean()
        bien = cleaned_data.get('bien')

        if bien:
            if not bien.area or not bien.usuario_responsable:
                self.add_error(
                    'bien',
                    f"El bien {bien.codigo_patrimonial} no tiene un Área o Usuario Responsable de origen asignado. "
                    f"Corrija la ficha del bien antes de realizar la transferencia."
                )
        return cleaned_data