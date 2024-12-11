from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_libros, name='lista_libros'),
    path('agregar/', views.agregar_libro, name='agregar_libro'),
    path('prestamos/', views.lista_prestamos, name='lista_prestamos'),
    path('prestamos/agregar/', views.agregar_prestamo, name='agregar_prestamo'),
    path('prestamos/devolver/<int:prestamo_id>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('prestamos/pagar/', views.pagar_multa, name='pagar_multa'),
    path('editar/<int:libro_id>/', views.editar_libro, name='editar_libro'),
    path('eliminar/<int:libro_id>/', views.eliminar_libro, name='eliminar_libro'),
    path('reportes/', views.reportes, name='reportes'),
    path('generar-pdf/', views.generar_pdf, name='generar_pdf'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout_usuario')
]