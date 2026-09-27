# REQUERIMIENTOS Y GUÍA PASO A PASO: PROYECTO DJANGO CON CRUD E IA (OPENAI / OLLAMA)

Este documento contiene la especificación formal y la secuencia de pasos de ejecución solicitada por el docente e ingeniero para construir, configurar y ejecutar desde cero el sistema de información en Django con operaciones CRUD completas y soporte de Inteligencia Artificial dual (OpenAI API y Ollama Local).

---

## 1. OBJETIVO DEL PROYECTO

Desarrollar una aplicación web robusta con **Django** que permita:
- Administrar un catálogo completo de productos mediante operaciones **CRUD** (Crear, Leer, Actualizar, Eliminar).
- Aplicar validaciones estrictas: unicidad de código/SKU, campos requeridos y valores no negativos en precios y existencias.
- Implementar **borrado lógico** para desactivar productos sin romper el historial relacional.
- Proveer un **control de existencias** dinámico con alertas visuales de stock crítico y agotado.
- Incluir un menú de **8 reportes predefinidos** implementados con el patrón de diseño **Strategy**.
- Integrar un asistente de **Inteligencia Artificial** capaz de responder consultas en lenguaje natural:
  - **Opción A (Requerimiento Ingeniero):** Integración con **OpenAI API** (`gpt-4o-mini` / `gpt-3.5-turbo`) utilizando una clave de API configurada en variables de entorno.
  - **Opción B (Soberanía Local):** Integración con **Ollama** (`invenbot` / `qwen2.5:0.5b`) con inferencia 100% local en CPU sin dependencias externas.

---

## 2. REQUISITOS TÉCNICOS DEL ENTORNO

- **Sistema Operativo:** Linux (Debian 12 / Ubuntu), macOS o Windows 10/11.
- **Intérprete:** Python 3.11+.
- **Framework Web:** Django 5.x.
- **Base de Datos:** SQLite 3 (desarrollo local).
- **Herramientas de IA:** Ollama (local) y/o OpenAI API (nube).
- **Editor:** VSCodium / Visual Studio Code o terminal bash.

---

## 3. PASO 1: CREAR Y ACTIVAR EL AMBIENTE VIRTUAL

En la terminal de Linux (Debian/Ubuntu):

```bash
# Crear el ambiente virtual con Python 3
python3 -m venv venv

# Activar el ambiente virtual en Linux / macOS
source venv/bin/activate
```

En Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

En Windows (Símbolo del sistema CMD):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

---

## 4. PASO 2: ACTUALIZAR PIP

```bash
python -m pip install --upgrade pip
```

---

## 5. PASO 3: INSTALAR DJANGO Y DEPENDENCIAS DEL PROYECTO

Instalar Django y las librerías necesarias para formularios, conexión HTTP, variables de entorno y soporte de IA:

```bash
# Instalación del núcleo web y utilidades
python -m pip install django requests python-dotenv sqlparse asgiref

# Instalación de clientes de Inteligencia Artificial (OpenAI y Ollama)
python -m pip install openai ollama

# Generar archivo de dependencias congeladas
pip freeze > requirements.txt
```

---

## 6. PASO 4: VERIFICAR VERSIÓN DE DJANGO Y CREAR EL PROYECTO

```bash
# Comprobar la instalación de django-admin
django-admin --version

# Crear el proyecto Django en el directorio actual (usar el punto final .)
django-admin startproject chat .

# Crear la aplicación principal para la lógica de inventario y chat
python manage.py startapp ai_chat
```

Estructura de directorios resultante:
```text
proyecto/
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── chat/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── ai_chat/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── signals.py
    ├── urls.py
    ├── views.py
    ├── services/
    │   ├── ollama_service.py
    │   └── report_strategies.py
    └── templates/
        ├── inventario.html
        └── chat.html
```

---

## 7. PASO 5: CONFIGURACIÓN DE `settings.py` Y VARIABLES DE ENTORNO

### 7.1 Archivo de Variables de Entorno (`.env`)

Crear un archivo `.env` en la raíz del proyecto:

