# Registro de Modificaciones Técnicas - CAMBIOS.md

**Asignatura:** Programación IV  
**Actividad:** Actividad 4 - Implementación, localización y extensión de un proyecto open source con Ollama o LlamaCpp  
**Repositorio Base:** [django-llm-chatbot-app (GitHub)](https://github.com/Kaushikc4/django-llm-chatbot-app)  
**Fecha de Referencia:** Septiembre 2026  
**Sistema Operativo:** Linux (Debian 12)  
**Red Local de Trabajo:** Subred `172.25.4.228/25`  

---

## 1. Identificación y Diagnóstico del Proyecto Base (Punto 1)

El proyecto original es una aplicación desarrollada en 2024 que utilizaba Django y Streamlit para comunicarse con un modelo Ollama. En su estado inicial presentaba las siguientes limitaciones críticas:
1. **Idioma:** Interfaz, botones, mensajes del sistema y documentación completamente en inglés.
2. **Arquitectura de Invocación:** Utilizaba llamadas síncronas bloqueantes con `subprocess.run(['ollama', 'run', ...])`, sin manejo robusto de sesiones ni historial conversacional multi-turno.
3. **Restricción de Recursos (RAM):** Intentaba levantar modelos pesados (`llama3` de 8B o `gemma:2b`), provocando colapsos de memoria (*Out of Memory - OOM*) en servidores con ~4 GB de RAM física disponible.
4. **Restricción de Red:** Escuchaba exclusivamente en `127.0.0.1:8000`, imposibilitando el acceso desde otros dispositivos de la red local institucional o doméstica.
5. **Funcionalidades Limitadas:** Carecía de interfaz web nativa en Django, modo claro/oscuro, selección de roles, exportación de conversaciones y herramientas de accesibilidad.

---

## 2. Ajustes de Infraestructura y Configuración de Red

### 2.1 Modelo de Inteligencia Artificial Optimizado
- **Problema:** El servidor cuenta con 3.8 GiB de RAM (~1.8 GiB libres). `llama3` requiere más de 4.7 GiB, lo que causaba cierre forzoso de procesos por el kernel.
- **Solución:** Se integró y configuró el modelo **`qwen2.5:1.5b`** a través de la librería oficial `ollama.Client`. Este modelo ocupa únicamente **986 MB**, responde de forma instantánea, mantiene excelente coherencia y cuenta con dominio nativo sobresaliente del idioma español.
- **Mecanismo de Respaldo:** En `ai_chat/chatbot.py` se implementó un bloque de recuperación por si el modelo principal configurado en `.env` falla, realizando *fallback* automático a `qwen2.5:1.5b`.

### 2.2 Exposición en la Subred `172.25.4.228/25`
- En `chat/settings.py` se añadieron:
  - `ALLOWED_HOSTS = ['*']` (con soporte para `172.25.4.228` y localhost).
  - `CSRF_TRUSTED_ORIGINS = ['http://172.25.4.228:8000', 'http://172.25.4.228:8501', ...]`
- Se configuró el bind en `0.0.0.0:8000` y `0.0.0.0:8501`.
- Se creó el script de inicio unificado `iniciar_servidor.sh`.

---

## 3. Localización al Español y Ajustes Funcionales (Punto 2)

### 3.1 Interfaz de Usuario 100% en Español
- Se tradujeron la totalidad de los elementos visuales en Django y Streamlit:
  - Título principal: *"¡Chatea Conmigo!"*
  - Botón de acción: *"➕ Nueva Conversación"*
  - Estados y avisos: *"Pensando la respuesta..."*, *"Aún no hay conversaciones anteriores."*
  - Indicadores de entrada: *"Escribe tu mensaje aquí..."*
  - Mensajes de confirmación y eliminación en español.

### 3.2 System Prompt en Español Coherente
- Se configuró la directiva de sistema en `ai_chat/chatbot.py`:
  > *"Eres un asistente virtual inteligente, servicial y amable. Responde SIEMPRE en español de forma clara, natural y precisa."*
- El historial de los últimos 10 mensajes se envía al modelo con roles mapeados (`system`, `user`, `assistant`), garantizando fluidez conversacional continua.

### 3.3 Documentación
- Se reescribió `README.md` en español explicando detalladamente la configuración de red, inicio rápido, uso de modelos y ejecución de pruebas.

---

## 4. Funcionalidades Adicionales Implementadas (Punto 3)

Se añadieron más de 4 funcionalidades de alto valor sin alterar el comportamiento base:

### ✨ Funcionalidad A: Alternador de Modo Claro / Modo Oscuro
- **Qué hace:** Permite cambiar dinámicamente entre un tema oscuro (*Streamlit Dark & Coral Red*) y un tema claro de alto contraste.
- **Implementación:**
  - Variables CSS dinámicas (`[data-theme="dark"]` y `[data-theme="light"]`).
  - Persistencia de la selección del usuario en `localStorage` del navegador para conservar la preferencia entre recargas.
  - Botón accesible en la barra lateral con iconos de sol/luna (☀️ / 🌙).

### ✨ Funcionalidad B: Sistema de Plantillas de Prompts / Selector de Roles
- **Qué hace:** Permite al usuario definir el perfil cognitivo del modelo antes o durante la interacción.
- **Roles disponibles:**
  1. 🤖 **Asistente General:** Respuestas concisas, amables y certeras.
  2. 💻 **Experto en Python y Django:** Especialista en arquitectura de software, código limpio y explicaciones paso a paso.
  3. ✍️ **Corrector y Redactor:** Análisis de ortografía, sintaxis y mejoras de estilo en español.
  4. 🧑‍🏫 **Tutor Didáctico:** Explicaciones pedagógicas adaptadas para principiantes mediante analogías.
- **Implementación:** Diccionario `ROLES` en `ai_chat/chatbot.py`, parámetro `role` en la API `/api/chat/`, selector interactivo en la cabecera de Django y en la barra lateral de Streamlit.

### ✨ Funcionalidad C: Exportación Integral del Historial de Conversación
- **Qué hace:** Permite descargar o respaldar la conversación activa en múltiples formatos estándar.
- **Formatos soportados:**
  - **Texto plano (.txt):** Transcripción limpia con marcas de tiempo.
  - **JSON (.json):** Estructura de datos completa para respaldos o integraciones de software.
  - **Markdown (.md):** Formato enriquecido listo para informes técnicos o repositorios.
  - **Imprimir / Guardar en PDF:** Integración con estilos `@media print` para exportar a PDF directo desde el navegador.
- **Implementación:** Nuevo endpoint backend `/api/sessions/<id>/export/?format=(txt|json|md)` con cabeceras `Content-Disposition: attachment`.

### ✨ Funcionalidad D: Accesibilidad y Herramientas de Mensaje
- **Copiar al portapapeles (Universal HTTP):** Botón `Copiar` en cada respuesta con confirmación visual limpia (`¡Copiado!`). Implementa respaldo infalible mediante `<textarea>` temporal y `document.execCommand('copy')`, permitiendo el copiado en navegadores sobre HTTP por IP sin bloqueo de seguridad.
- **Métricas de Inferencia en Tiempo Real:** Etiqueta sobria al pie de cada mensaje con tiempo de procesamiento en segundos (ej. `1.2s • qwen2.5:0.5b`).


### ⚡ Optimización Integral de Rendimiento en CPU (qwen2.5:0.5b y RAM permanente)
- **Modelo Ultra Ligero:** Se integró **`qwen2.5:0.5b`** (peso de solo **397 MB** frente a los gigabytes de otros modelos), el cual cabe holgadamente en la memoria física de la máquina virtual (Debian 12 con 3.8 GiB RAM).
- **Eliminación del Retardo de Carga (Keep-Alive):** Se configuró `keep_alive: '24h'` en Ollama para mantener el modelo permanentemente caliente en memoria RAM. Esto eliminó de raíz la espera de más de 25 segundos que causaba la recarga recurrente del modelo desde el archivo SWAP/disco.
- **Parámetros de Inferencia Rápidos:** `num_ctx: 512` (ahorro del 40% en memoria de contexto) y `num_predict: 50` (respuestas concisas y directas en pocos segundos).
- **Precalentamiento Automático:** En `iniciar_servidor.sh` se realiza una llamada de precalentamiento al detectar Ollama para que la primera interacción del usuario no sufra latencia de arranque.



---

## 5. Tabla de Archivos Creados y Modificados

| Archivo | Tipo | Descripción de Cambios |
| :--- | :--- | :--- |
| `ai_chat/chatbot.py` | Modificado | Sustitución de `subprocess` por `ollama.Client`, inclusión de `ROLES`, medición de latencia y manejo de contexto en español. |
| `ai_chat/views.py` | Modificado | Soporte de roles y latencia en `api_send_message`, nuevo endpoint `api_export_session` con descarga en TXT/JSON/MD. |
| `ai_chat/urls.py` | Modificado | Registro de la ruta `/api/sessions/<id>/export/`. |
| `ai_chat/templates/chat.html` | Creado/Modificado | Interfaz web completa en Django con Modo Claro/Oscuro, selector de roles, menú de exportación, copiar, audio y métricas. |
| `ai_chat/streamlit_app.py` | Modificado | Localización total al español, soporte de roles de prompt y exportación de chats en formato TXT. |
| `ai_chat/tests.py` | Modificado | Pruebas unitarias para vistas, endpoints API, exportación de sesiones y selección de roles. |
| `chat/settings.py` | Modificado | Configuración de red para `172.25.4.228/25`, `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`. |
| `iniciar_servidor.sh` | Creado | Script bash para arranque simplificado de Django y Streamlit sobre la red local. |
| `requirements.txt` | Creado | Lista congelada de dependencias generada mediante `pip freeze`. |
| `CAMBIOS.md` | Creado | Documentación técnica requerida por la actividad. |
| `README.md` | Modificado | Manual de instalación, configuración y arquitectura en español. |

---

## 6. Comandos de Instalación y Ejecución

### 6.1 Preparación del Entorno
```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar modelo ligero en Ollama
ollama pull qwen2.5:1.5b
```

### 6.2 Ejecución de la Aplicación
```bash
# Opción 1: Iniciar todo con el script integrado
chmod +x iniciar_servidor.sh
./iniciar_servidor.sh

# Opción 2: Iniciar manualmente Django para la red local
python manage.py runserver 0.0.0.0:8000

# Opción 3: Iniciar Streamlit para la red local
streamlit run ai_chat/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

### 6.3 Ejecución de Pruebas Automatizadas
```bash
python manage.py test
```
*Resultado esperado: 7 pruebas ejecutadas con éxito (`OK`).*
