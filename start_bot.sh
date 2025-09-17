#!/bin/bash
"""
Script para iniciar o Bot Telegram com WebApp
"""

# Configurações
WEBAPP_DIR="/home/hendel/Documentos/BOTS/Assistente_Stock_MPA"
VENV_PATH="$WEBAPP_DIR/.venv/bin/activate"
BOT_SCRIPT="$WEBAPP_DIR/bot/main_clean.py"

echo "🤖 Iniciando Bot Telegram com WebApp..."
echo "📁 Diretório: $WEBAPP_DIR"

# Verificar se ambiente virtual existe
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Ambiente virtual não encontrado em: $VENV_PATH"
    exit 1
fi

# Verificar se bot existe
if [ ! -f "$BOT_SCRIPT" ]; then
    echo "❌ Bot não encontrado em: $BOT_SCRIPT"
    exit 1
fi

# Verificar banco de dados
if [ ! -f "$WEBAPP_DIR/db/estoque.db" ]; then
    echo "🗄️  Banco de dados não encontrado! Execute: python3 db/init_db.py"
    exit 1
fi

# Ativar ambiente virtual e iniciar bot
cd "$WEBAPP_DIR"
source "$VENV_PATH"

echo "✅ Ambiente virtual ativado"
echo "🤖 Iniciando bot..."
echo ""
echo "📱 Bot estará disponível no Telegram"
echo "🌐 Certifique-se de que o WebApp esteja rodando em: $WEBAPP_URL"
echo ""
echo "⏹️  Para parar o bot, pressione Ctrl+C"
echo ""

export $(cat .env | xargs)
python3 "$BOT_SCRIPT"
