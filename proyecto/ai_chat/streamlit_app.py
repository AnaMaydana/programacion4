import os
import sys
import numpy as np
import streamlit as st
import django

# Añadir el directorio base del proyecto al path de Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat.settings')
django.setup()

from ai_chat.chatbot import Chatbot
from ai_chat.models import ChatSession, Message

# Configuración de página
st.set_page_config(
    page_title='¡Chatea Conmigo! - Chatbot IA',
    page_icon='🤖',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Inyección de estilos CSS para máxima pulcritud y fidelidad a la estética original
st.markdown("""
<style>
    /* Tipografía y fondo principal */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', system-ui, -apple-system, sans-serif;
    }

    /* Fondo general */
    .stApp {
        background-color: #0e1117;
        color: #f8fafc;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #161922 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Botones de la barra lateral */
    section[data-testid="stSidebar"] .stButton > button {
        background: #1f232d !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #2a303d !important;
        border-color: rgba(255, 75, 75, 0.4) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }

    /* Botón Nueva Conversación (Primary) */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .btn-new-chat button {
        background: linear-gradient(135deg, #ff4b4b, #e03535) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3) !important;
        justify-content: center !important;
        text-align: center !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ff6363, #eb3e3e) !important;
        box-shadow: 0 6px 16px rgba(255, 75, 75, 0.45) !important;
    }

    /* Título principal */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .subtitle-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.82rem;
        color: #94a3b8;
        margin-bottom: 24px;
    }

    .badge-pill {
        background: rgba(255, 75, 75, 0.12);
        color: #ff6b6b;
        border: 1px solid rgba(255, 75, 75, 0.25);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.75rem;
    }

    /* Contenedor de Mensajes de Chat */
    [data-testid="stChatMessage"] {
        background-color: #161922 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        transition: border-color 0.2s ease !important;
    }

    [data-testid="stChatMessage"]:hover {
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Mensaje del usuario con toque cálido/rojo sutil */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #1a1e29 !important;
        border-left: 3px solid #ff4b4b !important;
    }

    /* Avatar del usuario original (rojo con smiley) */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #ff4b4b !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }

    /* Avatar del asistente (estilo original badge 'B') */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #262730 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        font-weight: 700 !important;
    }

    /* Campo de entrada de texto inferior */
    [data-testid="stChatInput"] {
        border-radius: 24px !important;
        background-color: #1e222d !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de variables de estado
if 'user' not in st.session_state:
    st.session_state.user = f'Usuario_{np.random.randint(1000, 9999)}'

if 'session_id' not in st.session_state:
    st.session_state.session_id = None

if 'history' not in st.session_state:
    st.session_state.history = []

# ==========================================
# BARRA LATERAL (100% en Español)
# ==========================================
with st.sidebar:
    st.title('Sesiones de Chat')

    if st.button('➕ Nueva Conversación', type='primary', use_container_width=True):
        nueva = ChatSession.objects.create(user=st.session_state.user)
        st.session_state.session_id = nueva.id
        st.session_state.history = []
        st.rerun()

    st.markdown('---------')
    st.markdown('### **Conversaciones Anteriores**')

    # Cargar sesiones desde la base de datos
    sesiones_db = ChatSession.objects.order_by('-created_at')[:20]
    
    if not sesiones_db.exists():
        st.caption('Aún no hay conversaciones anteriores.')
    else:
        for s in sesiones_db:
            es_activa = (st.session_state.session_id == s.id)
            titulo = s.title if len(s.title) <= 28 else s.title[:28] + '...'
            icono = "👉 " if es_activa else ""
            etiqueta = f"{icono}{titulo}"
            
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(etiqueta, key=f'sesion_{s.id}', use_container_width=True):
                    st.session_state.session_id = s.id
                    st.session_state.history = [
                        (m.sender, m.message) for m in s.message.order_by('timestamp')
                    ]
                    st.rerun()
            with col2:
                if st.button('🗑️', key=f'del_{s.id}', help='Eliminar conversación'):
                    if st.session_state.session_id == s.id:
                        st.session_state.session_id = None
                        st.session_state.history = []
                    s.delete()
                    st.rerun()

    st.markdown('---')
    st.markdown('### **Rol / Personalidad**')
    opciones_roles = {
        'general': 'Asistente General',
        'programador': 'Experto Python y Django',
        'corrector': 'Corrector y Redactor',
        'tutor': 'Tutor Didáctico'
    }
    rol_elegido = st.selectbox(
        'Personalidad del modelo:',
        options=list(opciones_roles.keys()),
        format_func=lambda x: opciones_roles[x],
        index=0,
        label_visibility='collapsed'
    )

    if len(st.session_state.history) > 0:
        st.markdown('### **Exportar Conversación**')
        texto_export = f"Conversación ID: {st.session_state.session_id or 'Nueva'}\n"
        texto_export += f"Rol: {opciones_roles.get(rol_elegido, 'General')}\n"
        texto_export += "=" * 40 + "\n\n"
        for sdr, m in st.session_state.history:
            texto_export += f"[{sdr}]:\n{m}\n\n" + ("-" * 30) + "\n\n"
        st.download_button(
            label="Descargar Chat (.txt)",
            data=texto_export,
            file_name=f"conversacion_{st.session_state.session_id or 'activa'}.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.markdown('---')
    st.caption('**Red Local:** `172.25.4.228/25`')
    st.caption('**Modelo:** `qwen2.5:0.5b` (Ollama)')
    st.caption('[Abrir versión Django](http://172.25.4.228:8000/)')

# ==========================================
# ÁREA PRINCIPAL DE CHAT
# ==========================================
st.markdown('<div class="main-title">¡Chatea Conmigo!</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle-badge">'
    '<span class="badge-pill">IA LOCAL</span> '
    'Ejecutándose en tu servidor privado • Respuestas en español'
    '</div>', 
    unsafe_allow_html=True
)

# Plantillas dinámicas por rol
PLANTILLAS_ROLES = {
    'general': [
        ('💡 Fondo de cobertura', '¿Qué es un fondo de cobertura (Hedge Fund) y cómo funciona?'),
        ('🌐 Subred 172.25.4.228', 'Explícame cómo funciona la subred 172.25.4.228/25 en redes locales.'),
        ('🧠 Capacidades de IA', '¿Qué capacidades y ventajas tienes como modelo de lenguaje local?'),
        ('🛡️ Seguridad en Django', 'Dame 3 consejos de seguridad esenciales para servidores Django.'),
    ],
    'programador': [
        ('🐍 Función Python', 'Escribe una función en Python con tipado estricto, docstring y manejo de excepciones.'),
        ('🛡️ Seguridad Django', 'Dame 4 recomendaciones de seguridad esenciales para producción en Django.'),
        ('🐞 Depurar código', 'Explica cómo depurar eficazmente una excepción en Django y ver el stack trace.'),
        ('⚡ Optimizar ORM', '¿Cómo optimizo consultas en Django ORM con select_related y prefetch_related?'),
    ],
    'corrector': [
        ('🔍 Corregir texto', 'Corrige la ortografía y puntuación del siguiente texto: "Los muchachos desidieron hir al parque pero no avian llebado nada".'),
        ('👔 Redactar formal', 'Reescribe una solicitud de reunión de trabajo para que tenga un tono formal y profesional.'),
        ('✨ Mejorar fluidez', 'Mejora la redacción y claridad de un párrafo de presentación académica.'),
        ('📧 Correo formal', 'Redacta un correo electrónico formal solicitando información sobre un proyecto de software.'),
    ],
    'tutor': [
        ('🧩 Explicar con analogía', 'Explícame qué es una API usando una analogía cotidiana de un restaurante.'),
        ('❓ Mini cuestionario', 'Hazme 3 preguntas breves tipo test para evaluar conceptos básicos de programación.'),
        ('🪜 Paso a paso', 'Explícame paso a paso cómo viaja una petición HTTP desde el navegador al servidor.'),
        ('🎯 Ejercicio guiado', 'Plantéame un ejercicio básico sobre listas y bucles en Python con una pista.'),
    ],
}

# Estado inicial vacío: sugerencias dinámicas según la plantilla elegida
if len(st.session_state.history) == 0:
    st.info(f'👋 ¡Hola! Personalidad activa: **{opciones_roles.get(rol_elegido, "General")}**. Selecciona una plantilla o escribe tu consulta:')
    sugerencias_rol = PLANTILLAS_ROLES.get(rol_elegido, PLANTILLAS_ROLES['general'])
    col_a, col_b = st.columns(2)
    sugerencia_seleccionada = None
    with col_a:
        if st.button(sugerencias_rol[0][0], key='sug_1', use_container_width=True, help=sugerencias_rol[0][1]):
            sugerencia_seleccionada = sugerencias_rol[0][1]
        if st.button(sugerencias_rol[1][0], key='sug_2', use_container_width=True, help=sugerencias_rol[1][1]):
            sugerencia_seleccionada = sugerencias_rol[1][1]
    with col_b:
        if st.button(sugerencias_rol[2][0], key='sug_3', use_container_width=True, help=sugerencias_rol[2][1]):
            sugerencia_seleccionada = sugerencias_rol[2][1]
        if st.button(sugerencias_rol[3][0], key='sug_4', use_container_width=True, help=sugerencias_rol[3][1]):
            sugerencia_seleccionada = sugerencias_rol[3][1]
    
    if sugerencia_seleccionada:
        st.session_state.history.append(('Usuario', sugerencia_seleccionada))
        bot = Chatbot(user=st.session_state.user, session_id=st.session_state.session_id, role=rol_elegido)
        with st.spinner('Pensando la respuesta...'):
            respuesta = bot.chatbot(sugerencia_seleccionada, session_id=st.session_state.session_id, role=rol_elegido)
            st.session_state.session_id = bot.session_id
        st.session_state.history.append(('Bot', respuesta))
        st.rerun()

# Mostrar historial de mensajes (Con los avatares originales exactos de mini_gpt.jpg)
for sender, msg in st.session_state.history:
    if sender in ['User', 'Usuario', 'user']:
        # Avatar nativo de usuario de Streamlit (el icono rojo sonriente de mini_gpt.jpg)
        with st.chat_message("user"):
            st.markdown(msg)
    else:
        # Avatar 'B' idéntico al que muestra mini_gpt.jpg
        with st.chat_message("assistant", avatar="B"):
            st.markdown(msg)

# Entrada de texto del usuario
user_input = st.chat_input('Escribe tu mensaje aquí...')

if user_input:
    # Añadir visualmente mensaje del usuario
    st.session_state.history.append(('Usuario', user_input))

    # Instanciar chatbot con la sesión actual
    bot = Chatbot(user=st.session_state.user, session_id=st.session_state.session_id, role=rol_elegido)
    with st.spinner('Pensando la respuesta...'):
        respuesta = bot.chatbot(user_input, session_id=st.session_state.session_id, role=rol_elegido)
        st.session_state.session_id = bot.session_id

    # Añadir respuesta del bot
    st.session_state.history.append(('Bot', respuesta))
    st.rerun()