```ini
# Configuración general de Django
SECRET_KEY=django-insecure-clave-secreta-de-desarrollo-2026
DEBUG=True

# Configuración del proveedor de Inteligencia Artificial:
# 'ollama' para 100% IA Local
# 'openai' para utilizar la API de OpenAI
IA_PROVIDER=ollama

# Configuración de Ollama Local
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=invenbot

# Configuración de OpenAI (Requerimiento del Ingeniero)
OPENAI_API_KEY=sk-tu-api-key-de-openai-aqui
OPENAI_MODEL=gpt-4o-mini
```

### 7.2 Modificaciones en `chat/settings.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ai_chat',
]

# Configuración de proveedores de IA
IA_PROVIDER = os.getenv('IA_PROVIDER', 'ollama')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'invenbot')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True
```

---

## 8. PASO 6: CREAR LOS MODELOS DE DATOS (`ai_chat/models.py`)

El modelo `Producto` debe contener como mínimo los campos solicitados con sus respectivas validaciones:

```python
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, default='', verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código único / SKU")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del producto")
    descripcion = models.TextField(blank=True, default='', verbose_name="Descripción general")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (Bs.)")
    stock = models.IntegerField(default=0, verbose_name="Cantidad disponible")
    stock_minimo = models.IntegerField(default=5, verbose_name="Stock mínimo de alerta")
    unidad_medida = models.CharField(max_length=50, default='Unidad', verbose_name="Unidad de medida")
    estado = models.BooleanField(default=True, verbose_name="Estado activo")
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name="Fecha de registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def clean(self):
        if self.precio is not None and self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo.'})
        if self.stock is not None and self.stock < 0:
            raise ValidationError({'stock': 'La cantidad existente no puede ser negativa.'})
        if self.stock_minimo is not None and self.stock_minimo < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def estado_stock(self):
        if self.stock <= 0:
            return 'agotado'
        elif self.stock <= self.stock_minimo:
            return 'critico'
        return 'optimo'


class ConsultaIA(models.Model):
    pregunta = models.TextField(verbose_name="Pregunta escrita por el usuario")
    respuesta = models.TextField(verbose_name="Respuesta generada")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de la consulta")
    usuario = models.CharField(max_length=100, default='Usuario')

    class Meta:
        verbose_name = "Consulta IA"
        verbose_name_plural = "Consultas IA"
        ordering = ['-fecha']
```

---

## 9. PASO 7: CREAR Y EJECUTAR MIGRACIONES

```bash
python manage.py makemigrations ai_chat
python manage.py migrate
```

---

## 10. PASO 8: FORMULARIO CON VALIDACIONES ROBUSTAS (`ai_chat/forms.py`)

```python
from django import forms
from django.core.exceptions import ValidationError
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio', 'stock', 'stock_minimo', 'unidad_medida', 'estado']

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if not codigo:
            raise ValidationError('El código es obligatorio.')
        query = Producto.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError(f'El código "{codigo}" ya está registrado.')
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None or precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is None or stock < 0:
            raise ValidationError('La cantidad existente no puede ser negativa.')
        return stock
```

---

## 11. PASO 9: INTEGRACIÓN DE IA DUAL (OPENAI + OLLAMA) MEDIANTE PATRÓN FACTORY

En `ai_chat/services/ollama_service.py` se implementa la fábrica polimórfica que permite ejecutar el proyecto tanto con OpenAI como con Ollama local:

```python
import os, json, requests
from ai_chat.models import ConsultaIA

class OpenAIService:
    """Implementación de IA en la nube mediante OpenAI API."""
    def __init__(self, api_key=None, model='gpt-4o-mini'):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"

    def consultar(self, pregunta, usuario='Usuario'):
        from ai_chat.inventory_service import InventoryService
        es_inv, _, _, resumen = InventoryService.procesar_consulta(pregunta)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": f"Eres InvenBot, asistente de supermercado. Precios en Bs. Datos:\n{resumen}"},
            {"role": "user", "content": pregunta}
        ]
        res = requests.post(self.url, headers=headers, json={"model": self.model, "messages": messages, "max_tokens": 100}, timeout=10)
        texto = res.json()['choices'][0]['message']['content'].strip()
        ConsultaIA.objects.create(pregunta=pregunta, respuesta=texto, usuario=usuario)
        return {'exito': True, 'respuesta': texto, 'modelo': f"OpenAI ({self.model})"}


