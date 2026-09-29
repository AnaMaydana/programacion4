# DOCUMENTACIÓN TÉCNICA Y ARQUITECTURA DEL SISTEMA

**Asignatura:** Programación IV  
**Actividad:** Entregable Final - Desarrollo de un sistema de información genérico con CRUD e integración de IA local mediante Ollama, asistido por OpenCode  
**Estudiante:** Ana Maribel Maydana  
**Docente:** Jared Lopez Leaños  
**Institución:** Universidad Privada Domingo Savio (UPDS)  
**Fecha:** 29 de Septiembre de 2026  

---

## 1. INTRODUCCIÓN Y VISIÓN GENERAL

Este documento describe formalmente las decisiones técnicas, la arquitectura de software, los modelos de datos y los patrones de diseño aplicados en el desarrollo del **Sistema de Gestión de Inventario con CRUD e Inteligencia Artificial Local (InvenBot)**.

El objetivo central del sistema es proveer una plataforma web robusta, modular y desacoplada construida sobre el framework **Django 5.x**, que gestiona el inventario de un supermercado boliviano garantizando la soberanía y privacidad de los datos mediante inferencia 100% local con **Ollama**, acelerada con técnicas de pre-procesamiento RAG en SQLite y asistida en su ciclo de vida por **OpenCode**.

---

## 2. ARQUITECTURA DEL SISTEMA

El sistema adopta el patrón arquitectónico **Modelo-Vista-Template (MVT)** característico de Django, complementado con una **Capa de Servicios (Service Layer)** para desacoplar la lógica de negocio, los reportes analíticos y la integración con modelos de lenguaje natural (LLM).

```
+-------------------------------------------------------------------------+
|                              NAVEGADOR WEB                              |
|   HTML5 + Vanilla CSS + Bootstrap 5 + JavaScript Vanilla (Fetch/DOM)    |
|   - Panel Inventario (/inventario/)  - Chatbot InvenBot (/chat/)         |
|   - Pestaña Reportes (/reportes/)    - Admin Django (/admin/)           |
+------------------------------------+------------------------------------+
                                     | HTTP / JSON REST
                                     v
+-------------------------------------------------------------------------+
|                         CAPA WEB / VISTAS (MVT)                         |
|   ai_chat/views.py  |  ai_chat/urls.py  |  ai_chat/forms.py             |
|   - Endpoints CRUD: crear, editar, eliminar, toggle-estado, ajustar     |
|   - Endpoints Chat: api_send_message, export_session, new_session       |
|   - Endpoint Reportes: api_reportes (consumo vía AJAX)                  |
+------------------------------------+------------------------------------+
                                     | Invocación interna
                                     v
+-------------------------------------------------------------------------+
|                       CAPA DE SERVICIOS Y PATRONES                      |
|                                                                         |
|   [PATRÓN STRATEGY]                                                     |
|   ai_chat/services/report_strategies.py                                 |
|   - ReporteContext -> ReporteStrategy (8 estrategias de análisis)       |
|                                                                         |
|   [PATRÓN FACTORY]                                                      |
|   ai_chat/services/ollama_service.py                                    |
|   - AILocalServiceFactory -> OllamaLocalService / OpenAIService         |
|                                                                         |
|   [PATRÓN OBSERVER]                                                     |
|   ai_chat/signals.py (Señales Django post_save)                         |
|   - Observador de stock crítico y agotado con logging estructurado      |
|                                                                         |
|   [MOTOR RAG & DELIMITADOR]                                             |
|   ai_chat/inventory_service.py                                          |
|   - Interceptor de intenciones, lematización heurística y precalculado  |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+-----------------------------------+  +----------------------------------+
|      CAPA DE PERSISTENCIA         |  |   MOTOR DE INFERENCIA LOCAL      |
|      (Django ORM + SQLite 3)      |  |             OLLAMA               |
|   ai_chat/models.py:              |  |   http://localhost:11434         |
|   - Producto (11 atributos)       |  |   Modelo: invenbot               |
|   - Categoria                     |  |   Base: qwen2.5:0.5b (4-bit)     |
|   - ConsultaIA (auditoría)        |  |   Parámetros: keep_alive: 24h,   |
|   - ChatSession y Message         |  |   num_thread: 4, num_predict: 75 |
+-----------------------------------+  +----------------------------------+
```

