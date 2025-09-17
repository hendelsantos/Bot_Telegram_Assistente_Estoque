# Bot Telegram - Assistente de Estoque 📦

Um bot inteligente para Telegram desenvolvido em Python para gestão completa de estoque com funcionalidades avançadas.

## 🚀 Funcionalidades

### 📋 Gestão Básica
- ✅ **Cadastro de Itens**: Nome, código, categoria, localização, quantidade, fotos
- ✅ **Busca Inteligente**: Por nome, código ou categoria
- ✅ **Atualização**: Modificar informações e quantidades
- ✅ **Exclusão**: Remover itens do sistema
- ✅ **Upload de Fotos**: Suporte a imagens para identificação visual

### 🔧 Funcionalidades Avançadas
- ✅ **Relatórios**: Geração de relatórios detalhados em PDF
- ✅ **Histórico**: Rastreamento completo de movimentações
- ✅ **Alertas**: Notificações para estoque baixo
- ✅ **QR Code**: Geração e leitura de códigos QR para itens
- ✅ **Inventário Inteligente**: Contagem rápida com QR Code e relatórios automáticos
- ✅ **Controle de Usuários**: Sistema de permissões administrativas
- ✅ **Backup/Restauração**: Proteção e recuperação de dados
- ✅ **Logs**: Registro detalhado de atividades
- ✅ **Ajuda Interativa**: Sistema de ajuda contextual

### 🛠️ Gestão de Reparo
- ✅ **Envio para Reparo**: Controle de itens em manutenção
- ✅ **Retorno de Reparo**: Processamento de itens reparados
- ✅ **Rastreamento**: Histórico completo do processo

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **python-telegram-bot**: Framework para bots Telegram
- **SQLite**: Banco de dados local
- **pandas**: Manipulação de dados
- **reportlab**: Geração de relatórios PDF
- **qrcode & pyzbar**: Processamento de códigos QR
- **Pillow**: Processamento de imagens

## 📦 Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/hendelsantos/Bot_Telegram_Assistente_Estoque.git
cd Bot_Telegram_Assistente_Estoque
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure o ambiente:**
```bash
# Crie o arquivo .env com seu token do bot
echo "TELEGRAM_TOKEN=SEU_TOKEN_AQUI" > .env
```

5. **Inicialize o banco de dados:**
```bash
python db/init_db.py
```

6. **Execute o bot:**
```bash
python bot/main_clean.py
```

## ⚙️ Configuração

### 1. Token do Bot Telegram
- Crie um bot no [@BotFather](https://t.me/botfather)
- Copie o token e adicione no arquivo `.env`

### 2. Configuração de Administradores
- Edite o arquivo `bot/admins.txt`
- Adicione os IDs dos usuários administradores (um por linha)

### 3. Estrutura do Banco de Dados
```sql
-- Tabela de itens
CREATE TABLE itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    codigo TEXT,
    categoria TEXT,
    localizacao TEXT,
    quantidade INTEGER DEFAULT 0,
    observacoes TEXT,
    foto_path TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de movimentações
CREATE TABLE movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    tipo TEXT NOT NULL,
    quantidade INTEGER,
    observacao TEXT,
    usuario_id INTEGER,
    data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES itens (id)
);
```

## 🎯 Como Usar

### Comandos Principais
- `/start` - Iniciar o bot e ver menu principal
- `/menu` - Exibir menu de navegação rápida
- `/novoitem` - Cadastrar novo item
- `/buscar` - Buscar itens no estoque
- `/inventario` - Iniciar inventário com QR Code (admin)
- `/atualizar` - Atualizar informações de itens
- `/excluir` - Remover itens do sistema
- `/relatorio` - Gerar relatórios
- `/backup` - Fazer backup dos dados
- `/ajuda` - Sistema de ajuda interativo

### Menu de Navegação
O bot possui um menu intuitivo com botões para:
- 📋 **Gestão**: Cadastro, busca, atualização
- � **Inventário**: Contagem rápida com QR Code
- �🔧 **Reparo**: Envio e retorno de itens para manutenção
- 📊 **Relatórios**: Visualização de dados e estatísticas
- ⚙️ **Admin**: Funções administrativas (apenas para administradores)

## 📁 Estrutura do Projeto

```
Bot_Telegram_Assistente_Estoque/
├── bot/
│   ├── main_clean.py      # Arquivo principal do bot
│   └── admins.txt         # Lista de administradores
├── db/
│   ├── init_db.py         # Inicialização do banco
│   └── estoque.db         # Banco de dados SQLite
├── fotos/                 # Diretório para armazenar fotos
├── .env                   # Variáveis de ambiente
├── requirements.txt       # Dependências Python
└── README.md             # Este arquivo
```

## 🔒 Segurança

- **Controle de Acesso**: Sistema de permissões baseado em lista de administradores
- **Validação de Dados**: Verificações rigorosas de entrada
- **Backup Automático**: Proteção contra perda de dados
- **Logs Detalhados**: Rastreamento completo de atividades

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Hendel Santos**
- GitHub: [@hendelsantos](https://github.com/hendelsantos)
- Telegram: [Seu perfil]

## 🆘 Suporte

Se você encontrar algum problema ou tiver dúvidas:

1. Verifique a [documentação](#-como-usar)
2. Consulte as [issues abertas](https://github.com/hendelsantos/Bot_Telegram_Assistente_Estoque/issues)
3. Crie uma [nova issue](https://github.com/hendelsantos/Bot_Telegram_Assistente_Estoque/issues/new)

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!** ⭐
