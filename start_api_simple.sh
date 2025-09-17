#!/bin/bash

echo "🚀 Iniciando API REST - Sistema de Estoque"
echo "=========================================="

# Verificar se o Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    exit 1
fi

# Verificar se o diretório existe
if [ ! -f "server/api_rest_simple.py" ]; then
    echo "❌ Arquivo api_rest_simple.py não encontrado!"
    echo "Execute este script do diretório raiz do projeto"
    exit 1
fi

# Criar diretório db se não existir
mkdir -p db

# Verificar dependências
echo "📦 Verificando dependências..."
python3 -c "import flask, flask_cors, sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Instalando dependências..."
    pip3 install flask flask-cors
fi

# Iniciar API
echo "🔥 Iniciando API na porta 5000..."
echo "📚 Documentação: http://localhost:5000/api/v1/"
echo "🔗 Endpoints disponíveis:"
echo "  - GET  /api/v1/items           (Listar itens)"
echo "  - POST /api/v1/items           (Criar item)"
echo "  - GET  /api/v1/items/{code}    (Item específico)"
echo "  - PUT  /api/v1/items/{code}    (Atualizar item)"
echo "  - DELETE /api/v1/items/{code}  (Deletar item)"
echo "  - GET  /api/v1/items/search    (Buscar itens)"
echo "  - GET  /api/v1/categories      (Listar categorias)"
echo "  - GET  /api/v1/reports/dashboard (Dashboard)"
echo ""
echo "🔑 Use o header: X-API-Key: test-key-123"
echo ""
echo "Para parar a API: Ctrl+C"
echo "=========================================="

cd server
python3 api_rest_simple.py
