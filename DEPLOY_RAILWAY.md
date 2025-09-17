# 🚀 GUIA DE DEPLOY NO RAILWAY

## 📋 **PRÉ-REQUISITOS**

1. **Conta no Railway**: https://railway.app
2. **Token do Bot Telegram** (do @BotFather)
3. **GitHub conectado** ao Railway

---

## 🔧 **PASSO A PASSO**

### **1. Preparar Repository**
```bash
# Commitar mudanças
git add .
git commit -m "Preparado para deploy Railway"
git push origin main
```

### **2. Criar Projeto no Railway**
1. Acesse https://railway.app
2. Clique em "New Project"
3. Conecte com GitHub
4. Selecione o repositório: `Bot_Telegram_Assistente_Estoque`

### **3. Configurar Variáveis de Ambiente**
No Railway Dashboard, vá em **Variables** e adicione:

```
BOT_TOKEN=seu_token_do_botfather_aqui
```

### **4. Deploy Automático**
- Railway detectará `railway.toml` automaticamente
- Build será executado usando `requirements.txt`
- Aplicação iniciará com `start_railway.py`

### **5. Obter URL da Aplicação**
- Railway gerará uma URL: `https://seuapp.railway.app`
- Esta será a URL do seu WebApp

### **6. Configurar WebApp no Telegram**
No código do bot, atualize a URL:
```python
WEBAPP_URL = "https://seuapp.railway.app"
```

---

## 🌐 **ESTRUTURA DE DEPLOY**

```
📦 Railway Deploy
├── 🌐 WebApp Service (Principal)
│   ├── Flask Server (Port 8080)
│   ├── Interface Mobile
│   └── API Endpoints
└── 🤖 Bot Service (Opcional)
    └── Telegram Bot
```

---

## ⚙️ **CONFIGURAÇÕES AUTOMÁTICAS**

### **railway.toml**
```toml
[deploy]
startCommand = "python start_railway.py"

[build]
buildCommand = "pip install -r requirements.txt"

[variables]
PORT = "8080"
```

### **start_railway.py**
- ✅ Configura ambiente automaticamente
- ✅ Cria diretórios necessários
- ✅ Inicializa banco de dados
- ✅ Inicia serviços corretos

---

## 🔍 **VERIFICAR DEPLOY**

### **1. Logs no Railway**
- Vá em **Deployments** → **View Logs**
- Procure por: `🌐 WebApp disponível em...`

### **2. Testar WebApp**
- Acesse a URL gerada pelo Railway
- Deve mostrar a interface de inventário

### **3. Testar Bot**
- `/webapp` no Telegram
- Deve abrir o WebApp mobile

---

## 🚨 **TROUBLESHOOTING**

### **Build Falha**
```bash
# Verificar requirements.txt
cat requirements.txt

# Verificar railway.toml
cat railway.toml
```

### **Serviço não Inicia**
```bash
# Verificar logs no Railway
# Procurar por erros de importação
```

### **WebApp não Abre**
```bash
# Verificar se URL está correta no bot
# Verificar variáveis de ambiente
```

---

## 🎯 **URL FINAL**

Após deploy, seu sistema estará disponível em:
- **WebApp**: `https://seuapp.railway.app`
- **Mobile**: Via comando `/webapp` no Telegram
- **API**: `https://seuapp.railway.app/api/...`

---

## 🔒 **SEGURANÇA**

✅ **Variáveis de ambiente** protegidas no Railway
✅ **HTTPS automático** via Railway
✅ **Banco SQLite** incluso no container
✅ **CORS configurado** para Telegram WebApp

---

## 📱 **TESTE FINAL**

1. **Desktop**: Acesse URL do Railway
2. **Mobile**: Use `/webapp` no bot Telegram
3. **Scanner QR**: Teste câmera no celular
4. **Cadastro**: Adicione itens com códigos automáticos

**🎉 Pronto! Sistema de inventário mobile no Railway!**
