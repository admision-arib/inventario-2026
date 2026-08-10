# apps/usuarios/forms.py
from django import forms
from .models import Usuario
from apps.core.models import Area


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': '••••••••'}),
        required=False,
        help_text="Dejar en blanco para mantener la contraseña actual (al crear, si se deja en blanco se asignará el DNI)."
    )

    # Campo de selección múltiple para las áreas asignadas en custodia
    areas_custodia = forms.ModelMultipleChoiceField(
        queryset=Area.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'h-4 w-4 text-blue-600 rounded border-gray-300'}),
        required=False,
        label="Áreas en Custodia / A Su Cargo"
    )

    class Meta:
        model = Usuario
        fields = [
            'username', 'dni', 'first_name', 'last_name', 'email',
            'cargo', 'area', 'rol', 'areas_custodia', 'telefono',
            'is_active', 'is_staff'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'dni': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'maxlength': '8'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'}),
            'cargo': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'area': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'rol': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'h-4 w-4'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dni'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        # Si estamos editando un usuario existente, cargamos sus áreas en custodia previas
        if self.instance and self.instance.pk:
            self.fields['areas_custodia'].initial = self.instance.areas_custodia.all()

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            if not dni.isdigit() or len(dni) != 8:
                raise forms.ValidationError("El DNI debe tener 8 dígitos.")

            instance = getattr(self, 'instance', None)
            if instance and instance.pk:
                if Usuario.objects.filter(dni=dni).exclude(pk=instance.pk).exists():
                    raise forms.ValidationError("Ya existe un usuario con este DNI.")
            else:
                if Usuario.objects.filter(dni=dni).exists():
                    raise forms.ValidationError("Ya existe un usuario con este DNI.")
        return dni

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        # Si es un usuario nuevo y no se ingresó contraseña, asignar su DNI por defecto
        if not user.pk and not password:
            user.set_password(user.dni)
        elif password:
            user.set_password(password)

        if not user.username:
            user.username = user.dni

        if commit:
            user.save()
            # Guardar la relación Muchos a Muchos con las áreas de custodia
            user.areas_custodia.set(self.cleaned_data.get('areas_custodia', []))

        return user