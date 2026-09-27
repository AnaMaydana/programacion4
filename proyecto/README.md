# Sistema de Gestión de Inventario con CRUD e IA Local (Ollama)

Sistema de información web desarrollado en **Django 5.2** con base de datos **SQLite** e integración de Inteligencia Artificial **100% Local** mediante **Ollama** utilizando el modelo personalizado **InvenBot** (`qwen2.5:0.5b`).

Desarrollado para la asignatura **Programación IV** (Actividad 5 / Entregable Final).

---

## 🌟 Características Principales

1. **CRUD Completo de Productos (RF-01 a RF-04):**
   - Registro con validaciones: código único, nombre, descripción, categoría, precio >= 0, stock >= 0.
   - Búsqueda en tiempo real por código, nombre y categoría.
   - Edición completa y eliminación física.
   - **Borrado lógico:** Posibilidad de desactivar productos conservando el historial transaccional.
2. **Control de Existencias (RF-05):**
   - Ajustes rápidos de stock (`+` / `−`) en la interfaz web.
   - Bloqueo a nivel de modelo de cantidades negativas.
   - Alertas visuales dinámicas: Óptimo, Crítico y Agotado.
3. **Menú de Reportes Predefinidos (RF-06):**
   - Menú interactivo con los 8 reportes solicitados.
   - Implementado mediante el patrón de diseño **Strategy**.
   - Botón para **explicar el reporte en lenguaje natural con IA local**.
4. **Chat con IA 100% Local (RF-07, RF-08, RF-09):**
   - Agente **InvenBot** ejecutándose en CPU local con Ollama.
   - Restricción estricta: Solo responde sobre el inventario y precios en Bolivianos (Bs.).
   - Historial de consultas almacenado en base de datos (`ConsultaIA`, RF-10).
   - Renderizado enriquecido: Badges de precios, chips de stock y fichas de producto sin asteriscos crudos.
5. **Arquitectura y Patrones de Diseño (Punto 3):**
   - **Strategy:** Para el cálculo de los 8 reportes de inventario.
   - **Factory:** Para la instanciación desacoplada del servicio de IA local.
   - **Observer:** Mediante señales Django (`post_save`) para monitoreo de stock crítico.

---

## 🚀 Requisitos e Instalación

### Requisitos del Sistema
- Linux (Debian 12 / Ubuntu o similar)
- Python 3.11+
- Ollama instalado localmente

### 1. Preparar Entorno Virtual y Dependencias
```bash
# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar el Modelo en Ollama
```bash
# Descargar modelo base
ollama pull qwen2.5:0.5b

# Crear el modelo InvenBot a partir del Modelfile incluido
ollama create invenbot -f Modelfile
```

### 3. Migraciones y Base de Datos
```bash
python manage.py makemigrations ai_chat
python manage.py migrate
```

### 4. Iniciar la Aplicación
```bash
# Iniciar servidor Django en el puerto 8000
python manage.py runserver 0.0.0.0:8000

# O utilizar el script automatizado:
./iniciar_servidor.sh django
```

Acceder desde el navegador:
👉 **`http://localhost:8000/`** (Panel de Inventario y Reportes)  
👉 **`http://localhost:8000/chat/`** (Chatbot InvenBot con IA Local)  
👉 **`http://localhost:8000/admin/`** (Panel Administrativo de Django)

---

## 🧪 Ejecución de Pruebas Unitarias

Para validar el funcionamiento del CRUD, validaciones numéricas, patrones de diseño y llamadas al servicio local:

```bash
python manage.py test
```

Salida esperada:
```text
Found 21 test(s).
----------------------------------------------------------------------
Ran 21 tests ...
OK
```
