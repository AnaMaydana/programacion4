import re
from decimal import Decimal
from django.db.models import F, Sum, Avg, Count, Max, Min
from ai_chat.models import Categoria, Producto

class InventoryService:
    @staticmethod
    def obtener_producto_mas_caro():
        prod = Producto.objects.select_related('categoria').order_by('-precio').first()
        if not prod:
            return None
        return {
            'codigo': prod.codigo,
            'nombre': prod.nombre,
            'categoria': prod.categoria.nombre,
            'precio': float(prod.precio),
            'stock': prod.stock,
            'unidad_medida': prod.unidad_medida,
            'estado': prod.estado_stock
        }

    @staticmethod
    def obtener_producto_mas_barato():
        prod = Producto.objects.select_related('categoria').order_by('precio').first()
        if not prod:
            return None
        return {
            'codigo': prod.codigo,
            'nombre': prod.nombre,
            'categoria': prod.categoria.nombre,
            'precio': float(prod.precio),
            'stock': prod.stock,
            'unidad_medida': prod.unidad_medida,
            'estado': prod.estado_stock
        }

    @staticmethod
    def obtener_productos_stock_critico():
        criticos = Producto.objects.select_related('categoria').filter(
            stock__lte=F('stock_minimo')
        ).order_by('stock')
        
        resultado = []
        for p in criticos:
            resultado.append({
                'codigo': p.codigo,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo,
                'precio': float(p.precio),
                'unidad_medida': p.unidad_medida,
                'agotado': p.stock <= 0
            })
        return resultado

    @staticmethod
    def obtener_resumen_inventario():
        total_productos = Producto.objects.count()
        total_categorias = Categoria.objects.count()
        
        agregados = Producto.objects.aggregate(
            total_unidades=Sum('stock'),
            precio_promedio=Avg('precio'),
            precio_max=Max('precio'),
            precio_min=Min('precio')
        )
        
        # Cálculo del valor monetario total del inventario (precio * stock)
        valor_total = Decimal('0.00')
        for p in Producto.objects.only('precio', 'stock'):
            valor_total += (p.precio * p.stock)

        stock_critico_count = Producto.objects.filter(stock__lte=F('stock_minimo')).count()
        agotados_count = Producto.objects.filter(stock__lte=0).count()

        return {
            'total_productos': total_productos,
            'total_categorias': total_categorias,
            'total_unidades': agregados.get('total_unidades') or 0,
            'valor_total_inventario': float(valor_total),
            'precio_promedio': round(float(agregados.get('precio_promedio') or 0), 2),
            'precio_maximo': float(agregados.get('precio_max') or 0),
            'precio_minimo': float(agregados.get('precio_min') or 0),
            'stock_critico_count': stock_critico_count,
            'agotados_count': agotados_count
        }

    @staticmethod
    def buscar_por_categoria(categoria_busqueda):
        categoria = Categoria.objects.filter(nombre__icontains=categoria_busqueda.strip()).first()
        if not categoria:
            return None
        
        productos = categoria.productos.all().order_by('-precio')
        return {
            'categoria': categoria.nombre,
            'total': productos.count(),
            'productos': [
                {
                    'codigo': p.codigo,
                    'nombre': p.nombre,
                    'precio': float(p.precio),
                    'stock': p.stock,
                    'unidad_medida': p.unidad_medida
                }
                for p in productos
            ]
        }

    @classmethod
    def procesar_consulta(cls, prompt_usuario):
        """
        Analiza la pregunta del usuario para detectar intenciones sobre el inventario
        y extraer información precisa de la base de datos sin alucinaciones.
        Si la pregunta no corresponde al inventario (o busca productos no existentes),
        retorna False para aplicar la restricción oficial RF-09.
        """
        p = prompt_usuario.lower().strip()
        
        # Palabras de parada no relevantes para búsqueda de productos
        STOPWORDS = {
            'que', 'qué', 'cual', 'cuál', 'cuales', 'cuáles', 'como', 'cómo',
            'para', 'por', 'con', 'sin', 'sobre', 'entre', 'del', 'los', 'las',
            'una', 'uno', 'unos', 'unas', 'este', 'esta', 'estos', 'estas',
            'tienen', 'tiene', 'tienes', 'hay', 'venden', 'vende', 'vendes', 'existe', 'existen',
            'producto', 'productos', 'precio', 'precios', 'stock', 'cuanto', 'cuánto',
            'cuesta', 'cuestan', 'vale', 'valen', 'dame', 'muestra', 'muéstrame',
            'muestrame', 'ensename', 'enséñame', 'ver', 'busca', 'buscar', 'buscame', 'búscame',
            'lista', 'listar', 'listado', 'todos', 'todas', 'todo', 'toda',
            'informacion', 'información', 'supermercado', 'tienda', 'inventario',
            'tipo', 'tipos', 'quiero', 'saber', 'nombre', 'nombres', 'ropa', 'vestir'
        }

        def generar_variantes(token):
            v = {token}
            if token.endswith('es') and len(token) > 4:
                v.add(token[:-2])
                v.add(token[:-1])
            elif token.endswith('s') and len(token) > 3:
                v.add(token[:-1])
            return v

        # 1. ¿Cuál es el producto más caro / mayor precio?
        if any(w in p for w in ['mas caro', 'más caro', 'mayor precio', 'mas costoso', 'más costoso', 'precio mas alto', 'precio más alto', 'mas valor', 'más valor']):
            mas_caro = cls.obtener_producto_mas_caro()
            if mas_caro:
                respuesta = (
                    f"El producto más caro del inventario es **{mas_caro['nombre']}** "
                    f"(Código: {mas_caro['codigo']}) de la categoría *{mas_caro['categoria']}*, "
                    f"con un precio de **Bs. {mas_caro['precio']:.2f}** y un stock disponible de "
                    f"{mas_caro['stock']} {mas_caro['unidad_medida']}."
                )
                return True, 'producto_mas_caro', mas_caro, respuesta

        # 2. ¿Cuál es el producto más barato / económico?
        if any(w in p for w in ['mas barato', 'más barato', 'menor precio', 'mas economico', 'más económico', 'precio mas bajo', 'precio más bajo', 'de menor costo', 'mas accesible', 'más accesible']):
            mas_barato = cls.obtener_producto_mas_barato()
            if mas_barato:
                respuesta = (
                    f"El producto más barato del inventario es **{mas_barato['nombre']}** "
                    f"(Código: {mas_barato['codigo']}) de la categoría *{mas_barato['categoria']}*, "
                    f"con un precio de **Bs. {mas_barato['precio']:.2f}** y un stock disponible de "
                    f"{mas_barato['stock']} {mas_barato['unidad_medida']}."
                )
                return True, 'producto_mas_barato', mas_barato, respuesta

        # 3. Stock crítico, pocas existencias, por agotarse o faltantes
        if any(w in p for w in [
            'pocas existencias', 'poca existencia', 'pocas unidades', 'poco stock',
            'stock bajo', 'bajo stock', 'stock critico', 'stock crítico', 'por agotarse',
            'por vencer', 'reponer', 'reposicion', 'reposición', 'agotado', 'agotados',
            'agotada', 'agotadas', 'escaso', 'escasos', 'alerta de stock', 'alertas de stock',
            'falta stock', 'faltante', 'faltantes'
        ]):
            criticos = cls.obtener_productos_stock_critico()
            lineas = []
            for c in criticos:
                estado = "AGOTADO (0 unidades)" if c['agotado'] else f"Stock: {c['stock']} {c['unidad_medida']} (Mínimo: {c['stock_minimo']})"
                lineas.append(f"• **{c['nombre']}** [{c['categoria']}] - {estado} - Bs. {c['precio']:.2f}")
            
            respuesta = (
                f"Se registraron **{len(criticos)} productos en alerta de stock o pocas existencias**:\n\n"
                + "\n".join(lineas) +
                "\n\nSe sugiere programar la reposición prioritaria para garantizar el abastecimiento."
            )
            return True, 'stock_critico', criticos, respuesta

        # 4. Valor total del inventario / resumen financiero
        if any(w in p for w in [
            'valor total', 'cuanto vale el inventario', 'cuánto vale el inventario',
            'valor del inventario', 'costo del inventario', 'total del inventario',
            'resumen del inventario', 'resumen general', 'estado del inventario',
            'cuanto dinero', 'cuánto dinero', 'total en dinero'
        ]):
            resumen = cls.obtener_resumen_inventario()
            respuesta = (
                f"**Resumen General del Inventario del Supermercado:**\n\n"
                f"• **Total de productos registrados:** {resumen['total_productos']} ítems\n"
                f"• **Total de categorías:** {resumen['total_categorias']}\n"
                f"• **Unidades físicas en almacén:** {resumen['total_unidades']} unidades\n"
                f"• **Valor monetario total del inventario:** **Bs. {resumen['valor_total_inventario']:,.2f}**\n"
                f"• **Precio promedio:** Bs. {resumen['precio_promedio']:.2f}\n"
                f"• **Productos en alerta de stock:** {resumen['stock_critico_count']} productos "
                f"(incluye {resumen['agotados_count']} agotados)"
            )
            return True, 'resumen_inventario', resumen, respuesta

        # 5. Consulta por categoría específica existente
        categorias = Categoria.objects.all()
        tokens_todos = [w for w in re.findall(r'\b\w+\b', p) if len(w) > 2]
        variantes_consulta = set()
        for t in tokens_todos:
            variantes_consulta.update(generar_variantes(t))

        for cat in categorias:
            nombre_cat_lower = cat.nombre.lower()
            palabras_cat = [w for w in nombre_cat_lower.replace(' y ', ' ').split() if len(w) > 3]
            variantes_cat = set()
            for pc in palabras_cat:
                variantes_cat.update(generar_variantes(pc))
            
            if (variantes_consulta & variantes_cat) or any(palabra in p for palabra in palabras_cat):
                datos_cat = cls.buscar_por_categoria(cat.nombre)
                if datos_cat and datos_cat['productos']:
                    lista_prods = [
                        f"• **{x['nombre']}** ({x['codigo']}): Bs. {x['precio']:.2f} (Stock: {x['stock']} {x['unidad_medida']})"
                        for x in datos_cat['productos']
                    ]
                    respuesta = (
                        f"**Productos en la categoría {datos_cat['categoria']}** ({datos_cat['total']} ítems):\n\n"
                        + "\n".join(lista_prods)
                    )
                    return True, 'categoria_especifica', datos_cat, respuesta

        # 6. Búsqueda por producto específico existente en la base de datos
        # Primero por código exacto (ej. LAC-001, BEB-005)
        for prod in Producto.objects.select_related('categoria').all():
            if prod.codigo.lower() in p:
                respuesta = (
                    f"**{prod.nombre}** (Código: {prod.codigo})\n"
                    f"• Categoría: {prod.categoria.nombre}\n"
                    f"• Precio: **Bs. {prod.precio:.2f}**\n"
                    f"• Stock disponible: {prod.stock} {prod.unidad_medida}\n"
                    f"• Stock mínimo de alerta: {prod.stock_minimo} {prod.unidad_medida}\n"
                    f"• Estado: {prod.estado_stock.capitalize()}"
                )
                return True, 'producto_especifico', prod, respuesta

        # Luego por palabras clave distintivas del nombre del producto (excluyendo stopwords y aplicando variantes)
        tokens_consulta = [w for w in re.findall(r'\b\w+\b', p) if len(w) > 2 and w not in STOPWORDS]
        if tokens_consulta:
            prod_scores = []
            for prod in Producto.objects.select_related('categoria').all():
                nombre_lower = prod.nombre.lower()
                desc_lower = (prod.descripcion or '').lower()
                cat_lower = prod.categoria.nombre.lower()
                score = 0
                for t in tokens_consulta:
                    vars = generar_variantes(t)
                    if any(v in nombre_lower for v in vars):
                        score += 3
                    elif any(v in desc_lower for v in vars):
                        score += 1
                    elif any(v in cat_lower for v in vars):
                        score += 1
                if score > 0:
                    prod_scores.append((score, prod))

            if prod_scores:
                prod_scores.sort(key=lambda x: x[0], reverse=True)
                max_score = prod_scores[0][0]
                coincidencias = [pr for sc, pr in prod_scores if sc == max_score or (len(tokens_consulta) > 1 and sc >= max_score * 0.8)]

                if len(coincidencias) == 1:
                    prod = coincidencias[0]
                    respuesta = (
                        f"**{prod.nombre}** (Código: {prod.codigo})\n"
                        f"• Categoría: {prod.categoria.nombre}\n"
                        f"• Precio: **Bs. {prod.precio:.2f}**\n"
                        f"• Stock disponible: {prod.stock} {prod.unidad_medida}\n"
                        f"• Stock mínimo de alerta: {prod.stock_minimo} {prod.unidad_medida}\n"
                        f"• Estado: {prod.estado_stock.capitalize()}"
                    )
                    return True, 'producto_especifico', prod, respuesta
                else:
                    lineas = [
                        f"• **{pr.nombre}** ({pr.codigo}): Bs. {pr.precio:.2f} (Stock: {pr.stock} {pr.unidad_medida})"
                        for pr in coincidencias[:10]
                    ]
                    respuesta = (
                        f"Se encontraron **{len(coincidencias)} productos relacionados** en el inventario:\n\n"
                        + "\n".join(lineas)
                    )
                    return True, 'producto_especifico', coincidencias, respuesta

        # 7. Consulta explícita por catálogo o categorías del supermercado
        if any(w in p for w in ['que productos tienen', 'que productos hay', 'cuales son los productos', 'catalogo', 'catálogo', 'que venden', 'que categorias tienen', 'lista de productos', 'listar productos', 'lista del inventario']):
            resumen = cls.obtener_resumen_inventario()
            nombres_cats = [c.nombre for c in Categoria.objects.all()]
            respuesta = (
                f"El supermercado cuenta con **{resumen['total_productos']} productos** distribuidos en {len(nombres_cats)} categorías:\n\n"
                + "\n".join([f"• {c}" for c in nombres_cats]) +
                f"\n\nPuedes consultar por el producto más caro, más barato, stock crítico o por una categoría específica."
            )
            return True, 'catalogo_general', resumen, respuesta

        # No se encontró información en el inventario
        return False, None, None, "No encontré información suficiente en el inventario para responder esa pregunta."
