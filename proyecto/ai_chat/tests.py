import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from ai_chat.models import Categoria, Producto, ConsultaIA, ChatSession, Message
from ai_chat.forms import ProductoForm
from ai_chat.services.report_strategies import (
    ReporteContext,
    ProductoMasCaroStrategy,
    ProductoMasBaratoStrategy,
    PocasExistenciasStrategy,
    ProductosAgotadosStrategy,
    ValorTotalInventarioStrategy,
    MayorCantidadStrategy
)
from ai_chat.services.ollama_service import AILocalServiceFactory, OllamaLocalService


class TestProductoCRUDYValidaciones(TestCase):
    """
    Pruebas unitarias para Punto 3.2:
    - Validación de código único (RF-01, RF-03).
    - Validación de valores no negativos (precio, stock, stock_minimo).
    - Borrado lógico (cambio a estado inactivo RF-04).
    - Control de existencias e impedimento de stock negativo (RF-05).
    """
    def setUp(self):
        self.client = Client()
        self.categoria = Categoria.objects.create(
            nombre='Lácteos',
            descripcion='Productos lácteos y derivados'
        )
        self.producto = Producto.objects.create(
            codigo='LAC-001',
            nombre='Leche Entera 1L',
            descripcion='Leche pasteurizada en sachet',
            categoria=self.categoria,
            precio=Decimal('6.50'),
            stock=20,
            stock_minimo=5,
            unidad_medida='Litro',
            estado=True
        )

    def test_validacion_codigo_unico(self):
        """Verifica que el sistema rechaza la creación de un producto con código duplicado."""
        prod_duplicado = Producto(
            codigo='LAC-001',  # Código ya existente
            nombre='Leche Descremada',
            categoria=self.categoria,
            precio=Decimal('7.00'),
            stock=10,
            stock_minimo=5
        )
        with self.assertRaises(Exception):
            prod_duplicado.save()

    def test_validacion_precio_no_negativo(self):
        """Verifica que no se permitan precios negativos."""
        prod_invalido = Producto(
            codigo='LAC-999',
            nombre='Yogurt Fresa',
            categoria=self.categoria,
            precio=Decimal('-5.00'),  # Precio negativo
            stock=10,
            stock_minimo=5
        )
        with self.assertRaises(ValidationError):
            prod_invalido.full_clean()

    def test_validacion_stock_no_negativo(self):
        """Verifica que la cantidad existente no pueda ser negativa."""
        prod_invalido = Producto(
            codigo='LAC-888',
            nombre='Queso Criollo',
            categoria=self.categoria,
            precio=Decimal('25.00'),
            stock=-2,  # Stock negativo
            stock_minimo=5
        )
        with self.assertRaises(ValidationError):
            prod_invalido.full_clean()

    def test_borrado_logico_toggle_estado(self):
        """Verifica el borrado lógico cambiando el estado del producto a inactivo (RF-04)."""
        self.assertTrue(self.producto.estado)
        response = self.client.post(reverse('api_producto_toggle_estado', kwargs={'producto_id': self.producto.id}))
        self.assertEqual(response.status_code, 200)
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.estado)

        # Reactivación
        response2 = self.client.post(reverse('api_producto_toggle_estado', kwargs={'producto_id': self.producto.id}))
        self.assertEqual(response2.status_code, 200)
        self.producto.refresh_from_db()
        self.assertTrue(self.producto.estado)

    def test_control_existencias_ajustar_stock(self):
        """Verifica el aumento y disminución de stock impidiendo cantidades negativas (RF-05)."""
        # Aumentar stock en 5 unidades
        res_aumentar = self.client.post(
            reverse('api_producto_ajustar_stock', kwargs={'producto_id': self.producto.id}),
            data=json.dumps({'accion': 'aumentar', 'delta': 5}),
            content_type='application/json'
        )
        self.assertEqual(res_aumentar.status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 25)

        # Disminuir stock en 10 unidades
        res_disminuir = self.client.post(
            reverse('api_producto_ajustar_stock', kwargs={'producto_id': self.producto.id}),
            data=json.dumps({'accion': 'disminuir', 'delta': 10}),
            content_type='application/json'
        )
        self.assertEqual(res_disminuir.status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)

        # Intentar disminuir más de lo disponible (debe ser rechazado con error 400)
        res_exceso = self.client.post(
            reverse('api_producto_ajustar_stock', kwargs={'producto_id': self.producto.id}),
            data=json.dumps({'accion': 'disminuir', 'delta': 100}),
            content_type='application/json'
        )
        self.assertEqual(res_exceso.status_code, 400)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 15)  # El stock permanece inalterado

    def test_consulta_detalle_producto(self):
        """Verifica la consulta de detalle completo de un producto (Subpunto 1.3: Detalle)."""
        response = self.client.get(reverse('api_producto_detalle', kwargs={'producto_id': self.producto.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['producto']['codigo'], 'LAC-001')
        self.assertEqual(data['producto']['nombre'], 'Leche Entera 1L')
        self.assertEqual(data['producto']['precio'], 6.50)
        self.assertEqual(data['producto']['stock'], 20)
        self.assertIn('valor_inventario', data['producto'])

    def test_comando_generar_reporte(self):
        """Verifica la ejecución del comando de reporte en terminal (Subpunto 1.4)."""
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('generar_reporte', tipo='valor_total', stdout=out)
        salida = out.getvalue()
        self.assertIn('Valor Total', salida)
        self.assertIn('[OK]', salida)


class TestPatronStrategyReportes(TestCase):
    """
    Pruebas unitarias para el Patrón STRATEGY y los reportes predefinidos (RF-06):
    - Producto más caro / más barato.
    - Productos con pocas existencias (stock <= stock_minimo).
    - Productos agotados (stock = 0).
    - Valor total del inventario.
    - Productos con mayor cantidad.
    """
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre='Abarrotes', descripcion='Despensa')
        
        self.p_caro = Producto.objects.create(
            codigo='ABA-001',
            nombre='Aceite de Oliva Extra Virgen 1L',
            categoria=self.categoria,
            precio=Decimal('85.00'),
            stock=10,
            stock_minimo=3,
            unidad_medida='Botella'
        )
        self.p_barato = Producto.objects.create(
            codigo='ABA-002',
            nombre='Sal Yodada 1Kg',
            categoria=self.categoria,
            precio=Decimal('2.50'),
            stock=50,
            stock_minimo=10,
            unidad_medida='Bolsa'
        )
        self.p_agotado = Producto.objects.create(
            codigo='ABA-003',
            nombre='Arroz Integral 1Kg',
            categoria=self.categoria,
            precio=Decimal('12.00'),
            stock=0,  # Agotado
            stock_minimo=5,
            unidad_medida='Bolsa'
        )
        self.p_critico = Producto.objects.create(
            codigo='ABA-004',
            nombre='Fideos Espagueti 500g',
            categoria=self.categoria,
            precio=Decimal('5.50'),
            stock=3,  # Menor que stock_minimo (5)
            stock_minimo=5,
            unidad_medida='Paquete'
        )

    def test_reporte_producto_mas_caro(self):
        contexto = ReporteContext(tipo_reporte='mas_caro')
        datos = contexto.generar()
        self.assertTrue(datos['encontrado'])
        self.assertEqual(datos['producto']['codigo'], 'ABA-001')
        self.assertEqual(datos['producto']['precio'], 85.00)

    def test_reporte_producto_mas_barato(self):
        contexto = ReporteContext(tipo_reporte='mas_barato')
        datos = contexto.generar()
        self.assertTrue(datos['encontrado'])
        self.assertEqual(datos['producto']['codigo'], 'ABA-002')
        self.assertEqual(datos['producto']['precio'], 2.50)

    def test_reporte_productos_agotados(self):
        contexto = ReporteContext(tipo_reporte='agotados')
        datos = contexto.generar()
        self.assertEqual(datos['total'], 1)
        self.assertEqual(datos['items'][0]['codigo'], 'ABA-003')

    def test_reporte_pocas_existencias(self):
        contexto = ReporteContext(tipo_reporte='pocas_existencias')
        datos = contexto.generar()
        self.assertEqual(datos['total'], 1)
        self.assertEqual(datos['items'][0]['codigo'], 'ABA-004')

    def test_reporte_valor_total_inventario(self):
        # Valor esperado: (85*10) + (2.50*50) + (12*0) + (5.50*3) = 850 + 125 + 0 + 16.5 = 991.50
        contexto = ReporteContext(tipo_reporte='valor_total')
        datos = contexto.generar()
        self.assertEqual(datos['valor_total_bs'], 991.50)
        self.assertEqual(datos['total_productos'], 4)
        self.assertEqual(datos['total_unidades'], 63)

    def test_api_reportes_endpoint(self):
        client = Client()
        response = client.get(reverse('api_reportes') + '?tipo=mas_caro')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('datos', data)
        self.assertIn('resumen_texto', data)


class TestPatronFactoryYServicioOllama(TestCase):
    """
    Pruebas unitarias para el Patrón FACTORY y la integración con IA Local (RF-08):
    - Creación de servicio mediante fábrica.
    - Manejo de disponibilidad y fallos.
    - Registro en historial ConsultaIA (RF-10).
    """
    def test_factory_instancia_servicio_local(self):
        servicio = AILocalServiceFactory.crear_servicio('ollama')
        self.assertIsInstance(servicio, OllamaLocalService)
        self.assertIn('localhost:11434', servicio.base_url)

    def test_construccion_contexto_estructurado(self):
        cat = Categoria.objects.create(nombre='Panadería', descripcion='Pan')
        Producto.objects.create(
            codigo='PAN-001',
            nombre='Marraqueta Tradicional',
            categoria=cat,
            precio=Decimal('0.80'),
            stock=100,
            stock_minimo=20,
            unidad_medida='Unidad'
        )
        servicio = OllamaLocalService()
        contexto = servicio.construir_contexto_inventario()
        self.assertTrue(isinstance(contexto, (str, list)))
        self.assertIn('PAN-001', str(contexto))
        self.assertIn('0.80', str(contexto))

    def test_registro_consulta_ia(self):
        """Verifica que el modelo ConsultaIA almacene correctamente las consultas (RF-10)."""
        consulta = ConsultaIA.objects.create(
            pregunta='¿Qué productos están agotados?',
            respuesta='No hay productos agotados actualmente.',
            usuario='UsuarioTest'
        )
        self.assertEqual(ConsultaIA.objects.count(), 1)
        self.assertEqual(consulta.usuario, 'UsuarioTest')
        self.assertIsNotNone(consulta.fecha)
