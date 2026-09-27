"""
Patrón de Diseño: STRATEGY
Este módulo implementa el patrón Strategy para la generación y análisis de los
8 reportes predefinidos del inventario del supermercado (RF-06).
Permite encapsular cada algoritmo de cálculo y presentación de datos de forma intercambiable.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from django.db.models import F, Sum, Avg, Count, Max, Min
from ai_chat.models import Producto, Categoria

class ReporteStrategy(ABC):
    """
    Interfaz abstracta de la estrategia para los reportes de inventario.
    """
    @abstractmethod
    def ejecutar(self, **kwargs) -> dict:
        """
        Ejecuta la estrategia y retorna un diccionario con los datos del reporte.
        """
        pass

    @abstractmethod
    def obtener_resumen_texto(self, datos: dict) -> str:
        """
        Retorna una representación en texto del resultado para ser explicada por la IA local.
        """
        pass


class ListarTodosStrategy(ReporteStrategy):
    """Reporte 1: Listar todos los productos registrados."""
    def ejecutar(self, **kwargs) -> dict:
        productos = Producto.objects.select_related('categoria').all().order_by('nombre')
        items = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'precio': float(p.precio),
                'stock': p.stock,
                'unidad_medida': p.unidad_medida,
                'estado': 'Activo' if p.estado else 'Inactivo',
                'estado_stock': p.estado_stock
            }
            for p in productos
        ]
        return {
            'tipo': 'listar_todos',
            'titulo': 'Listado Completo de Productos',
            'total': len(items),
            'items': items
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        resumen = f"Total de productos registrados: {datos['total']}.\n"
        for it in datos['items'][:10]:
            resumen += f"- {it['nombre']} ({it['codigo']}): Bs. {it['precio']:.2f}, Stock: {it['stock']} {it['unidad_medida']}\n"
        if datos['total'] > 10:
            resumen += f"... y {datos['total'] - 10} productos más."
        return resumen


class ProductoMasCaroStrategy(ReporteStrategy):
    """Reporte 2: Mostrar el producto más caro y ranking Top 5."""
    def ejecutar(self, **kwargs) -> dict:
        prod = Producto.objects.select_related('categoria').order_by('-precio').first()
        if not prod:
            return {'tipo': 'mas_caro', 'titulo': 'Producto Más Caro', 'encontrado': False}
        
        top_5_qs = Producto.objects.select_related('categoria').order_by('-precio')[:5]
        top_5 = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'precio': float(p.precio),
                'stock': p.stock,
                'unidad_medida': p.unidad_medida,
                'estado_stock': p.estado_stock
            }
            for p in top_5_qs
        ]

        return {
            'tipo': 'mas_caro',
            'titulo': 'Producto Más Caro y Top 5 de Mayor Precio',
            'encontrado': True,
            'producto': {
                'id': prod.id,
                'codigo': prod.codigo,
                'nombre': prod.nombre,
                'categoria': prod.categoria.nombre,
                'precio': float(prod.precio),
                'stock': prod.stock,
                'unidad_medida': prod.unidad_medida,
                'estado_stock': prod.estado_stock
            },
            'top_5': top_5,
            'items': top_5
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        if not datos.get('encontrado'):
            return "No hay productos registrados en el inventario."
        p = datos['producto']
        texto = f"El producto más caro es {p['nombre']} ({p['codigo']}) con un precio de Bs. {p['precio']:.2f} en la categoría {p['categoria']}, con stock de {p['stock']} {p['unidad_medida']}."
        if 'top_5' in datos and len(datos['top_5']) > 1:
            texto += "\nRanking de los 5 productos con mayor precio:\n"
            for idx, item in enumerate(datos['top_5'], 1):
                texto += f"  {idx}. {item['nombre']} ({item['codigo']}): Bs. {item['precio']:.2f} ({item['categoria']})\n"
        return texto


class ProductoMasBaratoStrategy(ReporteStrategy):
    """Reporte 3: Mostrar el producto más barato y ranking Top 5."""
    def ejecutar(self, **kwargs) -> dict:
        prod = Producto.objects.select_related('categoria').order_by('precio').first()
        if not prod:
            return {'tipo': 'mas_barato', 'titulo': 'Producto Más Barato', 'encontrado': False}
        
        top_5_qs = Producto.objects.select_related('categoria').order_by('precio')[:5]
        top_5 = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'precio': float(p.precio),
                'stock': p.stock,
                'unidad_medida': p.unidad_medida,
                'estado_stock': p.estado_stock
            }
            for p in top_5_qs
        ]

        return {
            'tipo': 'mas_barato',
            'titulo': 'Producto Más Barato y Top 5 de Menor Precio',
            'encontrado': True,
            'producto': {
                'id': prod.id,
                'codigo': prod.codigo,
                'nombre': prod.nombre,
                'categoria': prod.categoria.nombre,
                'precio': float(prod.precio),
                'stock': prod.stock,
                'unidad_medida': prod.unidad_medida,
                'estado_stock': prod.estado_stock
            },
            'top_5': top_5,
            'items': top_5
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        if not datos.get('encontrado'):
            return "No hay productos registrados en el inventario."
        p = datos['producto']
        texto = f"El producto más barato es {p['nombre']} ({p['codigo']}) con un precio de Bs. {p['precio']:.2f} en la categoría {p['categoria']}, con stock de {p['stock']} {p['unidad_medida']}."
        if 'top_5' in datos and len(datos['top_5']) > 1:
            texto += "\nRanking de los 5 productos con menor precio:\n"
            for idx, item in enumerate(datos['top_5'], 1):
                texto += f"  {idx}. {item['nombre']} ({item['codigo']}): Bs. {item['precio']:.2f} ({item['categoria']})\n"
        return texto


class PocasExistenciasStrategy(ReporteStrategy):
    """Reporte 4: Mostrar productos con pocas existencias (stock <= stock_minimo)."""
    def ejecutar(self, **kwargs) -> dict:
        prods = Producto.objects.select_related('categoria').filter(
            stock__lte=F('stock_minimo'), stock__gt=0
        ).order_by('stock')
        items = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo,
                'unidad_medida': p.unidad_medida,
                'precio': float(p.precio)
            }
            for p in prods
        ]
        return {
            'tipo': 'pocas_existencias',
            'titulo': 'Productos con Pocas Existencias (Nivel Crítico)',
            'total': len(items),
            'items': items
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        if datos['total'] == 0:
            return "No existen productos con existencias críticas actualmente."
        texto = f"Se detectaron {datos['total']} productos con pocas existencias (menores o iguales al stock mínimo):\n"
        for it in datos['items']:
            texto += f"- {it['nombre']}: stock actual {it['stock']} {it['unidad_medida']} (mínimo permitido: {it['stock_minimo']})\n"
        return texto


class ProductosAgotadosStrategy(ReporteStrategy):
    """Reporte 5: Mostrar productos agotados (stock == 0)."""
    def ejecutar(self, **kwargs) -> dict:
        prods = Producto.objects.select_related('categoria').filter(stock__lte=0).order_by('nombre')
        items = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'precio': float(p.precio),
                'unidad_medida': p.unidad_medida
            }
            for p in prods
        ]
        return {
            'tipo': 'agotados',
            'titulo': 'Productos Agotados (Stock 0)',
            'total': len(items),
            'items': items
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        if datos['total'] == 0:
            return "No hay productos agotados en el inventario."
        texto = f"Se encontraron {datos['total']} productos totalmente agotados (stock 0):\n"
        for it in datos['items']:
            texto += f"- {it['nombre']} ({it['codigo']}) - Categoría: {it['categoria']}\n"
        return texto


class ProductosPorCategoriaStrategy(ReporteStrategy):
    """Reporte 6: Mostrar productos organizados por categoría."""
    def ejecutar(self, categoria_id=None, **kwargs) -> dict:
        categorias_qs = Categoria.objects.prefetch_related('productos').all()
        if categoria_id:
            categorias_qs = categorias_qs.filter(id=categoria_id)

        resultado = []
        todos_los_items = []
        for cat in categorias_qs:
            prods = cat.productos.all()
            prods_list = [
                {
                    'id': p.id,
                    'codigo': p.codigo,
                    'nombre': p.nombre,
                    'categoria': cat.nombre,
                    'categoria_id': cat.id,
                    'precio': float(p.precio),
                    'stock': p.stock,
                    'unidad_medida': p.unidad_medida,
                    'estado_stock': p.estado_stock
                }
                for p in prods
            ]
            resultado.append({
                'id': cat.id,
                'categoria': cat.nombre,
                'total_productos': len(prods_list),
                'total_unidades': sum(p.stock for p in prods),
                'productos': prods_list
            })
            todos_los_items.extend(prods_list)

        return {
            'tipo': 'por_categoria',
            'titulo': 'Productos por Categoría',
            'categorias': resultado,
            'items': todos_los_items,
            'total': len(todos_los_items)
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        texto = "Distribución de productos por categoría:\n"
        for c in datos['categorias']:
            texto += f"- {c['categoria']}: {c['total_productos']} productos registrados ({c['total_unidades']} unidades físicas)\n"
        return texto


class ValorTotalInventarioStrategy(ReporteStrategy):
    """Reporte 7: Mostrar el valor total del inventario y métricas financieras."""
    def ejecutar(self, **kwargs) -> dict:
        total_productos = Producto.objects.count()
        total_unidades = Producto.objects.aggregate(Sum('stock'))['stock__sum'] or 0
        precio_promedio = Producto.objects.aggregate(Avg('precio'))['precio__avg'] or Decimal('0.00')

        valor_total = Decimal('0.00')
        for p in Producto.objects.only('precio', 'stock'):
            valor_total += (p.precio * p.stock)

        return {
            'tipo': 'valor_total',
            'titulo': 'Valor Total y Resumen Financiero del Inventario',
            'total_productos': total_productos,
            'total_unidades': total_unidades,
            'precio_promedio': round(float(precio_promedio), 2),
            'valor_total_bs': float(valor_total)
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        return (
            f"El valor monetario total del inventario del supermercado es de Bs. {datos['valor_total_bs']:,.2f}. "
            f"Contiene un total de {datos['total_unidades']} unidades físicas pertenecientes a {datos['total_productos']} productos, "
            f"con un precio promedio de Bs. {datos['precio_promedio']:.2f}."
        )


class MayorCantidadStrategy(ReporteStrategy):
    """Reporte 8: Mostrar productos con mayor cantidad disponible."""
    def ejecutar(self, limite=5, **kwargs) -> dict:
        prods = Producto.objects.select_related('categoria').order_by('-stock')[:limite]
        items = [
            {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'stock': p.stock,
                'unidad_medida': p.unidad_medida,
                'precio': float(p.precio)
            }
            for p in prods
        ]
        return {
            'tipo': 'mayor_cantidad',
            'titulo': f'Top {len(items)} Productos con Mayor Cantidad Disponible',
            'items': items
        }

    def obtener_resumen_texto(self, datos: dict) -> str:
        texto = f"Los productos con mayor disponibilidad en el almacén son:\n"
        for it in datos['items']:
            texto += f"- {it['nombre']}: {it['stock']} {it['unidad_medida']} disponibles (Precio: Bs. {it['precio']:.2f})\n"
        return texto


class ReporteContext:
    """
    Contexto que utiliza la estrategia seleccionada (Patrón Strategy).
    """
    ESTRATEGIAS = {
        'todos': ListarTodosStrategy,
        'mas_caro': ProductoMasCaroStrategy,
        'mas_barato': ProductoMasBaratoStrategy,
        'pocas_existencias': PocasExistenciasStrategy,
        'agotados': ProductosAgotadosStrategy,
        'por_categoria': ProductosPorCategoriaStrategy,
        'valor_total': ValorTotalInventarioStrategy,
        'mayor_cantidad': MayorCantidadStrategy,
    }

    def __init__(self, tipo_reporte: str = 'valor_total'):
        estrategia_clase = self.ESTRATEGIAS.get(tipo_reporte, ValorTotalInventarioStrategy)
        self.strategy: ReporteStrategy = estrategia_clase()

    def set_strategy(self, strategy: ReporteStrategy):
        self.strategy = strategy

    def generar(self, **kwargs) -> dict:
        return self.strategy.ejecutar(**kwargs)

    def generar_texto_resumen(self, datos: dict) -> str:
        return self.strategy.obtener_resumen_texto(datos)
