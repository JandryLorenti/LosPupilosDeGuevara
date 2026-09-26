from django.db import models

# Create your models here.

class Estudiante(models.Model):
    CARRERAS = [
        ('SOF', 'Software'),
        ('ADM', 'Administracion'),
        ('DER', 'Derecho'),
        ('OTR', 'Otra'),  
    ]
    cedula = models.CharField(max_length=10, default='0000000000')
    nombre=models.CharField(max_length=100)
    apellido=models.CharField(max_length=100)
    correo=models.EmailField(unique=True)
    edad=models.PositiveBigIntegerField()
    carrera=models.CharField(max_length=3, choices=CARRERAS)
    fecha_registro=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.nombre} {self.apellido}'