#!/usr/bin/env python3
"""
Script de inicialização para Railway
Configura o ambiente e inicia os serviços
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def setup_environment():
    """Configura o ambiente para produção"""
    print("🚀 Configurando ambiente Railway...")
    
    # Criar diretórios necessários
    os.makedirs('db', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('fotos', exist_ok=True)
    os.makedirs('inventarios', exist_ok=True)
    
    # Inicializar banco se não existir
    db_path = 'db/estoque.db'
    if not os.path.exists(db_path):
        print("📦 Inicializando banco de dados...")
        subprocess.run([sys.executable, 'db/init_db.py'], check=True)
    
    print("✅ Ambiente configurado com sucesso!")

def start_services():
    """Inicia os serviços baseado na variável de ambiente"""
    service = os.environ.get('RAILWAY_SERVICE_NAME', 'web')
    
    if service == 'web':
        print("🌐 Iniciando WebApp Server...")
        os.execv(sys.executable, [sys.executable, 'server/webapp_server.py'])
    elif service == 'bot':
        print("🤖 Iniciando Telegram Bot (Railway Simple)...")
        os.execv(sys.executable, [sys.executable, 'bot/railway_bot_simple.py'])
    else:
        # Padrão: apenas WebApp
        print("🌐 Iniciando WebApp Server (padrão)...")
        os.execv(sys.executable, [sys.executable, 'server/webapp_server.py'])

if __name__ == '__main__':
    setup_environment()
    start_services()
