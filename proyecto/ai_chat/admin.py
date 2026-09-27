from django.contrib import admin
from .models import Producto, Categoria, ConsultaIA, ChatSession, Message

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion', 'total_productos')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)

    def total_productos(self, obj):
        return obj.productos.count()
    total_productos.short_description = 'Total Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'unidad_medida', 'estado', 'estado_stock')
    list_filter = ('categoria', 'estado', 'unidad_medida')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_editable = ('precio', 'stock', 'estado')
    ordering = ('nombre',)
    actions = ['activar_productos', 'desactivar_productos']

    @admin.action(description="Activar productos seleccionados")
    def activar_productos(self, request, queryset):
        filas = queryset.update(estado=True)
        self.message_user(request, f"{filas} productos fueron activados exitosamente.")

    @admin.action(description="Desactivar productos seleccionados (Borrado lógico)")
    def desactivar_productos(self, request, queryset):
        filas = queryset.update(estado=False)
        self.message_user(request, f"{filas} productos fueron desactivados.")


@admin.register(ConsultaIA)
class ConsultaIAAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'usuario', 'pregunta_corta', 'respuesta_corta')
    search_fields = ('pregunta', 'respuesta', 'usuario')
    list_filter = ('fecha', 'usuario')
    readonly_fields = ('fecha',)

    def pregunta_corta(self, obj):
        return obj.pregunta[:50] + ('...' if len(obj.pregunta) > 50 else '')
    pregunta_corta.short_description = 'Pregunta'

    def respuesta_corta(self, obj):
        return obj.respuesta[:50] + ('...' if len(obj.respuesta) > 50 else '')
    respuesta_corta.short_description = 'Respuesta'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_mensajes')
    ordering = ('-created_at',)

    def total_mensajes(self, obj):
        return obj.message.count()
    total_mensajes.short_description = 'Mensajes'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'timestamp', 'mensaje_corto')
    list_filter = ('sender', 'timestamp')

    def mensaje_corto(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    mensaje_corto.short_description = 'Contenido'
