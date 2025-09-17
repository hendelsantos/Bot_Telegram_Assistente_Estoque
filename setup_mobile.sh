#!/bin/bash
# Script melhorado para configurar HTTPS para celulares

echo "📱 Configurando WebApp para Android e iPhone"
echo "============================================="

# Verificar se o servidor está rodando
if ! curl -s http://localhost:8080/api/health > /dev/null; then
    echo "❌ Servidor WebApp não está rodando!"
    echo "🚀 Execute primeiro: ./start_webapp.sh"
    echo ""
    read -p "Deseja iniciar o servidor agora? (s/n): " resposta
    if [[ $resposta == "s" || $resposta == "S" ]]; then
        echo "🚀 Iniciando servidor..."
        ./start_webapp.sh &
        SERVER_PID=$!
        echo "⏳ Aguardando servidor inicializar..."
        sleep 5
        
        if ! curl -s http://localhost:8080/api/health > /dev/null; then
            echo "❌ Falha ao iniciar servidor!"
            exit 1
        fi
        echo "✅ Servidor iniciado!"
    else
        exit 1
    fi
fi

echo "✅ Servidor WebApp está rodando"

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo ""
    echo "📥 ngrok não está instalado! Opções para instalar:"
    echo ""
    echo "1️⃣  Snap (Ubuntu/Linux):"
    echo "   sudo snap install ngrok"
    echo ""
    echo "2️⃣  Download direto:"
    echo "   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
    echo "   tar xvzf ngrok-v3-stable-linux-amd64.tgz"
    echo "   sudo cp ngrok /usr/local/bin"
    echo ""
    echo "3️⃣  Site oficial: https://ngrok.com/download"
    echo ""
    read -p "Tentar instalar via snap? (s/n): " install_snap
    
    if [[ $install_snap == "s" || $install_snap == "S" ]]; then
        echo "📦 Instalando ngrok via snap..."
        sudo snap install ngrok
        if [ $? -eq 0 ]; then
            echo "✅ ngrok instalado com sucesso!"
        else
            echo "❌ Falha na instalação. Tente manualmente."
            exit 1
        fi
    else
        echo "ℹ️  Instale ngrok manualmente e execute este script novamente."
        exit 1
    fi
fi

echo "✅ ngrok encontrado"

# Verificar se ngrok está autenticado
if ! ngrok config check &> /dev/null; then
    echo ""
    echo "🔑 ngrok precisa ser autenticado:"
    echo "1. Acesse: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Copie seu authtoken"
    echo "3. Execute: ngrok config add-authtoken SEU_TOKEN_AQUI"
    echo ""
    read -p "Cole seu authtoken aqui: " authtoken
    
    if [[ -n "$authtoken" ]]; then
        ngrok config add-authtoken "$authtoken"
        echo "✅ Authtoken configurado!"
    else
        echo "❌ Token inválido!"
        exit 1
    fi
fi

echo ""
echo "🚀 Iniciando túnel HTTPS..."
echo "📱 Isso permitirá acesso do Telegram em celulares!"
echo ""
echo "📋 Quando o túnel iniciar, você verá:"
echo "   Forwarding: https://abc123.ngrok.io -> http://localhost:8080"
echo ""
echo "🔧 IMPORTANTE: Copie a URL HTTPS e:"
echo "   1. Atualize o arquivo .env: WEBAPP_URL=https://abc123.ngrok.io"
echo "   2. Reinicie o bot: Ctrl+C no bot e execute ./start_bot.sh"
echo "   3. No Telegram: /webapp ou Menu -> WebApp"
echo ""
echo "⏹️  Para parar: Ctrl+C"
echo ""

# Executar ngrok
ngrok http 8080
