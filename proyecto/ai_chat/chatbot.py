import os
from django.conf import settings
from ai_chat.models import ChatSession, Message
from ai_chat.inventory_service import InventoryService
import ollama

SYSTEM_PROMPT = (
    "Eres el asistente virtual oficial de inventario del supermercado. "
    "Tu única función es responder preguntas sobre los productos, precios en Bolivianos (Bs.), "
    "categorías y existencias del inventario utilizando estrictamente los datos suministrados. "
    "Responde SIEMPRE en español de forma concisa, clara, directa y estructurada. "
    "No inventes productos, precios ni cantidades que no existan en los datos del sistema."
)

ROLES = {
    'general': SYSTEM_PROMPT,
    'inventario': SYSTEM_PROMPT,
}

class Chatbot:
    def __init__(self, user=None, model=None, session_id=None, role='general'):
        self.user = user or 'Usuario'
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen2.5:0.5b')
        self.session_id = session_id
        self.role = 'inventario'
        self.latency = 0.0

    def get_or_create_session(self):
        session = None
        if self.session_id:
            session = ChatSession.objects.filter(id=self.session_id).first()
        if not session:
            session = ChatSession.objects.create(user=self.user)
            self.session_id = session.id
        return session

    def chatbot(self, prompt, session_id=None, role=None):
        import time
        start_time = time.time()
        try:
            if session_id:
                self.session_id = session_id
            session = self.get_or_create_session()

            # Guardar el mensaje del usuario
            Message.objects.create(
                session=session,
                sender='Usuario',
                message=prompt
            )

            # INTEGRACIÓN MEDIANTE FACTORY PATTERN (IA LOCAL / OLLAMA):
            from ai_chat.services.ollama_service import AILocalServiceFactory
            servicio = AILocalServiceFactory.crear_servicio()
            res_ia = servicio.consultar(prompt, usuario=self.user)
            bot_reply = res_ia.get('respuesta', '')

            # Guardar el mensaje del asistente
            Message.objects.create(
                session=session,
                sender='Asistente',
                message=bot_reply
            )

            self.latency = round(time.time() - start_time, 2)
            if self.latency < 0.1:
                self.latency = 0.1
            return bot_reply

        except Exception as e:
            self.latency = round(time.time() - start_time, 2)
            mensaje_error = f"Lo siento, ocurrió un error al consultar el inventario: {e}"
            return mensaje_error

