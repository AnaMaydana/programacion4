"""
Patrón de Diseño: OBSERVER
Este módulo implementa el patrón Observer mediante el mecanismo nativo de Señales (Signals) de Django.
Observa los cambios de estado y existencias en el modelo Producto y emite eventos/alertas
cuando el stock alcanza niveles críticos o agotados.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producto

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Producto)
def observador_cambio_stock(sender, instance, created, **kwargs):
    """
    Observer que reacciona a la creación o actualización de un producto.
    Si el stock es crítico o agotado, genera una alerta del sistema.
    """
    if created:
        logger.info(f"[OBSERVER: PRODUCTO CREADO] {instance.nombre} ({instance.codigo}) con {instance.stock} {instance.unidad_medida}.")
    else:
        if instance.stock <= 0:
            logger.warning(f"[OBSERVER: ALERTA ROJA - AGOTADO] El producto '{instance.nombre}' ({instance.codigo}) se ha agotado por completo (Stock: 0).")
        elif instance.stock <= instance.stock_minimo:
            logger.warning(f"[OBSERVER: ALERTA AMARILLA - STOCK CRÍTICO] El producto '{instance.nombre}' ({instance.codigo}) tiene stock bajo: {instance.stock} (Mínimo: {instance.stock_minimo}).")
        else:
            logger.info(f"[OBSERVER: STOCK ACTUALIZADO] '{instance.nombre}' actualizado con éxito. Stock: {instance.stock}.")
