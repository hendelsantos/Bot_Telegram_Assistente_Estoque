# 🚂 Deploy no Railway

## Configuração Rápida

### 1. Conectar Repositório
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha este repositório

### 2. Configurar Variáveis de Ambiente
No painel do Railway, vá em "Variables" e adicione:

```
TELEGRAM_BOT_TOKEN=SEU_TOKEN_AQUI
RAILWAY_SERVICE_NAME=bot
WEBAPP_URL=https://seu-projeto.railway.app
```

### 3. Deploy Automático
O Railway irá detectar automaticamente:
- `railway.toml` - Configuração de build e deploy
- `requirements-railway.txt` - Dependências Python simplificadas
- `start_railway.py` - Script de inicialização

## Arquivos Específicos do Railway

### Bot Simplificado
- `bot/railway_bot_simple.py` - Versão sem dependências problemáticas
- Remove funcionalidades que requerem bibliotecas pesadas (QR code, pyzbar)
- Mantém todas as funcionalidades essenciais do bot

### Configuração
- `railway.toml` - Build e deploy
- `requirements-railway.txt` - Dependências simplificadas
- `start_railway.py` - Inicialização com configuração de ambiente

## Funcionalidades Disponíveis no Railway

### ✅ Bot Telegram
- `/start` - Iniciar bot
- `/menu` - Menu interativo
- `/buscar` - Buscar itens
- `/relatorio` - Relatório do estoque
- `/webapp` - Interface web (requer HTTPS)

### ✅ WebApp
- Interface completa via navegador
- Gestão de estoque
- Relatórios

### ✅ API REST
- 12 endpoints completos
- Autenticação JWT
- Rate limiting

## Limitações no Railway

### ❌ Removidas
- Leitura de QR Code (pyzbar não suportado)
- Algumas dependências pesadas

### ⚠️ WebApp Telegram
- Requer URL HTTPS do Railway
- Configure `WEBAPP_URL` com sua URL de produção

## Monitoramento

O Railway fornece:
- Logs em tempo real
- Métricas de uso
- Auto-restart em falhas

## Comandos de Debug

Para verificar se está funcionando:
```bash
# Verificar logs
railway logs

# Verificar variáveis
railway variables

# Restart manual
railway restart
```

## Suporte

- ✅ Python 3.12
- ✅ SQLite (banco local)
- ✅ Telegram Bot API
- ✅ Flask WebApp
- ✅ API REST completa

---

**Versão:** v2.2.0  
**Última atualização:** $(date +%d/%m/%Y)
