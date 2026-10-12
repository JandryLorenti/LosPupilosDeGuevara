from django.db import models

# 1. Nuevo modelo (tabla) independiente para las Carreras
class Carrera(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre


# 2. Modelo Estudiante modificado
class Estudiante(models.Model):
    cedula = models.CharField(max_length=10, default='')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    edad = models.PositiveBigIntegerField()
    
    # NORMALIZACIÓN: Clave foránea que relaciona al estudiante con una carrera
    # on_delete=models.SET_NULL asegura que si eliminas una carrera del CRUD, 
    # no se borren los estudiantes, simplemente su campo carrera quedará en blanco (null).
    carrera = models.ForeignKey(Carrera, on_delete=models.SET_NULL, null=True, blank=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.nombre} {self.apellido}'