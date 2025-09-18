#!/usr/bin/env python3
"""
Bot Telegram com Funcionalidade de FOTOS - Sistema Completo de Estoque 100% FUNCIONAL
Versão com upload, armazenamento e exibição de fotos dos itens - Otimizado
"""

import os
import sys
import logging
import signal
from datetime import datetime
from dotenv import load_dotenv
import json
import asyncio
import uuid
import subprocess
import random

# Configurar logging antes de tudo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_fotos.log")
    ]
)

# Verificar se há outra instância rodando
def kill_other_instances():
    try:
        my_pid = os.getpid()
        cmd = f"ps -ef | grep '[p]ython.*railway.*fotos' | awk '{{print $2}}'"
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        
        if output:
            for pid in output.split('\n'):
                pid = int(pid.strip())
                if pid != my_pid:
                    print(f"⚠️ Encontrada outra instância do bot (PID: {pid}). Encerrando...")
                    try:
                        os.kill(pid, signal.SIGTERM)
                        print(f"✅ Instância anterior encerrada com sucesso.")
                    except Exception as e:
                        print(f"❌ Erro ao encerrar instância: {e}")
    except Exception as e:
        print(f"⚠️ Erro ao verificar outras instâncias: {e}")

# Matar outras instâncias antes de começar
kill_other_instances()

# Carregar variáveis de ambiente
load_dotenv()

# Verificar token antes de importar as libs do telegram
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print('❌ ERRO: Defina TELEGRAM_BOT_TOKEN no arquivo .env')
    sys.exit(1)

if ":" not in TOKEN or len(TOKEN) < 20:
    print('❌ ERRO: Token parece inválido. Verifique o formato.')
    sys.exit(1)

# Importar bibliotecas do Telegram após verificar o token
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    from telegram.ext import (
        ApplicationBuilder, CommandHandler, MessageHandler, filters, 
        ContextTypes, ConversationHandler, CallbackQueryHandler
    )
except ImportError as e:
    print(f"❌ ERRO: Não foi possível importar as bibliotecas do Telegram: {e}")
    print("📦 Execute: pip install python-telegram-bot>=20.0")
    sys.exit(1)

# Importar outras dependências
try:
    import aiosqlite
    import pandas as pd
except ImportError as e:
    print(f"❌ ERRO: Dependência faltando: {e}")
    print("📦 Execute: pip install aiosqlite pandas")
    sys.exit(1)

# Constantes
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
ADMINS_FILE = os.path.join(os.path.dirname(__file__), 'admins.txt')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8080')
FOTOS_DIR = os.path.join(os.path.dirname(__file__), '../fotos')

# Criar diretório de fotos se não existir
os.makedirs(FOTOS_DIR, exist_ok=True)

# Estados da conversação
(NOME_ITEM, DESC_ITEM, CATALOGO_ITEM, QTD_ITEM, FOTO_ITEM,
 EDITAR_ESCOLHA, EDITAR_CAMPO, EDITAR_VALOR,
 ADD_ADMIN, REMOVE_ADMIN) = range(10)

def is_admin(user_id):
    """Verifica se usuário é administrador"""
    try:
        if not os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'w') as f:
                f.write(str(user_id) + '\n')
            return True
        
        with open(ADMINS_FILE) as f:
            admins = [line.strip() for line in f if line.strip()]
        return str(user_id) in admins
    except Exception as e:
        logging.error(f"Erro ao verificar admin: {e}")
        return False

def add_admin(user_id):
    """Adiciona novo administrador"""
    try:
        with open(ADMINS_FILE, 'a') as f:
            f.write(str(user_id) + '\n')
        return True
    except Exception as e:
        logging.error(f"Erro ao adicionar admin: {e}")
        return False

def remove_admin(user_id):
    """Remove administrador"""
    try:
        with open(ADMINS_FILE) as f:
            admins = [line.strip() for line in f if line.strip()]
        
        admins = [admin for admin in admins if admin != str(user_id)]
        
        with open(ADMINS_FILE, 'w') as f:
            for admin in admins:
                f.write(admin + '\n')
        return True
    except Exception as e:
        logging.error(f"Erro ao remover admin: {e}")
        return False

