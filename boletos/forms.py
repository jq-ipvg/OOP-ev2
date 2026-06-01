from django import forms
from .models import Bus


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
