import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from ai_chat.models import Categoria, Producto
from ai_chat.inventory_service import InventoryService
from ai_chat.chatbot import Chatbot

class TestInventarioSupermercado(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_lacteos = Categoria.objects.create(
            nombre='Lácteos Test',
            descripcion='Categoría de prueba lácteos'
        )
        self.cat_carnes = Categoria.objects.create(
            nombre='Carnes Test',
            descripcion='Categoría de prueba carnes'
        )
        self.prod_barato = Producto.objects.create(
            codigo='TST-001',
            nombre='Gelatina de Fresa',
            categoria=self.cat_lacteos,
            precio=Decimal('0.80'),
            stock=50,
            stock_minimo=10,
            unidad_medida='Sobre'
        )
        self.prod_caro = Producto.objects.create(
            codigo='TST-002',
            nombre='Whisky 18 Años',
            categoria=self.cat_carnes,
            precio=Decimal('95.50'),
            stock=3,
            stock_minimo=5,
            unidad_medida='Botella'
        )

    def test_inventario_page_loads(self):
        response = self.client.get(reverse('inventario'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Supermercado')
        self.assertContains(response, 'Whisky 18 Años')
        self.assertContains(response, 'Gelatina de Fresa')

    def test_api_crear_producto(self):
        payload = {
            'codigo': 'NEW-999',
            'nombre': 'Arroz Diana 1kg',
            'categoria_id': self.cat_lacteos.id,
            'precio': '1.50',
            'stock': 40,
            'stock_minimo': 15,
            'unidad_medida': 'Kg'
        }
        response = self.client.post(
            reverse('api_producto_crear'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(Producto.objects.filter(codigo='NEW-999').exists())

    def test_api_editar_producto(self):
        payload = {
            'nombre': 'Gelatina de Fresa Grande',
            'precio': '1.20',
            'stock': 45
        }
        response = self.client.post(
            reverse('api_producto_editar', kwargs={'producto_id': self.prod_barato.id}),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.prod_barato.refresh_from_db()
        self.assertEqual(self.prod_barato.nombre, 'Gelatina de Fresa Grande')
        self.assertEqual(self.prod_barato.precio, Decimal('1.20'))

    def test_api_eliminar_producto(self):
        response = self.client.post(
            reverse('api_producto_eliminar', kwargs={'producto_id': self.prod_barato.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Producto.objects.filter(id=self.prod_barato.id).exists())

    def test_inventory_service_queries(self):
        caro = InventoryService.obtener_producto_mas_caro()
        self.assertIsNotNone(caro)
        self.assertEqual(caro['codigo'], 'TST-002')
        self.assertEqual(caro['precio'], 95.50)

        barato = InventoryService.obtener_producto_mas_barato()
        self.assertIsNotNone(barato)
        self.assertEqual(barato['codigo'], 'TST-001')

        criticos = InventoryService.obtener_productos_stock_critico()
        # Whisky tiene stock=3 y stock_minimo=5, debe estar en críticos
        codigos_criticos = [c['codigo'] for c in criticos]
        self.assertIn('TST-002', codigos_criticos)

    def test_procesar_consulta_intencion(self):
        match, intencion, datos, ctx = InventoryService.procesar_consulta('¿Cuál es el producto más caro?')
        self.assertTrue(match)
        self.assertEqual(intencion, 'producto_mas_caro')
        self.assertIn('Whisky 18 Años', ctx)
        self.assertIn('Bs. 95.50', ctx)

    def test_chatbot_con_consulta_inventario(self):
        bot = Chatbot(user='TestUser', role='inventario')
        reply = bot.chatbot('¿Cuál es el producto más caro?')
        self.assertIsNotNone(reply)
        # La respuesta debe mencionar el producto más caro real
        self.assertTrue(any(word in reply.lower() for word in ['whisky', '95.5', 'caro', 'precio']))