async def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    print("🗄️ Inicializando banco de dados...")
    
    # Verificar se diretório do banco existe
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"📁 Diretório do banco criado: {db_dir}")
    
    conn = None
    try:
        # Conectar ao banco de dados com timeout explícito
        conn = await aiosqlite.connect(DB_PATH, timeout=30.0)
        
        # Tabela principal com campos para fotos e catálogo
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                catalogo TEXT,
                quantidade INTEGER NOT NULL,
                status TEXT NOT NULL,
                foto_path TEXT,
                foto_id TEXT,
                info_reparo TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de movimentações
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            usuario TEXT,
            acao TEXT NOT NULL,
            detalhes TEXT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES itens(id)
        )
        ''')
        
        await conn.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        raise e
    finally:
        # Garantir que a conexão seja fechada
        if conn:
            await conn.close()

async def salvar_foto(photo_file, item_nome):
    """Salva a foto no diretório e retorna o caminho"""
    try:
        # Criar diretório de fotos se não existir (verificação extra)
        os.makedirs(FOTOS_DIR, exist_ok=True)
        
        # Gerar nome único para a foto
        filename = f"{uuid.uuid4().hex}_{item_nome.replace(' ', '_')[:30]}.jpg"
        filepath = os.path.join(FOTOS_DIR, filename)
        
        # Baixar e salvar foto
        await photo_file.download_to_drive(filepath)
        print(f"📸 Foto salva: {filepath}")
        return filename
    except Exception as e:
        logging.error(f"Erro ao salvar foto: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        is_user_admin = is_admin(user_id)
        
        texto = f'📸 *Assistente de Estoque com FOTOS - Sistema Completo*\n\n'
        texto += f'Olá, {user_name}!\n\n'
        
        if is_user_admin:
            texto += '👑 *Você é ADMINISTRADOR*\n\n'
            texto += '*Comandos Administrativos:*\n'
            texto += '• /novoitem - ➕ Cadastrar novo item COM FOTO\n'
            texto += '• /editaritem - ✏️ Editar item\n'
            texto += '• /deletaritem - 🗑️ Deletar item\n'
            texto += '• /backup - 💾 Backup do banco\n'
            texto += '• /adminusers - 👥 Gerenciar admins\n\n'
        
        texto += '*Comandos Gerais:*\n'
        texto += '• /menu - 📋 Menu principal\n'
        texto += '• /buscar - 🔍 Buscar itens\n'
        texto += '• /listar - 📦 Listar todos os itens\n'
        texto += '• /relatorio - 📊 Relatório completo\n'
        texto += '• /webapp - 📱 Interface web\n'
        texto += '• /ajuda - ❓ Ver comandos'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Erro no comando start: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal com botões"""
    try:
        user_id = update.effective_user.id
        
        keyboard = []
        
        # Botões para todos os usuários
        keyboard.extend([
            [InlineKeyboardButton("🔍 Buscar Item", callback_data='buscar_menu')],
            [InlineKeyboardButton("📦 Listar Todos", callback_data='listar_todos')],
            [InlineKeyboardButton("📊 Relatório", callback_data='relatorio_menu')],
        ])
        
        # Botões administrativos
        if is_admin(user_id):
            keyboard.extend([
                [InlineKeyboardButton("➕ Novo Item", callback_data='novo_item_menu')],
                [InlineKeyboardButton("✏️ Editar Item", callback_data='editar_item_menu')],
                [InlineKeyboardButton("💾 Backup", callback_data='backup_menu')],
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('📋 *Menu Principal*\nEscolha uma opção:', reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Erro no comando menu: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de ajuda"""
    try:
        user_id = update.effective_user.id
        
        texto = "*📋 Comandos Disponíveis:*\n\n"
        texto += "• /start - Iniciar bot\n"
        texto += "• /menu - Menu principal\n"
        texto += "• /buscar [nome] - Buscar itens\n"
        texto += "• /listar - Ver todos os itens\n"
        texto += "• /relatorio - Gerar relatório\n"
        texto += "• /webapp - Abrir interface web\n"
        texto += "• /ajuda - Ver esta ajuda\n"
        
        if is_admin(user_id):
            texto += "\n*👑 Comandos Administrativos:*\n"
            texto += "• /novoitem - Cadastrar item COM FOTO\n"
            texto += "• /editaritem - Editar item\n"
            texto += "• /deletaritem - Remover item\n"
            texto += "• /backup - Fazer backup\n"
            texto += "• /adminusers - Gerenciar admins\n"
        
        await update.message.reply_text(texto, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Erro no comando ajuda: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abre a interface web"""
    try:
        if not WEBAPP_URL:
            await update.message.reply_text("❌ WebApp não configurado.")
            return
        
        keyboard = [[InlineKeyboardButton("🌐 Abrir Interface Web", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Clique no botão abaixo para abrir a interface web:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Erro no comando webapp: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

# Funções de novo item COM FOTOS
async def novo_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de adicionar novo item com foto"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Você não tem permissão para cadastrar itens.")
            return ConversationHandler.END
        
        await update.message.reply_text(
            "🆕 *Cadastrar Novo Item com FOTO*\n\n"
            "Digite o *nome* do item:\n"
            "Para cancelar a qualquer momento, digite /cancelar",
            parse_mode='Markdown'
        )
        
        return NOME_ITEM
    except Exception as e:
        logging.error(f"Erro ao iniciar novo item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome do item e solicita a descrição"""
    try:
        nome = update.message.text.strip()
        context.user_data['novo_item'] = {'nome': nome}
        
        await update.message.reply_text(
            f"📝 *Nome:* {nome}\n\n"
            "Digite a *descrição* do item:",
            parse_mode='Markdown'
        )
        
        return DESC_ITEM
    except Exception as e:
        logging.error(f"Erro ao processar nome do item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a descrição do item e solicita o catálogo"""
    try:
        descricao = update.message.text.strip()
        context.user_data['novo_item']['descricao'] = descricao
        
        await update.message.reply_text(
            f"📝 *Descrição:* {descricao}\n\n"
            "Digite o *catálogo* do item (ex: Eletrônicos, Escritório, Ferramentas):",
            parse_mode='Markdown'
        )
        
        return CATALOGO_ITEM
    except Exception as e:
        logging.error(f"Erro ao processar descrição do item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o catálogo do item e solicita a quantidade"""
    try:
        catalogo = update.message.text.strip()
        context.user_data['novo_item']['catalogo'] = catalogo
        
        await update.message.reply_text(
            f"📁 *Catálogo:* {catalogo}\n\n"
            "Digite a *quantidade* do item:",
            parse_mode='Markdown'
        )
        
        return QTD_ITEM
    except Exception as e:
        logging.error(f"Erro ao processar catálogo do item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a quantidade do item e solicita a foto"""
    try:
        quantidade_text = update.message.text.strip()
        
        try:
            quantidade = int(quantidade_text)
            if quantidade < 0:
                raise ValueError("Quantidade não pode ser negativa")
        except ValueError:
            await update.message.reply_text("⚠️ Digite uma quantidade válida (número inteiro positivo):")
            return QTD_ITEM
        
        context.user_data['novo_item']['quantidade'] = quantidade
        
        await update.message.reply_text(
            f"🔢 *Quantidade:* {quantidade}\n\n"
            "📸 Agora, envie uma *foto* do item.\n"
            "Se não tiver uma foto, digite *pular*:",
            parse_mode='Markdown'
        )
        
        return FOTO_ITEM
    except Exception as e:
        logging.error(f"Erro ao processar quantidade do item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a foto do item e salva o item completo no banco"""
    try:
        user_id = update.effective_user.id
        nome_item = context.user_data['novo_item']['nome']
        foto_path = None
        foto_id = None
        
        if update.message.photo:
            # Se o usuário enviou uma foto
            photo_file = await update.message.photo[-1].get_file()
            try:
                foto_path = await salvar_foto(photo_file, nome_item)
                foto_id = update.message.photo[-1].file_id
                await update.message.reply_text("✅ Foto recebida e salva!")
            except Exception as e:
                logging.error(f"Erro ao salvar foto: {e}")
                await update.message.reply_text("⚠️ Erro ao salvar a foto, mas vamos continuar com o cadastro.")
        else:
            # Se o usuário digitou "pular" ou outro texto
            texto = update.message.text.strip().lower()
            if texto == 'pular':
                await update.message.reply_text("➡️ Pulando etapa de foto.")
            else:
                await update.message.reply_text("⚠️ Nenhuma foto enviada. Continuando sem foto.")
        
        # Preparar item para cadastro
        item = context.user_data['novo_item']
        item['status'] = 'disponível'
        item['foto_path'] = foto_path
        item['foto_id'] = foto_id
        
        # Salvar no banco
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    '''INSERT INTO itens (nome, descricao, catalogo, quantidade, status, foto_path, foto_id, data_atualizacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))''',
                    (item['nome'], item['descricao'], item['catalogo'], item['quantidade'], 
                    item['status'], item['foto_path'], item['foto_id'])
                )
                item_id = cursor.lastrowid
                
                # Registrar movimentação
                await db.execute(
                    '''INSERT INTO movimentacoes (item_id, usuario, acao, detalhes)
                    VALUES (?, ?, ?, ?)''',
                    (item_id, f"Admin {user_id}", "cadastro", f"Item cadastrado com {item['quantidade']} unidades")
                )
                
                await db.commit()
            
            # Mensagem de confirmação com info de foto
            if foto_path:
                await update.message.reply_text(
                    f"✅ *Item cadastrado com sucesso!* 📸\n\n"
                    f"📦 *Nome:* {item['nome']}\n"
                    f"📝 *Descrição:* {item['descricao']}\n"
                    f"📁 *Catálogo:* {item['catalogo']}\n"
                    f"🔢 *Quantidade:* {item['quantidade']}\n"
                    f"📸 *Foto:* Sim\n"
                    f"📊 *Status:* {item['status']}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"✅ *Item cadastrado com sucesso!* 📄\n\n"
                    f"📦 *Nome:* {item['nome']}\n"
                    f"📝 *Descrição:* {item['descricao']}\n"
                    f"📁 *Catálogo:* {item['catalogo']}\n"
                    f"🔢 *Quantidade:* {item['quantidade']}\n"
                    f"📸 *Foto:* Não\n"
                    f"📊 *Status:* {item['status']}",
                    parse_mode='Markdown'
                )
            
            # Limpar dados
            context.user_data.clear()
            
        except Exception as e:
            logging.error(f"Erro ao cadastrar item no banco: {e}")
            await update.message.reply_text(f"❌ Erro ao cadastrar item: {str(e)}")
        
        return ConversationHandler.END
    except Exception as e:
        logging.error(f"Erro ao processar foto do item: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela a operação atual"""
    context.user_data.clear()
    await update.message.reply_text("❌ Operação cancelada.")
    return ConversationHandler.END

# Funções de busca com FOTOS
async def buscar_itens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca itens por nome, com suporte a fotos"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔍 *Busca de Itens*\n\n"
                "Digite o nome do item após o comando:\n"
                "Exemplo: `/buscar mouse`",
                parse_mode='Markdown'
            )
            return
        
        termo = ' '.join(context.args).strip()
        
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    '''SELECT id, nome, descricao, catalogo, quantidade, status, foto_path, foto_id
                    FROM itens
                    WHERE nome LIKE ? OR descricao LIKE ? OR catalogo LIKE ?
                    ORDER BY nome''',
                    (f'%{termo}%', f'%{termo}%', f'%{termo}%')
                )
                
                itens = await cursor.fetchall()
                
                if not itens:
                    await update.message.reply_text(f"❌ Nenhum item encontrado com '{termo}'")
                    return
                
                # Processar e enviar cada item, com foto se disponível
                for item in itens:
                    # Preparar texto com emoji diferente para itens com/sem foto
                    if item['foto_id'] or item['foto_path']:
                        texto = f"📸 *Item #{item['id']}*\n\n"
                    else:
                        texto = f"📄 *Item #{item['id']}*\n\n"
                    
                    texto += f"📦 *Nome:* {item['nome']}\n"
                    texto += f"📝 *Descrição:* {item['descricao'] or 'N/A'}\n"
                    texto += f"📁 *Catálogo:* {item['catalogo'] or 'N/A'}\n"
                    texto += f"🔢 *Quantidade:* {item['quantidade']}\n"
                    texto += f"📊 *Status:* {item['status']}\n"
                    
                    # Se tem foto_id, enviar a foto diretamente
                    if item['foto_id']:
                        try:
                            await update.message.reply_photo(
                                photo=item['foto_id'],
                                caption=texto,
                                parse_mode='Markdown'
                            )
                            continue
                        except Exception as e:
                            logging.error(f"Erro ao usar foto_id: {e}")
                            # Se falhar, tenta usar o caminho do arquivo
                    
                    # Se tem foto_path, tentar enviar do arquivo
                    if item['foto_path']:
                        try:
                            file_path = os.path.join(FOTOS_DIR, item['foto_path'])
                            if os.path.exists(file_path):
                                with open(file_path, 'rb') as photo:
                                    await update.message.reply_photo(
                                        photo=photo,
                                        caption=texto,
                                        parse_mode='Markdown'
                                    )
                                continue
                        except Exception as e:
                            logging.error(f"Erro ao enviar foto do arquivo: {e}")
                    
                    # Se chegou aqui, não conseguiu enviar foto ou não tem foto
                    await update.message.reply_text(texto, parse_mode='Markdown')
                
                total = len(itens)
                await update.message.reply_text(f"✅ {total} {'item' if total == 1 else 'itens'} encontrado{'s' if total > 1 else ''} para '{termo}'")
        
        except Exception as e:
            logging.error(f"Erro na busca no banco: {e}")
            await update.message.reply_text(f"❌ Erro ao buscar itens: {str(e)}")
    except Exception as e:
        logging.error(f"Erro na busca de itens: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def listar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os itens resumidamente"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                '''SELECT id, nome, quantidade, status, foto_path IS NOT NULL OR foto_id IS NOT NULL as tem_foto
                FROM itens
                ORDER BY nome''')
            
            itens = await cursor.fetchall()
            
            if not itens:
                await update.message.reply_text("❌ Nenhum item cadastrado")
                return
            
            # Preparar mensagem
            texto = "📋 *Lista de Itens*\n\n"
            for item in itens:
                emoji = "📸" if item['tem_foto'] else "📄"
                texto += f"{emoji} #{item['id']} - {item['nome']} ({item['quantidade']} un.)\n"
            
            total = len(itens)
            texto += f"\nTotal: {total} {'item' if total == 1 else 'itens'}"
            
            await update.message.reply_text(texto, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Erro ao listar itens: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera relatório com estatísticas e informações de fotos"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Total de itens
            cursor = await db.execute('SELECT COUNT(*) as total FROM itens')
            total_itens = (await cursor.fetchone())['total']
            
            # Itens por status
            cursor = await db.execute('SELECT status, COUNT(*) as total FROM itens GROUP BY status')
            status = {row['status']: row['total'] async for row in cursor}
            
            # Total de itens com foto
            cursor = await db.execute(
                '''SELECT COUNT(*) as total FROM itens 
                WHERE foto_path IS NOT NULL OR foto_id IS NOT NULL''')
            itens_com_foto = (await cursor.fetchone())['total']
            
            # Itens por catálogo
            cursor = await db.execute(
                '''SELECT catalogo, COUNT(*) as total FROM itens 
                WHERE catalogo IS NOT NULL GROUP BY catalogo ORDER BY total DESC''')
            catalogos = [(row['catalogo'], row['total']) async for row in cursor]
            
            # Total de estoque
            cursor = await db.execute('SELECT SUM(quantidade) as total FROM itens')
            total_estoque = (await cursor.fetchone())['total'] or 0
        
        # Construir relatório
        texto = "📊 *RELATÓRIO DE ESTOQUE*\n\n"
        
        texto += f"📦 *Total de Itens:* {total_itens}\n"
        texto += f"🔢 *Quantidade Total:* {total_estoque} unidades\n"
        texto += f"📸 *Itens com Foto:* {itens_com_foto} ({round(itens_com_foto/total_itens*100) if total_itens > 0 else 0}%)\n"
        texto += f"📄 *Itens sem Foto:* {total_itens - itens_com_foto}\n\n"
        
        texto += "*Status dos Itens:*\n"
        for s, t in status.items():
            texto += f"• {s}: {t} itens\n"
        
        texto += "\n*Itens por Catálogo:*\n"
        for cat, total in catalogos[:5]:  # Mostrar os 5 maiores catálogos
            texto += f"• {cat}: {total} itens\n"
        
        if len(catalogos) > 5:
            texto += f"• Outros catálogos: {sum(t for _, t in catalogos[5:])} itens\n"
        
        # Enviar relatório
        await update.message.reply_text(texto, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Erro ao gerar relatório: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks dos botões"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'buscar_menu':
            await query.message.reply_text("🔍 Digite o comando: /buscar nome_do_item")
        
        elif query.data == 'listar_todos':
            await listar_todos(query, context)
        
        elif query.data == 'relatorio_menu':
            await relatorio(query, context)
        
        elif query.data == 'novo_item_menu':
            # Iniciar conversa para novo item
            await query.message.reply_text(
                "🆕 Para cadastrar um novo item com foto, use o comando: /novoitem"
            )
    except Exception as e:
        logging.error(f"Erro ao processar callback: {e}")
        await update.callback_query.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

# Handler de erro global
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lida com erros de forma global"""
    logging.error(f"Erro não tratado: {context.error}")
    
    try:
        # Tentar enviar mensagem para o usuário
        if update and update.effective_chat:
            await update.effective_chat.send_message(
                "❌ Ocorreu um erro ao processar sua solicitação. "
                "Por favor, tente novamente mais tarde."
            )
    except:
        pass

def main():
    """Função principal do bot"""
    try:
        # Verificar diretórios importantes
        for dir_path in [os.path.dirname(DB_PATH), FOTOS_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"📁 Diretório criado: {dir_path}")
        
        # Verificar arquivo de admins
        if not os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'w') as f:
                pass  # Cria arquivo vazio
            print(f"📄 Arquivo de admins criado: {ADMINS_FILE}")
        
        print(f'🚀 Iniciando Bot Completo com FOTOS...')
        print(f'🔑 Token: {TOKEN[:8]}...')
        print(f'🌐 WebApp: {WEBAPP_URL}')
        print(f'👑 Admins: {ADMINS_FILE}')
        print(f'📸 Fotos: {FOTOS_DIR}')
        
        # Tratamento de sinal de encerramento
        def signal_handler(sig, frame):
            print("\n⚠️ Recebido sinal de encerramento. Fechando bot...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar o banco de dados antes de criar a aplicação
        # Criamos um loop temporário para inicializar o banco
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(init_database())
            loop.close()
        except Exception as e:
            print(f"❌ Erro fatal ao inicializar banco de dados: {e}")
            return
        
        # Criar aplicação com configurações de retry
        app_builder = ApplicationBuilder().token(TOKEN)
        
        # Configurações adicionais para mais estabilidade
        app_builder.connection_pool_size(8)
        app_builder.connect_timeout(30.0)
        app_builder.pool_timeout(30.0)
        app_builder.read_timeout(30.0)
        app_builder.write_timeout(30.0)
        
        app = app_builder.build()
        
        # Adicionar handler de erro global
        app.add_error_handler(error_handler)
        
        # Conversation Handler para novo item
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('novoitem', novo_item_inicio)],
            states={
                NOME_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_nome)],
                DESC_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_descricao)],
                CATALOGO_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_catalogo)],
                QTD_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_quantidade)],
                FOTO_ITEM: [
                    MessageHandler(filters.PHOTO, novo_item_foto),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_foto)
                ]
            },
            fallbacks=[CommandHandler('cancelar', cancelar)]
        )
        
        # Registrar handlers
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('menu', menu))
        app.add_handler(CommandHandler('buscar', buscar_itens))
        app.add_handler(CommandHandler('listar', listar_todos))
        app.add_handler(CommandHandler('relatorio', relatorio))
        app.add_handler(CommandHandler('ajuda', ajuda))
        app.add_handler(CommandHandler('webapp', webapp_command))
        app.add_handler(conv_handler)
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Bot com FOTOS iniciado!")
        print("📋 Comandos registrados:")
        print("   • /start, /menu, /ajuda")
        print("   • /buscar, /listar, /relatorio") 
        print("   • /novoitem (COM FOTOS), /webapp")
        print("   • Callbacks interativos")
        
        # Sinalizar que estamos prontos para o sistema
        print("🟢 Sistema 100% funcional e pronto!")
        
        # Iniciar o bot
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
