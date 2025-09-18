#!/usr/bin/env python3
"""
Limpeza Completa do Ambiente do Bot
Este script limpa o ambiente Telegram e mata processos existentes do bot
"""

import os
import sys
import requests
import subprocess
import time
from dotenv import load_dotenv

# Carregar token do arquivo .env
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    print("❌ TOKEN não encontrado no arquivo .env")
    sys.exit(1)

print("🚀 Iniciando limpeza completa do ambiente...")
print(f"🔑 Usando token: {TOKEN[:10]}...")

# 1. Matar processos existentes
print("🔪 Verificando processos do bot...")
try:
    # Encontrar PIDs
    cmd = "ps -ef | grep -E '[p]ython.*bot.*fotos|[p]ython.*bot.*final' | awk '{print $2}'"
    output = subprocess.check_output(cmd, shell=True).decode().strip()
    
    if output:
        pids = output.split('\n')
        print(f"⚠️ Encontrados {len(pids)} processos rodando. Terminando...")
        
        for pid in pids:
            try:
                pid = int(pid.strip())
                os.kill(pid, 15)  # SIGTERM
                print(f"✅ Processo {pid} terminado.")
            except Exception as e:
                print(f"⚠️ Erro ao terminar processo {pid}: {e}")
        
        # Esperar um pouco para os processos terminarem
        time.sleep(2)
    else:
        print("✅ Nenhum processo do bot em execução.")
except Exception as e:
    print(f"⚠️ Erro ao verificar processos: {e}")

# 2. Remover arquivos de lock
print("🔓 Removendo arquivos de lock...")
try:
    lock_files = [
        "/tmp/assistente_estoque_bot.lock",
        "/tmp/assistente_estoque_bot.pid"
    ]
    
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print(f"✅ Arquivo removido: {lock_file}")
        else:
            print(f"ℹ️ Arquivo não existe: {lock_file}")
except Exception as e:
    print(f"⚠️ Erro ao remover arquivos de lock: {e}")

# 3. Limpar sessão do Telegram
print("🧹 Limpando sessão do Telegram...")
try:
    # URL para limpar o webhook
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
    response = requests.get(url)
    result = response.json()
    
    if result.get("ok"):
        print("✅ Webhook removido com sucesso!")
        print("✅ Updates pendentes descartadas!")
    else:
        print(f"❌ Erro: {result.get('description', 'Desconhecido')}")
    
    # Aguardar para garantir que o Telegram atualizou seu estado
    time.sleep(1)
except Exception as e:
    print(f"❌ Erro ao conectar à API do Telegram: {e}")

print("✨ Limpeza concluída! O ambiente está pronto para iniciar um novo bot.")
