from django.core.management.base import BaseCommand
from ai_chat.models import Categoria, Producto

class Command(BaseCommand):
    help = 'Puebla la base de datos con categorías y productos representativos de un supermercado'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando carga de datos del supermercado...'))

        categorias_datos = [
            {
                'nombre': 'Lácteos y Huevos',
                'descripcion': 'Leches, quesos, yogures, mantequillas y huevos frescos.'
            },
            {
                'nombre': 'Carnes y Aves',
                'descripcion': 'Cortes de res, pollo fresco, cerdo y embutidos seleccionados.'
            },
            {
                'nombre': 'Frutas y Verduras',
                'descripcion': 'Productos frescos de la huerta, frutas de temporada y verduras.'
            },
            {
                'nombre': 'Bebidas y Licores',
                'descripcion': 'Aguas, jugos naturales, gaseosas, vinos y licores premium.'
            },
            {
                'nombre': 'Abarrotes y Despensa',
                'descripcion': 'Arroz, pastas, aceites, granos, conservas y salsas.'
            },
            {
                'nombre': 'Panadería y Pastelería',
                'descripcion': 'Panes recién horneados, tostadas, galletas y postres.'
            },
            {
                'nombre': 'Limpieza y Hogar',
                'descripcion': 'Detergentes, desinfectantes, papel higiénico y artículos de aseo.'
            }
        ]

        categorias_objs = {}
        for c in categorias_datos:
            obj, _ = Categoria.objects.get_or_create(
                nombre=c['nombre'],
                defaults={'descripcion': c['descripcion']}
            )
            categorias_objs[c['nombre']] = obj

        productos_datos = [
            # Lácteos y Huevos
            {'codigo': 'LAC-001', 'nombre': 'Leche Entera Larga Vida 1L', 'cat': 'Lácteos y Huevos', 'precio': 1.45, 'stock': 48, 'min': 15, 'med': 'Litro'},
            {'codigo': 'LAC-002', 'nombre': 'Queso Gouda Rebanado 250g', 'cat': 'Lácteos y Huevos', 'precio': 3.80, 'stock': 12, 'min': 10, 'med': 'Paquete'},
            {'codigo': 'LAC-003', 'nombre': 'Yogur Griego Natural 500g', 'cat': 'Lácteos y Huevos', 'precio': 2.90, 'stock': 18, 'min': 8, 'med': 'Unidad'},
            {'codigo': 'LAC-004', 'nombre': 'Mantequilla con Sal 200g', 'cat': 'Lácteos y Huevos', 'precio': 2.40, 'stock': 25, 'min': 10, 'med': 'Unidad'},
            {'codigo': 'LAC-005', 'nombre': 'Huevos Frescos Extra Grandes (Docena)', 'cat': 'Lácteos y Huevos', 'precio': 2.85, 'stock': 34, 'min': 12, 'med': 'Docena'},
            {'codigo': 'LAC-006', 'nombre': 'Queso Parmesano Reggiano Importado 200g', 'cat': 'Lácteos y Huevos', 'precio': 8.90, 'stock': 3, 'min': 5, 'med': 'Unidad'},

            # Carnes y Aves
            {'codigo': 'CAR-001', 'nombre': 'Pechuga de Pollo Fresca 1kg', 'cat': 'Carnes y Aves', 'precio': 5.20, 'stock': 22, 'min': 10, 'med': 'Kg'},
            {'codigo': 'CAR-002', 'nombre': 'Corte Lomo Fino de Res Premium 1kg', 'cat': 'Carnes y Aves', 'precio': 18.50, 'stock': 8, 'min': 5, 'med': 'Kg'},
            {'codigo': 'CAR-003', 'nombre': 'Carne Molida Especial 1kg', 'cat': 'Carnes y Aves', 'precio': 6.80, 'stock': 15, 'min': 8, 'med': 'Kg'},
            {'codigo': 'CAR-004', 'nombre': 'Chuleta de Cerdo Ahumada 1kg', 'cat': 'Carnes y Aves', 'precio': 7.40, 'stock': 11, 'min': 6, 'med': 'Kg'},
            {'codigo': 'CAR-005', 'nombre': 'Jamón Serrano Gran Reserva Selección 1kg', 'cat': 'Carnes y Aves', 'precio': 42.00, 'stock': 2, 'min': 4, 'med': 'Kg'},

            # Frutas y Verduras
            {'codigo': 'FRU-001', 'nombre': 'Plátano / Banana Cavendish 1kg', 'cat': 'Frutas y Verduras', 'precio': 1.10, 'stock': 60, 'min': 20, 'med': 'Kg'},
            {'codigo': 'FRU-002', 'nombre': 'Manzana Roja Royal Gala 1kg', 'cat': 'Frutas y Verduras', 'precio': 2.20, 'stock': 30, 'min': 15, 'med': 'Kg'},
            {'codigo': 'FRU-003', 'nombre': 'Tomate Chonto Fresco 1kg', 'cat': 'Frutas y Verduras', 'precio': 1.60, 'stock': 40, 'min': 15, 'med': 'Kg'},
            {'codigo': 'FRU-004', 'nombre': 'Aguacate Hass Premium 1kg', 'cat': 'Frutas y Verduras', 'precio': 4.50, 'stock': 4, 'min': 8, 'med': 'Kg'},
            {'codigo': 'FRU-005', 'nombre': 'Cebolla Blanca Cabezona 1kg', 'cat': 'Frutas y Verduras', 'precio': 0.95, 'stock': 50, 'min': 20, 'med': 'Kg'},
            {'codigo': 'FRU-006', 'nombre': 'Papa Pastusa Seleccionada 1kg', 'cat': 'Frutas y Verduras', 'precio': 0.85, 'stock': 75, 'min': 25, 'med': 'Kg'},

            # Bebidas y Licores
            {'codigo': 'BEB-001', 'nombre': 'Agua Mineral Sin Gas 1.5L', 'cat': 'Bebidas y Licores', 'precio': 0.75, 'stock': 80, 'min': 25, 'med': 'Botella'},
            {'codigo': 'BEB-002', 'nombre': 'Refresco Coca-Cola Original 2L', 'cat': 'Bebidas y Licores', 'precio': 2.10, 'stock': 45, 'min': 20, 'med': 'Botella'},
            {'codigo': 'BEB-003', 'nombre': 'Jugo de Naranja 100% Natural 1L', 'cat': 'Bebidas y Licores', 'precio': 2.65, 'stock': 19, 'min': 10, 'med': 'Envase'},
            {'codigo': 'BEB-004', 'nombre': 'Cerveza Artesanal IPA Pack x6 330ml', 'cat': 'Bebidas y Licores', 'precio': 9.80, 'stock': 14, 'min': 8, 'med': 'Six-pack'},
            {'codigo': 'BEB-005', 'nombre': 'Whisky Escocés Single Malt 12 Años 750ml', 'cat': 'Bebidas y Licores', 'precio': 58.00, 'stock': 5, 'min': 3, 'med': 'Botella'},

            # Abarrotes y Despensa
            {'codigo': 'ABA-001', 'nombre': 'Arroz Blanco Grano Largo Extra 1kg', 'cat': 'Abarrotes y Despensa', 'precio': 1.35, 'stock': 90, 'min': 30, 'med': 'Kg'},
            {'codigo': 'ABA-002', 'nombre': 'Aceite de Girasol Puro 900ml', 'cat': 'Abarrotes y Despensa', 'precio': 3.10, 'stock': 32, 'min': 15, 'med': 'Botella'},
            {'codigo': 'ABA-003', 'nombre': 'Aceite de Oliva Extra Virgen 500ml', 'cat': 'Abarrotes y Despensa', 'precio': 9.50, 'stock': 2, 'min': 6, 'med': 'Botella'},
            {'codigo': 'ABA-004', 'nombre': 'Pasta Spaghetti Tradicional 500g', 'cat': 'Abarrotes y Despensa', 'precio': 1.15, 'stock': 65, 'min': 20, 'med': 'Paquete'},
            {'codigo': 'ABA-005', 'nombre': 'Café Tostado y Molido Colombiano 500g', 'cat': 'Abarrotes y Despensa', 'precio': 5.90, 'stock': 24, 'min': 10, 'med': 'Bolsa'},
            {'codigo': 'ABA-006', 'nombre': 'Atún en Aceite de Oliva Lata 140g', 'cat': 'Abarrotes y Despensa', 'precio': 1.85, 'stock': 42, 'min': 15, 'med': 'Lata'},
            {'codigo': 'ABA-007', 'nombre': 'Gelatina en Polvo Sabor Fresa 100g', 'cat': 'Abarrotes y Despensa', 'precio': 0.45, 'stock': 55, 'min': 15, 'med': 'Sobre'},

            # Panadería y Pastelería
            {'codigo': 'PAN-001', 'nombre': 'Pan de Molde Integral 500g', 'cat': 'Panadería y Pastelería', 'precio': 2.30, 'stock': 28, 'min': 10, 'med': 'Bolsa'},
            {'codigo': 'PAN-002', 'nombre': 'Pan Francés Fresco (Bolsa x6)', 'cat': 'Panadería y Pastelería', 'precio': 1.20, 'stock': 35, 'min': 12, 'med': 'Bolsa'},
            {'codigo': 'PAN-003', 'nombre': 'Galletas de Chocolate Rellenas 300g', 'cat': 'Panadería y Pastelería', 'precio': 1.95, 'stock': 30, 'min': 10, 'med': 'Paquete'},
            {'codigo': 'PAN-004', 'nombre': 'Torta de Vainilla Artesanal 1kg', 'cat': 'Panadería y Pastelería', 'precio': 14.00, 'stock': 1, 'min': 3, 'med': 'Unidad'},

            # Limpieza y Hogar
            {'codigo': 'LIM-001', 'nombre': 'Detergente Líquido para Ropa Concentrado 3L', 'cat': 'Limpieza y Hogar', 'precio': 11.50, 'stock': 20, 'min': 8, 'med': 'Bidón'},
            {'codigo': 'LIM-002', 'nombre': 'Lavavajillas Líquido Antibacterial 750ml', 'cat': 'Limpieza y Hogar', 'precio': 2.45, 'stock': 26, 'min': 10, 'med': 'Botella'},
            {'codigo': 'LIM-003', 'nombre': 'Papel Higiénico Doble Hoja Pack x12', 'cat': 'Limpieza y Hogar', 'precio': 6.20, 'stock': 18, 'min': 10, 'med': 'Pack'},
            {'codigo': 'LIM-004', 'nombre': 'Desinfectante Multiusos Lavanda 1L', 'cat': 'Limpieza y Hogar', 'precio': 1.90, 'stock': 33, 'min': 12, 'med': 'Botella'},
            {'codigo': 'LIM-005', 'nombre': 'Jabón Líquido para Manos Humectante 500ml', 'cat': 'Limpieza y Hogar', 'precio': 2.15, 'stock': 0, 'min': 8, 'med': 'Frasco'},
        ]

        creados = 0
        actualizados = 0
        for p in productos_datos:
            cat_obj = categorias_objs[p['cat']]
            prod, created = Producto.objects.update_or_create(
                codigo=p['codigo'],
                defaults={
                    'nombre': p['nombre'],
                    'categoria': cat_obj,
                    'precio': p['precio'],
                    'stock': p['stock'],
                    'stock_minimo': p['min'],
                    'unidad_medida': p['med']
                }
            )
            if created:
                creados += 1
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'¡Carga exitosa! Se procesaron {len(categorias_datos)} categorías y {len(productos_datos)} productos '
            f'({creados} nuevos, {actualizados} actualizados).'
        ))
