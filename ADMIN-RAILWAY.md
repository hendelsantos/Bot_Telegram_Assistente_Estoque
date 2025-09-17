# 👑 Bot Administrativo Railway

## Versão Completa com Funcionalidades Administrativas

### 🎯 Objetivo
Esta versão permite gerenciar completamente o estoque via Telegram, incluindo:
- ✅ Cadastro de novos itens
- ✅ Edição de itens existentes
- ✅ Gerenciamento de administradores
- ✅ Backup do banco de dados
- ✅ Relatórios detalhados
- ✅ Controle de acesso por usuário

---

## 🚀 Deploy no Railway

### 1. Configuração Inicial
```bash
# Clonar o repositório
git clone https://github.com/hendelsantos/Bot_Telegram_Assistente_Estoque.git
cd Bot_Telegram_Assistente_Estoque
```

### 2. Railway Setup
1. **Conectar repositório** no Railway
2. **Usar configuração administrativa:**
   - Arquivo: `railway-admin.toml`
   - Script: `start_railway_admin.py`
   - Bot: `bot/railway_admin_bot.py`

### 3. Variáveis de Ambiente
```
TELEGRAM_BOT_TOKEN=seu_token_do_telegram
RAILWAY_SERVICE_NAME=admin
WEBAPP_URL=https://seu-projeto.railway.app
```

---

## 👑 Sistema de Administração

### Primeiro Acesso
1. **Envie `/start`** para o bot
2. **Automaticamente** você se torna o primeiro admin
3. **Configure outros admins** via `/admin_menu`

### Arquivo de Admins
- Localização: `bot/admins.txt`
- Formato: Um ID de usuário por linha
- **Como obter ID:** Envie mensagem para `@userinfobot`

---

## 📋 Comandos Administrativos

### Menu Principal
```
/start          - Iniciar bot
/menu           - Menu geral
/admin_menu     - Menu administrativo (somente admins)
```

### Gestão de Estoque
```
/novo_item      - Cadastrar novo item
/editar_item    - Editar item existente
/buscar <termo> - Buscar itens
/relatorio      - Relatório completo
```

### Funcionalidades Admin
```
/admin_users    - Gerenciar administradores
/backup         - Backup do banco de dados
/webapp         - Interface web completa
```

---

## 🔧 Funcionalidades Detalhadas

### ➕ Cadastro de Itens
**Comando:** `/novo_item`

**Fluxo:**
1. Nome do item
2. Descrição detalhada
3. Quantidade inicial
4. Confirmação automática

**Exemplo:**
```
/novo_item
> Nome: Notebook Dell XPS 13
> Descrição: Notebook Dell XPS 13, Intel i7, 16GB RAM, 512GB SSD
> Quantidade: 5
✅ Item cadastrado com sucesso!
```

### 🔍 Busca Avançada
**Comando:** `/buscar <termo>`

**Recursos:**
- Busca por nome e descrição
- Até 10 resultados
- Status do item (ativo/inativo)
- Informações completas

**Exemplo:**
```
/buscar notebook
🔍 Resultados para: notebook
✅ Notebook Dell XPS 13
   📝 Notebook Dell XPS 13, Intel i7...
   📦 Quantidade: 5
   🆔 ID: 123
```

### 📊 Relatórios
**Comando:** `/relatorio`

**Inclui:**
- Total de itens cadastrados
- Itens ativos
- Quantidade total em estoque
- Alertas de estoque baixo
- Últimos itens cadastrados

### 💾 Backup
**Comando:** Via menu administrativo

**Funcionalidades:**
- Exportação completa do banco
- Formato JSON estruturado
- Data/hora do backup
- Contagem de itens

---

## 🔐 Controle de Acesso

### Níveis de Usuário

#### 👤 Usuário Comum
- Buscar itens
- Ver relatórios
- Acessar WebApp (visualização)

#### 👑 Administrador
- **Tudo do usuário comum +**
- Cadastrar novos itens
- Editar itens existentes
- Gerenciar outros admins
- Fazer backup
- Acessar WebApp (completo)

### Gerenciar Admins
```
/admin_menu → Gerenciar Admins
- Adicionar novo admin
- Remover admin existente
- Listar todos os admins
```

---

## 📱 Interface WebApp

### Recursos Completos
- **Dashboard** com estatísticas
- **Catálogo** de itens
- **Formulários** de cadastro/edição
- **Scanner QR** (quando disponível)
- **Relatórios** exportáveis
- **Interface responsiva**

### Acesso
1. Comando `/webapp`
2. Clique no botão "📱 Abrir WebApp"
3. Interface abre dentro do Telegram

---

## 🛠 Manutenção e Monitoramento

### Logs Disponíveis
- Comandos executados
- Erros de sistema
- Operações de banco
- Acessos de usuário

### Estatísticas
- Número total de itens
- Uso por usuário
- Comandos mais utilizados
- Performance do sistema

---

## 🚂 Railway Específico

### Vantagens
- **Deploy automático** a cada push
- **Escalabilidade** automática
- **Logs centralizados**
- **SSL/HTTPS** incluído
- **Banco SQLite** persistente

### Configuração
```toml
# railway-admin.toml
[deploy]
startCommand = "python start_railway_admin.py"
restartPolicyType = "ON_FAILURE"

[variables]
RAILWAY_SERVICE_NAME = "admin"
```

---

## 📋 Exemplo de Uso Completo

### Cenário: Empresa de TI

1. **Configuração inicial:**
   ```
   /start - Se tornar admin
   /admin_menu - Acessar painel
   ```

2. **Cadastrar equipamentos:**
   ```
   /novo_item
   > Notebook Dell XPS 13
   > Intel i7, 16GB RAM, 512GB SSD
   > 10
   
   /novo_item
   > Mouse Logitech MX Master 3
   > Mouse wireless ergonômico
   > 25
   ```

3. **Buscar equipamentos:**
   ```
   /buscar dell
   /buscar mouse
   /relatorio
   ```

4. **Adicionar outro admin:**
   ```
   /admin_menu → Gerenciar Admins
   > Adicionar ID: 987654321
   ```

5. **Backup periódico:**
   ```
   /admin_menu → Backup Banco
   ```

---

## ⚡ Deploy Rápido

### Passo a Passo
1. **Fork** do repositório
2. **Railway:** New Project → GitHub
3. **Variáveis:** Adicionar `TELEGRAM_BOT_TOKEN`
4. **Deploy:** Automático
5. **Teste:** Enviar `/start` para o bot

### Verificação
```bash
# Logs do Railway
railway logs --follow

# Status do bot
/start → deve responder imediatamente
/admin_menu → menu administrativo
```

---

**Versão:** v2.3.0-admin  
**Compatibilidade:** Railway, Heroku, VPS  
**Suporte:** Telegram Bot API 6.0+
