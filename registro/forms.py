from django import forms
from .models import Estudiante

class EstudianteForm(forms.ModelForm):
    class Meta:
        model=Estudiante
        fields=['nombre', 'apellido', 'correo', 'edad', 'carrera',"cedula"]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Rodrigo Josue'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej. Guevara Reyes'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'estudiante@gmail.com'}),
            'edad': forms.NumberInput(attrs={'placeholder': 'Ej. 19'}),
            'cedula': forms.TextInput(attrs={'placeholder': 'Ej. 0912345678'}),
        }
        # fields=['nombre', 'apellido', 'correo', 'edad', 'carrera', 'comentarios','cedula']
        # widgets={
        #     'comentarios': forms.Textarea(attrs={'rows':3}),
        # }
    
    def clean_edad(self):
        edad=self.cleaned_data['edad']
        if edad<16 or edad>100:
            raise forms.ValidationError('Debes tener al menos 16 años y no más de 100.')
        return edad