#!/bin/bash
"""
Script para testar o sistema completo - Bot + WebApp
"""

echo "🧪 Script de Teste Completo - Bot + WebApp"
echo "=========================================="

# Configurações
PROJECT_DIR="/home/hendel/Documentos/BOTS/Assistente_Stock_MPA"
VENV_PATH="$PROJECT_DIR/.venv/bin/activate"

# Verificar ambiente virtual
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    exit 1
fi

cd "$PROJECT_DIR"
source "$VENV_PATH"

echo "✅ Ambiente virtual ativado"

# Verificar banco de dados
if [ ! -f "db/estoque.db" ]; then
    echo "🗄️  Criando banco de dados..."
    python3 db/init_db.py
fi

echo "✅ Banco de dados verificado"

# Verificar dependências
echo "📦 Verificando dependências..."
python3 -c "import flask, flask_cors, telegram, aiosqlite" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Todas as dependências estão instaladas"
else
    echo "❌ Faltam dependências!"
    exit 1
fi

# Testar servidor WebApp em background
echo "🌐 Testando servidor WebApp..."
python3 server/webapp_server.py &
SERVER_PID=$!

# Aguardar servidor inicializar
sleep 3

# Testar se servidor está respondendo
curl -s http://localhost:8080/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Servidor WebApp funcionando"
else
    echo "❌ Servidor WebApp não está respondendo"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Parar servidor
kill $SERVER_PID 2>/dev/null
echo "🛑 Servidor WebApp parado"

echo ""
echo "🎉 Teste completo realizado com sucesso!"
echo ""
echo "Para usar o sistema:"
echo "1. 🚀 Inicie o WebApp: ./start_webapp.sh"
echo "2. 🤖 Em outro terminal, inicie o bot: ./start_bot.sh"
echo "3. 📱 Use /webapp no Telegram para abrir o scanner QR"
echo ""
echo "🔗 URLs importantes:"
echo "   • WebApp: http://localhost:8080"
echo "   • API Health: http://localhost:8080/api/health"
echo "   • API Stats: http://localhost:8080/api/stats"