---

## 3. DECISIONES TÉCNICAS FUNDAMENTALES

### 3.1 Framework Web: Django 5.x
- **Razón:** Proporciona un ecosistema maduro, seguro y estructurado ("Batteries Included"). Ofrece ORM integrado con soporte transaccional, sistema de validación robusto mediante formularios tipados, protección nativa contra inyecciones SQL, ataques CSRF y Cross-Site Scripting (XSS), y un panel de administración personalizable sin dependencias externas.

### 3.2 Motor de Base de Datos: SQLite 3
- **Razón:** Base de datos relacional serverless embebida en Python, conforme al estándar ACID. Elimina la sobrecarga de administración de motores cliente-servidor (PostgreSQL o MySQL) durante fases de laboratorio y evaluación, manteniendo latencias de lectura menores a 1 ms en memoria compartida.

### 3.3 Inteligencia Artificial 100% Local: Ollama (`invenbot` basado en `qwen2.5:0.5b`)
- **Razón:** Garantiza total soberanía y confidencialidad comercial sobre precios, márgenes y existencias. Evita costos de suscripción por token y funciona completamente offline.
- **Optimización de Modelo:** Se evaluaron modelos de 7B/8B parámetros, pero saturaban la memoria RAM del equipo de laboratorio (Debian 12 con 4 GB de RAM). Se adoptó `qwen2.5:0.5b` cuantizado en 4 bits (397 MB en disco), parametrizado a través de un `Modelfile` optimizado:
  - `num_thread: 4`: Fijación de hilos de CPU dejando 1 núcleo libre para el kernel y Django.
  - `keep_alive: "24h"`: Persistencia de pesos en RAM para suprimir el tiempo de recarga I/O en cada consulta.
  - `num_predict: 75`: Respuestas directas de menos de 100 palabras para latencias sub-segundo.

### 3.4 Arquitectura RAG Híbrida y Fallback de Latencia
- **Razón:** Para mitigar posibles demoras de inferencia por CPU bajo sobrecarga térmica, se implementó la clase `InventoryService`:
  1. Si la pregunta busca listas completas, catálogos o productos específicos, el servicio precalcula la respuesta en SQLite en **0.01 segundos**.
  2. Si la pregunta requiere razonamiento contextual, se envía a Ollama con un timeout de seguridad de 12 segundos.
  3. Si Ollama no responde o el servicio se detiene, el sistema activa automáticamente un fallback instantáneo devolviendo los datos precalculados de la base de datos sin interrumpir la experiencia del usuario.

### 3.5 Renderizado Enriquecido en Frontend (Solución a Asteriscos Crudos)
- **Razón:** Los modelos LLM generan sintaxis Markdown (`**negrita**`, `***resaltado***`), que un renderizador ingenuo despliega como asteriscos crudos en pantalla (`***aceite*** 45`). En `chat.html` se construyó un motor de expresiones regulares en JavaScript que detecta la semántica del texto y la transforma en tarjetas `.ficha-producto-card`, badges `.badge-precio` en Bs. y chips de stock `.stock-pill` estilizados.

---

## 4. PATRONES DE DISEÑO IMPLEMENTADOS

El proyecto implementa rigurosamente **tres patrones de diseño** de la ingeniería de software clásica (GoF):

