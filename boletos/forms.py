from django import forms
from .models import Bus, Ruta, Itinerario


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['nombre', 'placa', 'pisos', 'asientos_piso_1', 'asientos_piso_2']
        widgets = {
            'asientos_piso_1': forms.NumberInput(attrs={'min': 1, 'max': 45}),
            'asientos_piso_2': forms.NumberInput(attrs={'min': 0, 'max': 45}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asientos_piso_2'].required = False

    def clean_asientos_piso_1(self):
        val = self.cleaned_data['asientos_piso_1']
        if val > 45:
            raise forms.ValidationError('Máximo 45 asientos por piso.')
        return val

    def clean_asientos_piso_2(self):
        val = self.cleaned_data.get('asientos_piso_2', 0) or 0
        if val > 45:
            raise forms.ValidationError('Máximo 45 asientos por piso.')
        return val


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['origen', 'destino', 'duracion_minutos']
        widgets = {
            'duracion_minutos': forms.NumberInput(attrs={'min': 10}),
        }

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get('origen')
        destino = cleaned.get('destino')
        if origen and destino and origen == destino:
            raise forms.ValidationError('El origen y destino no pueden ser iguales.')
        return cleaned


class ItinerarioForm(forms.ModelForm):
    class Meta:
        model = Itinerario
        fields = ['bus', 'ruta', 'hora_salida', 'tipo', 'fecha_especifica']
        widgets = {
            'hora_salida': forms.TimeInput(attrs={'type': 'time'}),
            'fecha_especifica': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['bus'].queryset = Bus.objects.filter(empresa=self.user)
            self.fields['ruta'].queryset = Ruta.objects.filter(empresa=self.user)

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        fecha = cleaned.get('fecha_especifica')
        if tipo == 'unico' and not fecha:
            raise forms.ValidationError('Debes especificar una fecha para itinerarios únicos.')
        if tipo == 'diario' and fecha:
            cleaned['fecha_especifica'] = None
        return cleaned


class PaymentForm(forms.Form):
    nombre_titular = forms.CharField(max_length=150, label='Nombre del titular')
    numero_tarjeta = forms.CharField(max_length=19, label='Número de tarjeta',
                                     widget=forms.TextInput(attrs={'placeholder': '0000 0000 0000 0000'}))
    fecha_vencimiento = forms.CharField(max_length=5, label='Vencimiento',
                                        widget=forms.TextInput(attrs={'placeholder': 'MM/AA'}))
    cvv = forms.CharField(max_length=3, label='CVV',
                          widget=forms.TextInput(attrs={'placeholder': '123'}))

    def clean_numero_tarjeta(self):
        val = self.cleaned_data['numero_tarjeta'].replace(' ', '')
        if val != '0000000000000000':
            raise forms.ValidationError('Número de tarjeta inválido.')
        return val

    def clean_fecha_vencimiento(self):
        val = self.cleaned_data['fecha_vencimiento'].strip()
        if val != '12/34':
            raise forms.ValidationError('Fecha de vencimiento inválida.')
        return val

    def clean_cvv(self):
        val = self.cleaned_data['cvv'].strip()
        if val != '123':
            raise forms.ValidationError('CVV inválido.')
        return val
