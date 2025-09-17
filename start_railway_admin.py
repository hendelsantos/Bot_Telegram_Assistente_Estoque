#!/usr/bin/env python3
"""
Script de inicialização para Railway - Versão Administrativa
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
    """Configura o ambiente para produção administrativa"""
    print("🚀 Configurando ambiente Railway Administrativo...")
    
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
    
    # Verificar arquivo de admins
    admins_file = 'bot/admins.txt'
    if not os.path.exists(admins_file):
        print("👑 Criando arquivo de administradores...")
        with open(admins_file, 'w') as f:
            f.write('# Adicione os IDs dos administradores aqui, um por linha\n')
    
    print("✅ Ambiente administrativo configurado com sucesso!")

def start_services():
    """Inicia os serviços baseado na variável de ambiente"""
    service = os.environ.get('RAILWAY_SERVICE_NAME', 'admin')
    
    if service == 'admin':
        print("👑 Iniciando Bot Administrativo Railway...")
        os.execv(sys.executable, [sys.executable, 'bot/railway_admin_bot.py'])
    elif service == 'web':
        print("🌐 Iniciando WebApp Server...")
        os.execv(sys.executable, [sys.executable, 'server/webapp_server.py'])
    elif service == 'api':
        print("🔌 Iniciando API REST...")
        os.execv(sys.executable, [sys.executable, 'server/api_ultra_simple.py'])
    else:
        # Padrão: Bot Administrativo
        print("👑 Iniciando Bot Administrativo (padrão)...")
        os.execv(sys.executable, [sys.executable, 'bot/railway_admin_bot.py'])

if __name__ == '__main__':
    setup_environment()
    start_services()
