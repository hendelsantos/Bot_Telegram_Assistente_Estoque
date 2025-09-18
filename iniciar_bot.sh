#!/bin/bash
# Script de inicialização do Bot Assistente de Estoque com FOTOS
# Este script garante a inicialização correta do bot sem conflitos

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Caminho para o diretório do bot
BOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $BOT_DIR

# Exibir cabeçalho
echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}🚀 INICIANDO BOT ASSISTENTE DE ESTOQUE COM FOTOS${NC}"
echo -e "${BLUE}==============================================${NC}"
echo

# 1. Verificar ambiente virtual
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado. Criando...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Ambiente virtual criado com sucesso!${NC}"
fi

# 2. Ativar ambiente virtual
echo -e "${BLUE}🔄 Ativando ambiente virtual...${NC}"
source .venv/bin/activate

# 3. Verificar dependências
echo -e "${BLUE}📦 Verificando dependências...${NC}"
pip install python-telegram-bot>=20.0 python-dotenv aiosqlite pandas > /dev/null 2>&1
echo -e "${GREEN}✅ Dependências verificadas!${NC}"

# 4. Limpar sessão anterior
echo -e "${YELLOW}🧹 Limpando sessão anterior do bot...${NC}"
python bot/clear_telegram.py > /dev/null 2>&1

# 5. Verificar arquivo de configuração
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    echo -e "${YELLOW}🔧 Criando arquivo .env de exemplo...${NC}"
    echo "TELEGRAM_BOT_TOKEN=seu_token_aqui" > .env
    echo -e "${RED}⚠️  ATENÇÃO: Edite o arquivo .env e adicione seu token!${NC}"
    exit 1
fi

# 6. Inicializar banco de dados
echo -e "${BLUE}🗄️  Verificando banco de dados...${NC}"
python db/init_db.py > /dev/null 2>&1
echo -e "${GREEN}✅ Banco de dados inicializado!${NC}"

# 7. Iniciar o bot
echo -e "${GREEN}🚀 Iniciando o bot...${NC}"
echo -e "${YELLOW}💻 Log será exibido abaixo. Pressione Ctrl+C para encerrar.${NC}"
echo -e "${BLUE}==============================================${NC}"
echo

# Executar o bot
python bot/bot_final.py
