#!/bin/bash
# ==============================================================================
# Script de inicio para el Chatbot IA sobre la red 172.25.4.228/25
# ==============================================================================

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ No se encontró el entorno virtual 'venv'."
    exit 1
fi

IP_RED="172.25.4.228"
PUERTO_DJANGO="8000"
PUERTO_STREAMLIT="8501"

echo "============================================================"
echo " 🤖 Iniciando Chatbot IA en Español"
echo " 🌐 Subred: 172.25.4.228/25"
echo " 🔗 Acceso Django:    http://${IP_RED}:${PUERTO_DJANGO}/"
echo " 🔗 Acceso Streamlit: http://${IP_RED}:${PUERTO_STREAMLIT}/"
echo "============================================================"

if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  ADVERTENCIA: El servicio local de Ollama no responde en el puerto 11434."
    echo "    Asegúrate de iniciarlo con: systemctl start ollama"
else
    echo "✅ Servicio Ollama detectado. Precalentando modelo invenbot en RAM..."
    curl -s http://localhost:11434/api/generate -d '{"model": "invenbot", "keep_alive": "24h"}' > /dev/null 2>&1 &
fi

# Parámetro opcional:
# ./iniciar_servidor.sh django      -> Solo Django
# ./iniciar_servidor.sh streamlit   -> Solo Streamlit
# ./iniciar_servidor.sh             -> Inicia Django y Streamlit juntos

MODO="${1:-ambos}"

if [ "$MODO" = "django" ]; then
    echo "Iniciando solo servidor Django en 0.0.0.0:${PUERTO_DJANGO}..."
    python manage.py runserver 0.0.0.0:${PUERTO_DJANGO}
elif [ "$MODO" = "streamlit" ]; then
    echo "Iniciando solo servidor Streamlit en 0.0.0.0:${PUERTO_STREAMLIT}..."
    streamlit run ai_chat/streamlit_app.py \
        --server.address 0.0.0.0 \
        --server.port ${PUERTO_STREAMLIT} \
        --server.enableCORS false \
        --server.enableXsrfProtection false
else
    echo "Iniciando Streamlit en segundo plano..."
    streamlit run ai_chat/streamlit_app.py \
        --server.address 0.0.0.0 \
        --server.port ${PUERTO_STREAMLIT} \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.headless true > /dev/null 2>&1 &
    STREAMLIT_PID=$!

    # Detener Streamlit cuando termine el script
    trap "kill $STREAMLIT_PID 2>/dev/null" EXIT

    echo "Iniciando servidor Django principal en 0.0.0.0:${PUERTO_DJANGO}..."
    python manage.py runserver 0.0.0.0:${PUERTO_DJANGO}
fi
