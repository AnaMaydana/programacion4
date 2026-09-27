from django import forms
from django.core.exceptions import ValidationError
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio', 'stock', 'stock_minimo', 'unidad_medida', 'estado']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PROD-001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción detallada (opcional)'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Unidad, Kg, Litro'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise ValidationError('El código del producto es obligatorio.')
        
        # Validar unicidad (excluyendo la instancia actual si es edición)
        query = Producto.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError(f'El código "{codigo}" ya está registrado para otro producto.')
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None or precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is None or stock < 0:
            raise ValidationError('La cantidad existente no puede ser negativa.')
        return stock

    def clean_stock_minimo(self):
        stock_min = self.cleaned_data.get('stock_minimo')
        if stock_min is None or stock_min < 0:
            raise ValidationError('El stock mínimo no puede ser negativo.')
        return stock_min


class AjusteStockForm(forms.Form):
    ACCIONES = (
        ('aumentar', 'Aumentar existencia (+)'),
        ('disminuir', 'Disminuir existencia (-)'),
    )
    accion = forms.ChoiceField(choices=ACCIONES, widget=forms.Select(attrs={'class': 'form-control'}))
    cantidad = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    motivo = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo del ajuste'}))


class ChatPreguntaForm(forms.Form):
    pregunta = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe una consulta sobre el inventario (ej. ¿Cuál es el producto más caro?)...',
            'id': 'chatInput'
        })
    )
