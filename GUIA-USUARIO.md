# Guia de Uso - Bot Assistente de Estoque 100% Funcional

Este guia contém instruções detalhadas para garantir o uso correto e sem conflitos do bot atualizado.

## 🛠️ Inicialização Correta do Bot

Para iniciar o bot corretamente e evitar conflitos, siga estas etapas:

1. **Limpar sessões existentes:**
   ```bash
   python bot/clear_telegram.py
   ```

2. **Remover locks de arquivo (se necessário):**
   ```bash
   rm -f /tmp/assistente_estoque_bot.lock /tmp/assistente_estoque_bot.pid
   ```

3. **Iniciar o bot final:**
   ```bash
   source .venv/bin/activate
   python bot/bot_final.py
   ```

## 🚨 Solução de Problemas

### Erro "Conflict: terminated by other getUpdates request"

Este erro ocorre quando múltiplas instâncias do bot tentam usar o mesmo token do Telegram.

**Solução:**
1. Encerre todas as instâncias do bot:
   ```bash
   pkill -f "python.*bot.*"
   ```
2. Limpe as sessões do Telegram:
   ```bash
   python bot/clear_telegram.py
   ```
3. Remova os arquivos de lock:
   ```bash
   rm -f /tmp/assistente_estoque_bot.lock /tmp/assistente_estoque_bot.pid
   ```
4. Inicie novamente usando o bot_final.py.

### Banco de Dados

Se encontrar problemas com o banco de dados, você pode reinicializá-lo:

```bash
source .venv/bin/activate
python db/init_db.py
```

## 📋 Arquivos Importantes

- `bot/bot_final.py` - Versão 100% funcional do bot com sistema anti-conflito
- `bot/railway_fotos_100.py` - Versão alternativa do bot com fotos
- `bot/clear_telegram.py` - Utilitário para limpar sessões do Telegram
- `db/init_db.py` - Inicializa o banco de dados
- `db/estoque.db` - Banco de dados SQLite

## 🤖 Recursos do Bot Final

A nova versão `bot_final.py` implementa:

- ✅ **Sistema de lock exclusivo** - Impede múltiplas instâncias
- ✅ **Limpeza automática** - Gerencia recursos corretamente
- ✅ **Melhor tratamento de erros** - Logs detalhados e recuperação automática
- ✅ **Inicialização robusta** - Garante conexão correta com banco de dados
- ✅ **Sistema de fotos** - Upload, armazenamento e exibição de fotos

## ⚙️ Dicas de Produção

Para usar em ambiente de produção:

1. **Registrar como serviço:**
   - Use systemd para manter o bot rodando
   - Configure reinício automático em caso de falhas
   
2. **Backup automático:**
   - Configure backups regulares do banco de dados
   - Mantenha backup das fotos armazenadas

3. **Monitoramento:**
   - Verifique os logs para problemas potenciais
   - Implemente um sistema de alertas para erros críticos

---

## 📑 Lista de Comandos

### Comandos Gerais:
- `/start` - Inicia o bot
- `/menu` - Menu principal
- `/buscar [nome]` - Busca itens
- `/listar` - Ver todos os itens
- `/relatorio` - Gerar relatório
- `/webapp` - Abrir interface web
- `/ajuda` - Ver ajuda completa

### Comandos Administrativos:
- `/novoitem` - Cadastrar item COM FOTO
- `/editaritem` - Editar item
- `/deletaritem` - Remover item
- `/backup` - Fazer backup
- `/adminusers` - Gerenciar administradores
