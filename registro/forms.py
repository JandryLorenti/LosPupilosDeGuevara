from django import forms
from .models import Estudiante

class EstudianteForm(forms.ModelForm):
    class Meta:
        model=Estudiante
        fields=['nombre', 'apellido', 'correo', 'edad', 'carrera',"cedula"]

        # fields=['nombre', 'apellido', 'correo', 'edad', 'carrera', 'comentarios','cedula']
        # widgets={
        #     'comentarios': forms.Textarea(attrs={'rows':3}),
        # }
    
    def clean_edad(self):
        edad=self.cleaned_data['edad']
        if edad<16:
            raise forms.ValidationError('Debes tener al menos 16 años.')
        return edad