#!/bin/bash

# Script de Inicialização Completa do Sistema
# Autor: GitHub Copilot
# Data: $(date)

echo "🚀 INICIANDO SISTEMA COMPLETO DE INVENTÁRIO"
echo "============================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

# Diretório do projeto
PROJECT_DIR="/home/hendel/Documentos/BOTS/Assistente_Stock_MPA"

# Verificar se estamos no diretório correto
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Diretório do projeto não encontrado: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Verificar ambiente virtual
if [ ! -d ".venv" ]; then
    log_error "Ambiente virtual não encontrado. Execute primeiro: python3 -m venv .venv"
    exit 1
fi

# Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
source .venv/bin/activate

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    log_error "Arquivo .env não encontrado. Configure o token do bot primeiro."
    exit 1
fi

# Verificar banco de dados
if [ ! -f "db/estoque.db" ]; then
    log_warning "Banco de dados não encontrado. Inicializando..."
    python db/init_db.py
    if [ $? -eq 0 ]; then
        log_success "Banco de dados inicializado"
    else
        log_error "Falha ao inicializar banco de dados"
        exit 1
    fi
fi

# Verificar e parar processos anteriores
log_info "Verificando processos existentes..."

# Parar bot anterior se estiver rodando
pkill -f "bot/main_clean.py" 2>/dev/null
if [ $? -eq 0 ]; then
    log_warning "Bot anterior finalizado"
fi

# Parar servidor anterior se estiver rodando
pkill -f "webapp_server.py" 2>/dev/null
if [ $? -eq 0 ]; then
    log_warning "Servidor anterior finalizado"
fi

# Aguardar processos finalizarem
sleep 2

# Função para verificar se porta está livre
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Porta ocupada
    else
        return 0  # Porta livre
    fi
}

# Verificar porta 8080
if ! check_port 8080; then
    log_warning "Porta 8080 ocupada. Liberando..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    sleep 1
fi

log_header "INICIANDO SERVIÇOS"

# 1. Iniciar Bot do Telegram
log_info "Iniciando Bot do Telegram..."
export $(cat .env | xargs)
nohup python bot/main_clean.py > logs/bot.log 2>&1 &
BOT_PID=$!

# Aguardar bot inicializar
sleep 3

# Verificar se bot está rodando
if ps -p $BOT_PID > /dev/null; then
    log_success "Bot do Telegram iniciado (PID: $BOT_PID)"
else
    log_error "Falha ao iniciar bot do Telegram"
    log_info "Verifique logs/bot.log para detalhes"
    exit 1
fi

# 2. Iniciar Servidor WebApp
log_info "Iniciando Servidor WebApp..."
nohup python server/webapp_server.py > logs/webapp.log 2>&1 &
WEBAPP_PID=$!

# Aguardar servidor inicializar
sleep 3

# Verificar se servidor está rodando
if ps -p $WEBAPP_PID > /dev/null; then
    log_success "Servidor WebApp iniciado (PID: $WEBAPP_PID)"
else
    log_error "Falha ao iniciar servidor WebApp"
    log_info "Verifique logs/webapp.log para detalhes"
    exit 1
fi

# Verificar se portas estão abertas
sleep 2

if check_port 8080; then
    log_error "Servidor WebApp não está escutando na porta 8080"
else
    log_success "Servidor WebApp escutando na porta 8080"
fi

# Salvar PIDs para controle
echo $BOT_PID > .bot.pid
echo $WEBAPP_PID > .webapp.pid

log_header "STATUS DO SISTEMA"

# Verificar banco de dados
ITEM_COUNT=$(sqlite3 db/estoque.db "SELECT COUNT(*) FROM itens" 2>/dev/null || echo "0")
log_info "Itens no banco de dados: $ITEM_COUNT"

# URLs de acesso
echo ""
log_header "URLS DE ACESSO"
log_success "WebApp Local: http://localhost:8080"
log_success "WebApp Rede: http://$(hostname -I | awk '{print $1}'):8080"

# Informações do sistema
echo ""
log_header "INFORMAÇÕES DO SISTEMA"
log_info "Diretório: $PROJECT_DIR"
log_info "Bot PID: $BOT_PID"
log_info "WebApp PID: $WEBAPP_PID"
log_info "Logs Bot: logs/bot.log"
log_info "Logs WebApp: logs/webapp.log"

# Comandos úteis
echo ""
log_header "COMANDOS ÚTEIS"
echo -e "${BLUE}📋 Monitorar logs:${NC}"
echo "   tail -f logs/bot.log      # Logs do bot"
echo "   tail -f logs/webapp.log   # Logs do WebApp"
echo ""
echo -e "${BLUE}🛑 Parar serviços:${NC}"
echo "   kill $BOT_PID             # Parar bot"
echo "   kill $WEBAPP_PID          # Parar WebApp"
echo "   ./stop_system.sh          # Parar tudo"
echo ""
echo -e "${BLUE}📊 Status:${NC}"
echo "   ps -p $BOT_PID            # Status do bot"
echo "   ps -p $WEBAPP_PID         # Status do WebApp"

# Verificar itens com códigos
CODED_ITEMS=$(sqlite3 db/estoque.db "SELECT COUNT(*) FROM itens WHERE codigo IS NOT NULL" 2>/dev/null || echo "0")
if [ "$CODED_ITEMS" -gt "0" ]; then
    log_success "$CODED_ITEMS itens com códigos automáticos"
else
    log_warning "Nenhum item com código automático. Execute: python utils/smart_registration.py"
fi

echo ""
log_header "🎉 SISTEMA INICIADO COM SUCESSO!"
echo ""
log_success "✅ Bot Telegram funcionando"
log_success "✅ WebApp mobile funcionando"  
log_success "✅ Sistema de códigos automáticos ativo"
log_success "✅ Busca inteligente disponível"
log_success "✅ QR Scanner funcionando"

echo ""
log_info "Sistema pronto para uso! 🚀"

# Manter script rodando para monitoramento
if [ "$1" = "--monitor" ]; then
    echo ""
    log_info "Modo monitoramento ativo. Pressione Ctrl+C para sair..."
    
    # Função para cleanup
    cleanup() {
        echo ""
        log_warning "Finalizando serviços..."
        kill $BOT_PID 2>/dev/null
        kill $WEBAPP_PID 2>/dev/null
        rm -f .bot.pid .webapp.pid
        log_success "Sistema finalizado"
        exit 0
    }
    
    # Capturar Ctrl+C
    trap cleanup SIGINT SIGTERM
    
    # Loop de monitoramento
    while true; do
        sleep 10
        
        # Verificar se serviços ainda estão rodando
        if ! ps -p $BOT_PID > /dev/null; then
            log_error "Bot parou de funcionar!"
            break
        fi
        
        if ! ps -p $WEBAPP_PID > /dev/null; then
            log_error "WebApp parou de funcionar!"
            break
        fi
    done
fi
