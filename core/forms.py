from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings
from boletos.models import Profile


class ClienteRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=150, required=False, label='Nombre')
    last_name = forms.CharField(max_length=150, required=False, label='Apellido')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class EmpresaRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=150, required=False, label='Nombre')
    last_name = forms.CharField(max_length=150, required=False, label='Apellido')
    empresa_nombre = forms.CharField(max_length=100, label='Nombre de la empresa')
    codigo_verificacion = forms.CharField(max_length=50, label='Código de verificación',
                                          help_text='Ingresa el código proporcionado para registrar una empresa.')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                  'empresa_nombre', 'codigo_verificacion']

    def clean_codigo_verificacion(self):
        codigo = self.cleaned_data['codigo_verificacion']
        if codigo != settings.EMPRESA_REGISTRATION_CODE:
            raise forms.ValidationError('Código de verificación incorrecto.')
        return codigo

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            profile.tipo = 'empresa'
            profile.empresa_nombre = self.cleaned_data['empresa_nombre']
            profile.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False, label='Nombre')
    last_name = forms.CharField(max_length=30, required=False, label='Apellido')
    empresa_nombre = forms.CharField(max_length=100, required=False, label='Nombre de la empresa')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if self.profile:
            self.fields['empresa_nombre'].initial = self.profile.empresa_nombre
            if self.profile.tipo != 'empresa':
                self.fields['empresa_nombre'].widget = forms.HiddenInput()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and self.profile:
            self.profile.empresa_nombre = self.cleaned_data.get('empresa_nombre', '')
            self.profile.save()
        return user