### 4.1 Patrón STRATEGY (Estrategia para Reportes Analíticos - RF-06)
- **Ubicación:** `ai_chat/services/report_strategies.py`
- **Problema que resuelve:** Evita sentencias condicionales extensas (`if/elif/else`) en las vistas al calcular diferentes estadísticas sobre el inventario, permitiendo añadir o modificar reportes de forma aislada respetando el principio Open/Closed (OCP) de SOLID.
- **Estructura:**
  - `ReporteStrategy (Interfaz ABC)`: Declara los métodos `ejecutar(**kwargs) -> dict` y `obtener_resumen_texto(datos: dict) -> str`.
  - **Estrategias Concretas (8 Implementadas):**
    1. `ListarTodosStrategy`: Catálogo general de productos.
    2. `ProductoMasCaroStrategy`: Máximo precio unitario y ranking Top 5.
    3. `ProductoMasBaratoStrategy`: Mínimo precio unitario y ranking Top 5.
    4. `PocasExistenciasStrategy`: Productos con stock en nivel de alerta ($\le \text{stock\_minimo}$).
    5. `ProductosAgotadosStrategy`: Existencias agotadas ($\text{stock} = 0$).
    6. `ProductosPorCategoriaStrategy`: Agrupación relacional y conteo por departamento.
    7. `ValorTotalInventarioStrategy`: Cálculo global ($\sum \text{precio} \times \text{stock}$), unidades y precio promedio.
    8. `MayorCantidadStrategy`: Top de productos con mayor volumen físico en almacén.
  - `ReporteContext`: Contexto que instancia dinámicamente la estrategia solicitada a través de un diccionario de registro y delega la ejecución.

### 4.2 Patrón FACTORY (Fábrica Polimórfica de Servicios de IA - RF-08)
- **Ubicación:** `ai_chat/services/ollama_service.py`
- **Problema que resuelve:** Desacopla las vistas del controlador del proveedor concreto de inferencia de IA. Permite que el sistema opere por defecto con **Ollama Local** (soberanía de datos) o de forma dual con **OpenAI API** (requerimiento alternativo de la cátedra) según las variables de entorno, sin alterar el código de los endpoints.
- **Estructura:**
  - `AILocalServiceFactory`: Clase factoría con el método estático `crear_servicio(tipo: str = None)`.
  - Clases concretas: `OllamaLocalService` y `OpenAIService`. Ambas respetan el mismo contrato de métodos (`consultar`, `explicar_reporte`, `verificar_disponibilidad`).

### 4.3 Patrón OBSERVER (Observador de Alertas con Señales Django - RF-05)
- **Ubicación:** `ai_chat/signals.py`
- **Problema que resuelve:** Notificar y registrar auditorías de eventos críticos (productos agotados o en stock mínimo) sin acoplar código de alertas dentro del flujo transaccional de guardado en las vistas ni en los formularios.
- **Estructura:**
  - **Sujeto:** Modelo `Producto` al invocar `save()`.
  - **Señal:** `post_save` emitida por el despachador de señales de Django.
  - **Observador:** Función decorada con `@receiver(post_save, sender=Producto) def observador_cambio_stock`. Evalúa las existencias resultantes y genera logs estructurados de advertencia (`WARNING: ALERTA ROJA - AGOTADO`, `WARNING: ALERTA AMARILLA - STOCK CRÍTICO`).

---

## 5. MODELO DE DATOS Y PERSISTENCIA

El esquema de base de datos relacional se compone de las siguientes entidades principales:

### 5.1 Entidad `Producto`
Supera el mínimo de 6 campos exigido, incorporando 11 atributos:
- `id` (`BigAutoField`): Clave primaria autoincremental.
- `codigo` (`CharField`, max=50, `unique=True`): Identificador único comercial / SKU.
- `nombre` (`CharField`, max=150): Denominación del producto.
- `descripcion` (`TextField`, opcional): Detalle y características.
- `categoria` (`ForeignKey` a `Categoria`, `on_delete=CASCADE`): Relación Many-to-One.
- `precio` (`DecimalField`, 10 dígitos, 2 decimales): Precio oficial en Bolivianos (Bs.), validado $\ge 0$.
- `stock` (`IntegerField`): Cantidad física en almacén, validado $\ge 0$.
- `stock_minimo` (`IntegerField`, default=5): Umbral de reposición, validado $\ge 0$.
- `unidad_medida` (`CharField`, default='Unidad'): Kg, Litro, Unidad, Paquete, etc.
- `estado` (`BooleanField`, default=True): Soporte de **borrado lógico** (Activo/Inactivo).
- `fecha_registro` (`DateTimeField`, default=timezone.now): Auditoría de creación.
- `fecha_actualizacion` (`DateTimeField`, auto_now=True): Marca temporal de modificación.
- **Propiedad dinámica:** `estado_stock` ("agotado", "critico", "optimo").

