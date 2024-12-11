from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from .models import Libro, Prestamo
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _ 
from django.contrib import messages
from django.db import models 
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .forms import RegistroForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.utils.timezone import make_aware
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required
def lista_libros(request):
    query = request.GET.get('q')
    libros = Libro.objects.filter(titulo__icontains=query) if query else Libro.objects.all()
    return render(request, 'gestion/lista_libros.html', {'libros': libros, 'query': query})

CATEGORIAS_VALIDAS = [
    'ficción', 'terror', 'clásico', 'superhéroes', 
    'documental', 'manual', 'historieta', 'manga', 'biografía'
]

@login_required
def agregar_libro(request):
    if request.method == 'POST':
        titulo = request.POST['titulo']
        autor = request.POST['autor']
        categoria = request.POST['categoria'].strip().lower()  
        ubicacion = request.POST['ubicacion']

        if not all([titulo, autor, categoria, ubicacion]):
            messages.error(request, _('Todos los campos son obligatorios.'))
            return render(request, 'gestion/agregar_libro.html')

        if categoria not in CATEGORIAS_VALIDAS:
            messages.error(request, _('La categoría "{}" no está disponible.').format(categoria))
            return render(request, 'gestion/agregar_libro.html')

        if Libro.objects.filter(titulo=titulo).exists():
            messages.error(request, _('El libro "{}" ya existe en la base de datos.').format(titulo))
            return render(request, 'gestion/agregar_libro.html')

        Libro.objects.create(titulo=titulo, autor=autor, categoria=categoria, ubicacion=ubicacion)
        messages.success(request, _('Libro agregado correctamente.'))
        return redirect('lista_libros')

    return render(request, 'gestion/agregar_libro.html')

def home(request):
    return redirect('login_usuario')

@login_required
def lista_prestamos(request):
    prestamos = Prestamo.objects.all()
    return render(request, 'gestion/lista_prestamos.html', {'prestamos': prestamos})

@login_required
def agregar_prestamo(request):
    if request.method == 'POST':
        libro_id = request.POST['libro_id']
        fecha_devolucion = parse_datetime(request.POST['fecha_devolucion'])
        libro = get_object_or_404(Libro, id=libro_id, estado=True)

        if fecha_devolucion is not None:
            fecha_devolucion = make_aware(fecha_devolucion)

        if fecha_devolucion <= timezone.now():
            messages.error(request, _('La fecha de devolución debe ser en el futuro.'))
            return redirect('agregar_prestamo')

        Prestamo.objects.create(libro=libro, fecha_devolucion=fecha_devolucion)
        libro.estado = False 
        libro.save()
        
        messages.success(request, _('Préstamo agregado correctamente.'))
        return redirect('lista_prestamos')

    libros = Libro.objects.filter(estado=True)
    return render(request, 'gestion/agregar_prestamo.html', {'libros': libros})

@login_required
def devolver_prestamo(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    prestamo.fecha_devolucion = timezone.now()
    prestamo.multa = prestamo.calcular_multa()  
    if prestamo.multa > 0:
        messages.warning(request, 'El libro fue devuelto tarde. Se generó una multa de ${}.'.format(prestamo.multa))
    prestamo.save()
    libro = prestamo.libro  
    libro.estado = True  
    libro.save()  
    prestamo.delete()  
    
    messages.success(request, 'La devolución se ha registrado correctamente.')
    return redirect('lista_prestamos')

def calcular_multa(self):
    if self.fecha_devolucion < timezone.now(): 
        dias_retraso = (timezone.now() - self.fecha_devolucion).days
        return dias_retraso * 0.5  
    return 0.00

def __str__(self):
        return f"Préstamo de {self.libro.titulo} - {self.fecha_prestamo}"

@login_required
def pagar_multa(request):
    if request.method == 'POST':
        prestamo_id = request.POST.get('prestamo_id')

        if not prestamo_id:
            messages.error(request, _('El ID de préstamo no es válido.'))
            return redirect('lista_prestamos')
        try:
            prestamo = Prestamo.objects.get(id=prestamo_id)
        except Prestamo.DoesNotExist:
            messages.error(request, _('El préstamo seleccionado no existe.'))
            return redirect('lista_prestamos')

        prestamo.multa_pagada = True
        prestamo.save()
        messages.success(request, _('La multa ha sido pagada correctamente.'))
        return redirect('lista_prestamos')  
    
    prestamos = Prestamo.objects.filter(multa_pagada=False)
    return render(request, 'gestion/pagar_multa.html', {'prestamos': prestamos})

@login_required
def editar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    if request.method == 'POST':
        libro.titulo = request.POST['titulo']
        libro.autor = request.POST['autor']
        libro.categoria = request.POST['categoria']
        libro.ubicacion = request.POST['ubicacion']
        libro.save()
        messages.success(request, 'Libro actualizado correctamente.')
        return redirect('lista_libros')
    return render(request, 'gestion/editar_libro.html', {'libro': libro})

@login_required
def eliminar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)
    libro.delete()
    messages.success(request, 'Libro eliminado correctamente.')
    return redirect('lista_libros')

@login_required
def reportes(request):

    prestamos = Prestamo.objects.all()

    if request.GET.get('descargar') == 'pdf':
        return generar_pdf(request)  

    return render(request, 'gestion/reportes.html', {
        'prestamos': prestamos,
    })

@login_required
def generar_pdf(request):
    prestamos = Prestamo.objects.all()  
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestamos.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.drawString(100, height - 100, "Reporte de Préstamos")
    
    y_position = height - 130
    
    p.drawString(100, y_position, "ID")
    p.drawString(200, y_position, "Título")
    p.drawString(300, y_position, "Usuario")
    p.drawString(400, y_position, "Préstamo")
    p.drawString(500, y_position, "Devolución")

    y_position -= 20  
    for prestamo in prestamos:
        p.drawString(100, y_position, str(prestamo.id))
        p.drawString(200, y_position, prestamo.libro.titulo)

        if prestamo.usuario:
            p.drawString(300, y_position, prestamo.usuario.username)
        else:
            p.drawString(300, y_position, "Sin usuario") 
        
        p.drawString(400, y_position, str(prestamo.fecha_prestamo))
        p.drawString(500, y_position, str(prestamo.fecha_devolucion))
        y_position -= 20 

    p.showPage()
    p.save()
    
    return response

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = RegistroForm()
    return render(request, 'gestion/registro.html', {'form': form})

def login_usuario(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('lista_libros') 
        else:
            messages.error(request, _('Usuario no válido. Verifica tus credenciales e inténtalo nuevamente.'))
            return render(request, 'gestion/login.html')
    return render(request, 'gestion/login.html')

@login_required
def logout_usuario(request):
    logout(request)  
    return redirect('login') 