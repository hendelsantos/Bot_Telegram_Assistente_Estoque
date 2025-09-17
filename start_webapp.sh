#!/bin/bash
"""
Script para iniciar o servidor WebApp
"""

# Configurações
WEBAPP_DIR="/home/hendel/Documentos/BOTS/Assistente_Stock_MPA"
VENV_PATH="$WEBAPP_DIR/.venv/bin/activate"
SERVER_SCRIPT="$WEBAPP_DIR/server/webapp_server.py"

echo "🚀 Iniciando servidor WebApp..."
echo "📁 Diretório: $WEBAPP_DIR"

# Verificar se ambiente virtual existe
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Ambiente virtual não encontrado em: $VENV_PATH"
    exit 1
fi

# Verificar se servidor existe
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "❌ Servidor não encontrado em: $SERVER_SCRIPT"
    exit 1
fi

# Ativar ambiente virtual e iniciar servidor
cd "$WEBAPP_DIR"
source "$VENV_PATH"

echo "✅ Ambiente virtual ativado"
echo "🌐 Iniciando servidor Flask..."
echo ""
echo "📱 WebApp estará disponível em: http://localhost:8080"
echo "🔗 Para usar no Telegram, use: https://sua-url-publica.com"
echo ""
echo "⏹️  Para parar o servidor, pressione Ctrl+C"
echo ""

python3 "$SERVER_SCRIPT"
