# 📸 Sistema de Estoque com FOTOS - Guia Completo

## 🚀 Funcionalidades Implementadas

### ✅ **Cadastro de Itens com Fotos**
- Nome do item
- Descrição detalhada  
- Catálogo/código (opcional)
- Quantidade
- **FOTO do item** (opcional)

### ✅ **Sistema de Busca Inteligente**
- Busca por nome, descrição ou catálogo
- Exibe fotos junto com os resultados
- Identificação visual com emojis (📸 = com foto, 📄 = sem foto)

### ✅ **Relatórios Completos**
- Estatísticas gerais do estoque
- Contagem de itens com/sem fotos
- Maiores e menores estoques
- Itens recém cadastrados

## 📋 Como Usar

### 🔧 **Para Administradores**

#### 1. Cadastrar Item com Foto
```
/novoitem
```
O bot irá guiá-lo através do processo:
1. Nome do item
2. Descrição
3. Catálogo (digite "skip" para pular)
4. Quantidade
5. **Envie uma foto ou digite "skip"**

#### 2. Buscar Itens
```
/buscar mouse
/buscar notebook
/buscar cabo usb
```
- Busca em nome, descrição e catálogo
- **Mostra fotos automaticamente quando disponíveis**

#### 3. Listar Todos os Itens
```
/listar
```
- Lista até 20 itens
- Mostra se tem foto (📸) ou não (📄)

#### 4. Relatório Completo
```
/relatorio
```
- Estatísticas detalhadas
- **Conta quantos itens têm fotos**

### 👥 **Para Usuários Gerais**
- `/buscar` - Buscar itens
- `/listar` - Ver todos os itens  
- `/relatorio` - Ver estatísticas
- `/menu` - Menu interativo

## 🗂️ **Estrutura do Banco de Dados**

```sql
CREATE TABLE itens (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    catalogo TEXT,              -- NOVO: Catálogo/código
    quantidade INTEGER NOT NULL,
    status TEXT NOT NULL,
    foto_path TEXT,             -- NOVO: Caminho da foto
    foto_id TEXT,               -- NOVO: ID da foto no Telegram
    data_cadastro TIMESTAMP,
    data_atualizacao TIMESTAMP  -- NOVO: Data de atualização
);
```

## 📸 **Sistema de Fotos**

### **Armazenamento**
- Fotos salvas em `/fotos/`
- Nome único gerado automaticamente
- Formato: `uuid_nome-item.jpg`

### **Exibição**
- Fotos mostradas automaticamente nas buscas
- Emojis indicam se item tem foto (📸/📄)
- Relatórios contam itens com/sem fotos

### **Segurança**
- Apenas administradores podem cadastrar
- Fotos organizadas por UUID
- Backup inclui referências às fotos

## 🎯 **Comandos Disponíveis**

### **Comandos Gerais** (Todos os usuários)
| Comando | Descrição |
|---------|-----------|
| `/start` | Iniciar o bot |
| `/menu` | Menu interativo |
| `/buscar <termo>` | **Buscar itens (com fotos)** |
| `/listar` | Listar todos os itens |
| `/relatorio` | **Relatório com estatísticas de fotos** |
| `/ajuda` | Ver ajuda |

### **Comandos Administrativos** (Só admins)
| Comando | Descrição |
|---------|-----------|
| `/novoitem` | **Cadastrar item COM FOTO** |
| `/editaritem` | Editar item existente |
| `/deletaritem` | Deletar item |
| `/backup` | Backup do banco |
| `/adminusers` | Gerenciar administradores |

## 💡 **Exemplos Práticos**

### **Cadastrar Mouse com Foto**
1. `/novoitem`
2. Nome: "Mouse Gamer RGB"
3. Descrição: "Mouse gamer com LED RGB, 6000 DPI"
4. Catálogo: "MSE-001" (ou "skip")
5. Quantidade: 15
6. **Enviar foto do mouse**

### **Buscar e Ver Foto**
```
/buscar mouse
```
**Resultado:**
```
📸 Mouse Gamer RGB
📝 Mouse gamer com LED RGB, 6000 DPI
📋 Catálogo: MSE-001
📦 Qtd: 15 | 🆔 ID: 1
```
*+ Foto do mouse exibida automaticamente*

## 🔧 **Configuração**

### **Variáveis de Ambiente**
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
WEBAPP_URL=http://localhost:8080
```

### **Estrutura de Pastas**
```
Assistente_Stock_MPA/
├── bot/
│   ├── railway_fotos.py     # 📸 BOT COM FOTOS
│   └── admins.txt
├── db/
│   ├── estoque.db
│   └── init_db.py
├── fotos/                   # 📸 PASTA DAS FOTOS
│   ├── abc123_mouse.jpg
│   └── def456_notebook.jpg
└── .env
```

## 🎯 **Diferenciais do Sistema**

### ✅ **O que foi implementado**
- ✅ Cadastro com fotos
- ✅ Exibição automática de fotos nas buscas
- ✅ Campo catálogo/código
- ✅ Estatísticas de fotos nos relatórios
- ✅ Emojis visuais (📸/📄)
- ✅ Sistema opcional (pode pular foto)
- ✅ Organização segura das fotos

### 🎯 **Como testar**
1. Execute: `python bot/railway_fotos.py`
2. No Telegram: `/novoitem`
3. Cadastre um item e envie uma foto
4. Use `/buscar` para ver o item com foto
5. Verifique `/relatorio` para estatísticas

## 🚀 **Deploy**

### **Local**
```bash
source .venv/bin/activate
python bot/railway_fotos.py
```

### **Railway**
1. Substitua `railway_completo.py` por `railway_fotos.py` no `start_railway_admin.py`
2. Deploy normal

---

**🎉 Sistema completo implementado com sucesso!**
Agora você pode cadastrar itens com fotos, buscar e visualizar imagens automaticamente!
