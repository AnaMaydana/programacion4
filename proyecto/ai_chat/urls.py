from django.urls import path
from . import views

urlpatterns = [
    # Panel Principal de Inventario (CRUD y Reportes)
    path('', views.inventario_vista, name='inventario'),
    path('inventario/', views.inventario_vista, name='inventario_directo'),
    path('reportes/', views.reportes_vista, name='reportes'),
    
    # Interfaz de Chat con IA Local
    path('chat/', views.chat, name='chat'),
    path('api/chat/', views.api_send_message, name='api_chat'),
    path('api/sessions/', views.api_get_sessions, name='api_sessions'),
    path('api/sessions/<int:session_id>/messages/', views.api_get_session_messages, name='api_session_messages'),
    path('api/sessions/<int:session_id>/export/', views.api_export_session, name='api_export_session'),
    path('api/sessions/<int:session_id>/delete/', views.api_delete_session, name='api_delete_session'),
    path('api/new-session/', views.api_new_session, name='api_new_session'),
    
    # Endpoints CRUD de Productos (RF-01 a RF-04)
    path('api/productos/crear/', views.api_producto_crear, name='api_producto_crear'),
    path('api/productos/<int:producto_id>/editar/', views.api_producto_editar, name='api_producto_editar'),
    path('api/productos/<int:producto_id>/eliminar/', views.api_producto_eliminar, name='api_producto_eliminar'),
    path('api/productos/<int:producto_id>/toggle-estado/', views.api_producto_toggle_estado, name='api_producto_toggle_estado'),
    
    # Control de Existencias (RF-05)
    path('api/productos/<int:producto_id>/ajustar-stock/', views.api_producto_ajustar_stock, name='api_producto_ajustar_stock'),
    
    # Reportes Predefinidos con Explicación de IA Local (RF-06)
    path('api/reportes/', views.api_reportes, name='api_reportes'),
    path('api/inventario/kpis/', views.api_inventario_kpis, name='api_inventario_kpis'),
]