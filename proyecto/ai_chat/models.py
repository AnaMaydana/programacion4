from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class ChatSession(models.Model):
    user = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def title(self):
        first_msg = self.message.filter(sender__in=['User', 'Usuario']).first()
        if first_msg:
            txt = first_msg.message.strip().replace('\n', ' ')
            return (txt[:35] + '...') if len(txt) > 35 else txt
        return f"Conversación #{self.id}"


class Message(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='message')
    sender = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    descripcion = models.TextField(blank=True, default='', verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código único")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del producto")
    descripcion = models.TextField(blank=True, default='', verbose_name="Descripción general")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', verbose_name="Categoría")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (Bs.)")
    stock = models.IntegerField(default=0, verbose_name="Cantidad disponible")
    stock_minimo = models.IntegerField(default=5, verbose_name="Nivel mínimo permitido")
    unidad_medida = models.CharField(max_length=50, default='Unidad', verbose_name="Unidad de medida")
    estado = models.BooleanField(default=True, verbose_name="Estado del producto (Activo/Inactivo)")
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) - Bs. {self.precio}"

    def clean(self):
        if self.precio is not None and self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo.'})
        if self.stock is not None and self.stock < 0:
            raise ValidationError({'stock': 'La cantidad existente no puede ser negativa.'})
        if self.stock_minimo is not None and self.stock_minimo < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def cantidad_existente(self):
        return self.stock

    @cantidad_existente.setter
    def cantidad_existente(self, val):
        self.stock = val

    @property
    def estado_stock(self):
        if self.stock <= 0:
            return 'agotado'
        elif self.stock <= self.stock_minimo:
            return 'critico'
        return 'optimo'


class ConsultaIA(models.Model):
    """
    Entidad opcional/recomendada en la especificación RF-10
    para registrar el historial de consultas y respuestas generadas por Ollama.
    """
    pregunta = models.TextField(verbose_name="Pregunta escrita por el usuario")
    respuesta = models.TextField(verbose_name="Respuesta generada por Ollama")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora de la consulta")
    usuario = models.CharField(max_length=100, default='Usuario', verbose_name="Usuario que realizó la consulta")

    class Meta:
        verbose_name = "Consulta IA"
        verbose_name_plural = "Historial de Consultas IA"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y %H:%M')} | {self.usuario}: {self.pregunta[:35]}"
