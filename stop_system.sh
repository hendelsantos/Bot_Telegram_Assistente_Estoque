#!/bin/bash

# Script para parar todos os serviços do sistema
# Autor: GitHub Copilot
# Data: $(date)

echo "🛑 PARANDO SISTEMA DE INVENTÁRIO"
echo "================================"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

PROJECT_DIR="/home/hendel/Documentos/BOTS/Assistente_Stock_MPA"
cd "$PROJECT_DIR" 2>/dev/null || {
    echo "Não foi possível acessar o diretório do projeto"
    exit 1
}

# Parar por PID se existir
if [ -f ".bot.pid" ]; then
    BOT_PID=$(cat .bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        kill $BOT_PID
        log_success "Bot finalizado (PID: $BOT_PID)"
    fi
    rm -f .bot.pid
fi

if [ -f ".webapp.pid" ]; then
    WEBAPP_PID=$(cat .webapp.pid)
    if ps -p $WEBAPP_PID > /dev/null 2>&1; then
        kill $WEBAPP_PID
        log_success "WebApp finalizado (PID: $WEBAPP_PID)"
    fi
    rm -f .webapp.pid
fi

# Parar processos por nome
log_info "Finalizando processos Python relacionados..."

pkill -f "bot/main_clean.py" 2>/dev/null && log_success "Bot finalizado por nome"
pkill -f "webapp_server.py" 2>/dev/null && log_success "WebApp finalizado por nome"

# Liberar portas se necessário
log_info "Liberando porta 8080..."
lsof -ti:8080 | xargs kill -9 2>/dev/null && log_warning "Processo na porta 8080 finalizado"

# Aguardar finalização
sleep 2

# Verificar se ainda há processos rodando
REMAINING_BOT=$(pgrep -f "bot/main_clean.py" | wc -l)
REMAINING_WEBAPP=$(pgrep -f "webapp_server.py" | wc -l)

if [ "$REMAINING_BOT" -eq "0" ] && [ "$REMAINING_WEBAPP" -eq "0" ]; then
    log_success "Todos os serviços foram finalizados com sucesso!"
else
    log_warning "Alguns processos podem ainda estar rodando"
    if [ "$REMAINING_BOT" -gt "0" ]; then
        echo "   Bot: $REMAINING_BOT processo(s)"
    fi
    if [ "$REMAINING_WEBAPP" -gt "0" ]; then
        echo "   WebApp: $REMAINING_WEBAPP processo(s)"
    fi
fi

echo ""
log_info "Sistema parado. Para reiniciar use: ./start_system.sh"