class OllamaLocalService:
    """Implementación de IA 100% Local mediante Ollama."""
    def __init__(self, base_url="http://localhost:11434", model="invenbot"):
        self.base_url = base_url
        self.model = model

    def consultar(self, pregunta, usuario='Usuario'):
        from ai_chat.inventory_service import InventoryService
        es_inv, _, _, resumen = InventoryService.procesar_consulta(pregunta)
        prompt = f"DATOS:\n{resumen}\n\nPREGUNTA:\n{pregunta}"
        res = requests.post(f"{self.base_url}/api/generate", json={
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "24h",
            "options": {"num_thread": 4, "num_predict": 50, "temperature": 0.1}
        }, timeout=12)
        texto = res.json().get('response', resumen).strip()
        ConsultaIA.objects.create(pregunta=pregunta, respuesta=texto, usuario=usuario)
        return {'exito': True, 'respuesta': texto, 'modelo': self.model}


class AILocalServiceFactory:
    @staticmethod
    def crear_servicio(tipo=None):
        proveedor = (tipo or os.getenv('IA_PROVIDER', 'ollama')).lower()
        if proveedor == 'openai' or os.getenv('OPENAI_API_KEY'):
            return OpenAIService()
        return OllamaLocalService()
```

---

## 12. PASO 10: EJECUCIÓN DE PRUEBAS Y ARRANQUE DEL SERVIDOR

### 12.1 Ejecutar Pruebas Automatizadas

```bash
python manage.py test
```

Salida esperada:
```text
Found 21 test(s).
----------------------------------------------------------------------
Ran 21 tests in 4.8s
OK
```

### 12.2 Crear Superusuario Administrador

```bash
python manage.py createsuperuser
```

### 12.3 Iniciar el Servidor Web

```bash
# Iniciar escuchando en todas las interfaces de red para acceso local y remoto
python manage.py runserver 0.0.0.0:8000
```

URLs de acceso:
- **Gestión de Inventario & Reportes:** `http://localhost:8000/`
- **Asistente de Chat (IA):** `http://localhost:8000/chat/`
- **Panel Administrativo Django:** `http://localhost:8000/admin/`

---

## 13. PROMPT DE REPRODUCCIÓN AUTOMATIZADA PARA OPENCODE / OPENAI

El siguiente texto puede copiarse y enviarse a **OpenCode** o a cualquier modelo de **OpenAI** para generar o verificar el proyecto de forma automática:

```text
Actúa como un desarrollador senior en Python y Django.
Genera un sistema web de información para gestión de inventarios con Django 5.x y SQLite llamado 'chat', con una aplicación llamada 'ai_chat'.

Requerimientos del sistema:
1. Modelo Producto con campos: codigo (único), nombre, descripcion, categoria (FK), precio (Decimal >= 0), stock (Integer >= 0), stock_minimo (Integer >= 0), unidad_medida, estado (Boolean activo/inactivo para borrado lógico), fecha_registro.
2. Modelo ConsultaIA para almacenar historial de interacciones: id, pregunta, respuesta, fecha, usuario.
3. Formulario ProductoForm con validación estricta de no-negativos y unicidad de código.
4. CRUD completo con vistas y plantillas: listar productos, búsqueda en tiempo real por nombre y categoría, modal de nuevo producto, modal de edición, eliminación física y borrado lógico.
5. Control de existencias con botones rápidos para aumentar o disminuir stock (+ / -), impidiendo cantidades negativas.
6. Menú con los 8 reportes predefinidos calculados mediante el Patrón Strategy: todos, más caro, más barato, pocas existencias, agotados, por categoría, valor total y mayor stock.
7. Integración de IA con patrón Factory:
   - Proveedor local mediante Ollama (modelo invenbot con qwen2.5:0.5b).
   - Proveedor opcional mediante OpenAI API (gpt-4o-mini con OPENAI_API_KEY).
8. Chat web con interfaz estilizada: badges de precios en Bs., píldoras de estado de stock (Óptimo, Crítico, Agotado) y tarjetas de producto.
9. Pruebas unitarias completas con TestCase para validaciones, cálculos de reportes e integración de IA.
```
