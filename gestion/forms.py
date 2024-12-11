from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Bibliotecario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Bibliotecario
        fields = ('username', 'rut', 'password1', 'password2')

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        return rut
