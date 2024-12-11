from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class Bibliotecario(AbstractUser):
    rut = models.CharField(max_length=12, unique=True) 

class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100)
    estado = models.BooleanField(default=True) 
    copias_disponibles = models.PositiveIntegerField(default=1) 

    def __str__(self):
        return self.titulo

class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField(auto_now_add=True)  
    fecha_devolucion = models.DateTimeField(default=timezone.now)  
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    multa_pagada = models.BooleanField(default=False)
    usuario = models.ForeignKey(Bibliotecario, on_delete=models.CASCADE, null=True)

    def calcular_multa(self):
        if self.fecha_devolucion < timezone.now():  
            dias_retraso = (timezone.now() - self.fecha_devolucion).days
            return dias_retraso * 0.5  
        return 0.00
    
    def __str__(self):
        return f"Préstamo de {self.libro.titulo} - {self.fecha_prestamo}"
    
    def actualizar_multa(self):
        self.multa = self.calcular_multa()
        self.save()
