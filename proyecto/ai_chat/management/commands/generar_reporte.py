"""
Comando de administración de Django para ejecutar reportes predefinidos de inventario (Subpunto 1.4).
Implementa el Patrón STRATEGY desde la línea de comandos (CLI).
"""

from django.core.management.base import BaseCommand
from ai_chat.services.report_strategies import ReporteContext

class Command(BaseCommand):
    help = 'Genera y muestra reportes analíticos del inventario usando el Patrón Strategy (Subpunto 1.4).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            default='valor_total',
            help='Tipo de reporte: todos, mas_caro, mas_barato, pocas_existencias, agotados, por_categoria, valor_total, mayor_cantidad'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        self.stdout.write(self.style.MIGRATE_HEADING(f"=== GENERANDO REPORTE DE INVENTARIO: '{tipo}' ==="))
        
        try:
            contexto = ReporteContext(tipo_reporte=tipo)
            datos = contexto.generar()
            resumen = contexto.generar_texto_resumen(datos)
            
            self.stdout.write(self.style.SUCCESS(f"\nTítulo: {datos.get('titulo', 'Reporte')}"))
            self.stdout.write(f"\nResumen Analítico:\n{resumen}\n")
            
            if 'items' in datos and datos['items']:
                self.stdout.write(self.style.WARNING("--- DETALLE DE REGISTROS ---"))
                for item in datos['items'][:10]:
                    codigo = item.get('codigo', 'N/A')
                    nombre = item.get('nombre', 'N/A')
                    precio = item.get('precio', 0.0)
                    stock = item.get('stock', 0)
                    self.stdout.write(f"• [{codigo}] {nombre} - Bs. {precio:.2f} (Stock: {stock})")
                if len(datos['items']) > 10:
                    self.stdout.write(f"... y {len(datos['items']) - 10} productos más.")
            
            self.stdout.write(self.style.SUCCESS("\n[OK] Reporte generado exitosamente con el Patrón Strategy.\n"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al generar reporte: {str(e)}"))
