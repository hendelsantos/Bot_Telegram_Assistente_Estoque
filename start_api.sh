#!/bin/bash
"""
Script para iniciar a API REST
"""

echo "🚀 Iniciando API REST do Sistema de Estoque..."

# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências se necessário
pip install requests PyJWT

# Iniciar API
echo "📡 API será iniciada em http://localhost:5000"
echo "📚 Documentação: http://localhost:5000/api/v1/docs"
echo ""

python server/api_rest.py