### 5.2 Entidad `Categoria`
- `id` (`BigAutoField`): Clave primaria.
- `nombre` (`CharField`, max=100, `unique=True`): Nombre de la categoría.
- `descripcion` (`TextField`, opcional): Alcance del departamento.

### 5.3 Entidad `ConsultaIA` (Auditoría RF-10)
- `id` (`BigAutoField`): Identificador único.
- `pregunta` (`TextField`): Texto de la consulta del usuario.
- `respuesta` (`TextField`): Respuesta emitida por el modelo de IA.
- `fecha` (`DateTimeField`, `auto_now_add=True`): Fecha y hora exacta.
- `usuario` (`CharField`, max=100): Identificador del usuario solicitante.

### 5.4 Entidades de Chat Conversacional (`ChatSession` y `Message`)
Permiten persistir conversaciones multi-turno y exportar los diálogos en formatos TXT, JSON y Markdown.

---

## 6. CALIDAD, VALIDACIONES Y PRUEBAS

### 6.1 Validaciones en Múltiples Capas
1. **Capa de Modelo (`Producto.clean`):** Valida atómicamente que precio, stock y stock mínimo sean no negativos antes de cualquier operación `save()`.
2. **Capa de Formulario (`ProductoForm`):** Normaliza cadenas de código, descarta espacios residuales y valida unicidad excluyendo la propia instancia en modo edición.
3. **Capa de Endpoint API:** Bloquea ajustes manuales de decremento si el stock resultante resultase menor a cero.

### 6.2 Pruebas Unitarias Automatizadas
Se diseñó una suite de **23 pruebas unitarias** (`TestCase`) en `ai_chat/tests.py` y `ai_chat/tests_inventario.py`, cubriendo:
- Rechazo de códigos duplicados.
- Validación de precios y existencias no negativas.
- Borrado lógico y reactivación mediante toggle de estado.
- Consulta de detalle completo de un producto (Subpunto 1.3: Detalle).
- Control de existencias e impedimento de stock negativo.
- Exactitud matemática de las 8 estrategias de reportes.
- Ejecución de reportes analíticos mediante comando de gestión en terminal (Subpunto 1.4).
- Despacho y funcionamiento de la fábrica polimórfica de IA (`AILocalServiceFactory`).
- Persistencia en la tabla de auditoría `ConsultaIA`.

---

## 7. ASISTENCIA DE OPENCODE EN EL DESARROLLO

El ciclo de desarrollo fue acelerado integralmente mediante **OpenCode**, el agente de codificación de código abierto que opera en la terminal Linux:
- **Generación de Scaffolding:** Creación del modelo relacional `Producto` y validadores limpios en `forms.py`.
- **Integración del Servicio Ollama:** Implementación del cliente HTTP con control de excepciones y timeouts en `services/ollama_service.py`.
- **Refactorización a Patrones de Diseño:** Modularización de reportes mediante el patrón Strategy y desacoplamiento de la factoría de IA.
- **Construcción de la Suite de Pruebas:** Generación de casos de prueba exhaustivos con validación de estados y aserciones.

*(Para el detalle completo de sesiones, prompts, respuestas y código generado, consultar el archivo adjunto [OPENCODE.md](file:///home/maribel/Proyectofinal/proyecto/OPENCODE.md)).*
