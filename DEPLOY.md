# Deploy Configuration
railway_config:
  build:
    command: "pip install -r requirements.txt"
  start:
    command: "python bot/railway_fotos.py"
  
heroku_config:
  buildpacks:
    - heroku/python
  env:
    PYTHON_VERSION: "3.12.0"
  processes:
    web: "python bot/railway_fotos.py"

# Environment Variables Required
environment_variables:
  - TELEGRAM_BOT_TOKEN  # Token do bot do Telegram
  - WEBHOOK_URL         # URL do webhook (opcional para Railway/Heroku)
  - DATABASE_URL        # URL do banco (opcional - usa SQLite por padrão)

# Files Structure for Deploy
deploy_files:
  essential:
    - bot/railway_fotos.py       # Bot principal com fotos
    - db/init_db.py             # Inicialização do banco
    - requirements.txt          # Dependências Python
    - runtime.txt              # Versão do Python
  
  optional:
    - fotos/                   # Diretório para armazenar fotos
    - logs/                    # Diretório para logs
    - backups/                 # Diretório para backups

# Quick Deploy Commands
quick_deploy:
  railway: |
    railway login
    railway init
    railway add
    railway deploy
  
  heroku: |
    heroku login
    heroku create your-bot-name
    git push heroku main

# Production Checklist
production_checklist:
  - ✅ TOKEN configurado no Railway/Heroku
  - ✅ Diretório /fotos criado automaticamente
  - ✅ Banco SQLite inicializado
  - ✅ Bot testado localmente
  - ✅ Webhook configurado (se necessário)
  - ✅ Logs funcionando
  - ✅ Backup automático ativo
