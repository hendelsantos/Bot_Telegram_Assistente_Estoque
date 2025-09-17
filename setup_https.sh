#!/bin/bash
"""
Script para configurar HTTPS usando ngrok para o WebApp
"""

echo "🌐 Configurando HTTPS para WebApp usando ngrok"
echo "=============================================="

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok não está instalado!"
    echo ""
    echo "📥 Para instalar ngrok:"
    echo "1. Visite: https://ngrok.com/download"
    echo "2. Baixe e instale para seu sistema"
    echo "3. Cadastre-se e configure o authtoken"
    echo ""
    echo "🚀 Instalação rápida (Ubuntu/Debian):"
    echo "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "sudo apt update && sudo apt install ngrok"
    echo ""
    exit 1
fi

echo "✅ ngrok encontrado"

# Verificar se o servidor WebApp está rodando
if ! curl -s http://localhost:8080/api/health > /dev/null; then
    echo "❌ Servidor WebApp não está rodando!"
    echo "🚀 Inicie o servidor primeiro: ./start_webapp.sh"
    exit 1
fi

echo "✅ Servidor WebApp está rodando"

# Iniciar ngrok
echo "🚀 Iniciando ngrok..."
echo "⚠️  IMPORTANTE: Mantenha este terminal aberto!"
echo ""
echo "📋 Após iniciar, você verá algo como:"
echo "   Forwarding: https://abc123.ngrok.io -> http://localhost:8080"
echo ""
echo "🔧 Copie a URL HTTPS e atualize o arquivo .env:"
echo "   WEBAPP_URL=https://abc123.ngrok.io"
echo ""
echo "🔄 Depois reinicie o bot para aplicar a nova URL"
echo ""
echo "⏹️  Para parar: Ctrl+C"
echo ""

# Executar ngrok
ngrok http 8080
