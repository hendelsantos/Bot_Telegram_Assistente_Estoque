# 📋 Guia de Versões Railway

## 🎯 Escolha a Versão Ideal

### 👤 **Versão Simples** (v2.2.0)
**Para:** Uso básico, consulta apenas  
**Arquivo:** `railway_bot_simple.py`  
**Funcionalidades:**
- ✅ Buscar itens
- ✅ Relatórios
- ✅ WebApp (visualização)
- ❌ Cadastro de itens
- ❌ Edição de estoque

**Deploy:**
```bash
# Usar: railway.toml (padrão)
# Script: start_railway.py
```

---

### 👑 **Versão Administrativa** (v2.3.0-admin)
**Para:** Gestão completa do estoque  
**Arquivo:** `railway_admin_bot.py`  
**Funcionalidades:**
- ✅ **TUDO da versão simples +**
- ✅ Cadastrar novos itens
- ✅ Editar itens existentes
- ✅ Gerenciar administradores
- ✅ Backup do banco
- ✅ Controle de acesso
- ✅ WebApp completo

**Deploy:**
```bash
# Usar: railway-admin.toml
# Script: start_railway_admin.py
```

---

## 🚀 Deploy Rápido

### Configuração Railway

#### Versão Simples
```toml
# Usar railway.toml existente
[variables]
TELEGRAM_BOT_TOKEN = "seu_token"
RAILWAY_SERVICE_NAME = "bot"
```

#### Versão Administrativa
```toml
# Usar railway-admin.toml
[variables]
TELEGRAM_BOT_TOKEN = "seu_token"
RAILWAY_SERVICE_NAME = "admin"
WEBAPP_URL = "https://seu-projeto.railway.app"
```

---

## 📊 Comparação

| Funcionalidade | Simples | Admin |
|----------------|---------|-------|
| Buscar itens | ✅ | ✅ |
| Relatórios | ✅ | ✅ |
| WebApp | ✅ | ✅ |
| Cadastrar itens | ❌ | ✅ |
| Editar itens | ❌ | ✅ |
| Backup | ❌ | ✅ |
| Gerenciar admins | ❌ | ✅ |
| Controle acesso | ❌ | ✅ |

---

## 🎛 Comandos

### Versão Simples
```
/start      - Iniciar
/menu       - Menu principal
/buscar     - Buscar itens
/relatorio  - Relatório
/webapp     - Interface web
```

### Versão Administrativa
```
// Todos os comandos da versão simples +
/admin_menu - Menu administrativo
/novo_item  - Cadastrar item
👑 Acesso diferenciado por usuário
```

---

## 🔧 Escolha por Caso de Uso

### 🏢 **Empresa Pequena/Média**
**Recomendação:** Versão Administrativa  
**Motivo:** Controle completo + múltiplos usuários

### 👤 **Uso Pessoal/Consulta**
**Recomendação:** Versão Simples  
**Motivo:** Mais leve + funcionalidades básicas

### 🏭 **Empresa Grande**
**Recomendação:** Versão Administrativa  
**Motivo:** Gestão de permissões + backup

---

## 📁 Estrutura do Repositório

```
📂 Assistente_Stock_MPA/
├── 🤖 bot/
│   ├── railway_bot_simple.py      # ← Versão Simples
│   ├── railway_admin_bot.py       # ← Versão Admin
│   └── admins.txt                 # Lista de admins
├── ⚙️ Configuração/
│   ├── railway.toml               # ← Deploy Simples
│   ├── railway-admin.toml         # ← Deploy Admin
│   ├── start_railway.py           # ← Script Simples
│   └── start_railway_admin.py     # ← Script Admin
└── 📚 Docs/
    ├── RAILWAY.md                 # Doc versão simples
    └── ADMIN-RAILWAY.md           # Doc versão admin
```

---

## 🚦 Deploy Step-by-Step

### 1. **Escolher Versão**
- Simples: Apenas consulta
- Admin: Gestão completa

### 2. **Configurar Railway**
```bash
# Conectar repositório GitHub
# Escolher arquivo de configuração correto
```

### 3. **Definir Variáveis**
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
RAILWAY_SERVICE_NAME=admin_ou_bot
```

### 4. **Deploy Automático**
Railway detecta e faz deploy automaticamente

---

**Versões Disponíveis:**
- `v2.2.0` - Simples
- `v2.3.0-admin` - Administrativa

**Última Atualização:** 17/09/2025
