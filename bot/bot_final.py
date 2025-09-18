#!/usr/bin/env python3
"""
Bot Telegram com Funcionalidade de FOTOS - Sistema Completo de Estoque 100% FUNCIONAL
Versão FINAL com tratamento robusto de instâncias e conexões
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
import time
import sqlite3
import random
import fcntl
import atexit

# Configurar logging antes de tudo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot_fotos.log")
    ]
)

logger = logging.getLogger("BotFinal")

# Definir constantes globais
LOCK_FILE = "/tmp/assistente_estoque_bot.lock"
PID_FILE = "/tmp/assistente_estoque_bot.pid"

# Gerenciamento de lock de instância única
def obter_lock_exclusivo():
    """Garante que apenas uma instância do bot esteja em execução"""
    try:
        # Criar arquivo de lock
        lock_fd = open(LOCK_FILE, 'w')
        
        # Tentar obter lock exclusivo, não bloqueante
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Registrar PID atual
        with open(PID_FILE, 'w') as pid_file:
            pid_file.write(str(os.getpid()))
            
        # Registrar função para liberar lock no encerramento
        atexit.register(liberar_lock, lock_fd)
        
        print("🔒 Lock exclusivo obtido com sucesso")
        return lock_fd
    except IOError:
        try:
            # Ler PID do processo que possui o lock
            with open(PID_FILE, 'r') as pid_file:
                pid = int(pid_file.read().strip())
                print(f"⚠️ Outra instância do bot já está em execução (PID: {pid})")
                
                # Verificar se o processo ainda está vivo
                try:
                    os.kill(pid, 0)  # Não mata, apenas verifica se existe
                    print(f"❌ Processo com PID {pid} ainda está em execução. Saindo.")
                    return None
                except OSError:
                    print(f"⚠️ Processo com PID {pid} não existe mais, mas o lock persiste.")
                    print("🧹 Limpando arquivos de lock órfãos...")
                    
                    # Tentar remover arquivos de lock manualmente
                    try:
                        os.remove(LOCK_FILE)
                        os.remove(PID_FILE)
                        print("✅ Arquivos de lock removidos com sucesso")
                        
                        # Tentar novamente após limpeza
                        time.sleep(1)
                        return obter_lock_exclusivo()
                    except Exception as e:
                        print(f"❌ Não foi possível remover arquivos de lock: {e}")
                        return None
        except Exception as e:
            print(f"❌ Erro ao verificar instância existente: {e}")
            return None
            
def liberar_lock(lock_fd):
    """Libera o lock exclusivo"""
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        
        # Tentar remover arquivos de lock
        try:
            os.remove(LOCK_FILE)
            os.remove(PID_FILE)
        except:
            pass
            
        print("🔓 Lock liberado com sucesso")
    except Exception as e:
        print(f"⚠️ Erro ao liberar lock: {e}")

# Carregar variáveis de ambiente
load_dotenv()

# Verificar token antes de importar as libs do telegram
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print('❌ ERRO: Defina TELEGRAM_BOT_TOKEN no arquivo .env')
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
        logger.error(f"Erro ao verificar admin: {e}")
        return False

def add_admin(user_id):
    """Adiciona novo administrador"""
    try:
        with open(ADMINS_FILE, 'a') as f:
            f.write(str(user_id) + '\n')
        return True
    except Exception as e:
        logger.error(f"Erro ao adicionar admin: {e}")
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
        logger.error(f"Erro ao remover admin: {e}")
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
        # Primeiro verificamos o banco com sqlite3 síncrono
        sqlite_conn = sqlite3.connect(DB_PATH, timeout=60.0)
        sqlite_conn.execute('PRAGMA journal_mode = WAL;')  # Modo WAL para melhor concorrência
        sqlite_conn.execute('PRAGMA busy_timeout = 30000;') # 30 segundos de timeout
        sqlite_conn.close()
        
        # Agora conectamos assincronamente
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
        logger.error(f"Erro ao salvar foto: {e}")
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
        logger.error(f"Erro no comando start: {e}")
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
        logger.error(f"Erro no comando menu: {e}")
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
        logger.error(f"Erro no comando ajuda: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abre a interface web"""
    try:
        if not WEBAPP_URL:
            await update.message.reply_text("❌ WebApp não configurado.")
            return
        
        keyboard = [[InlineKeyboardButton("🌐 Abrir Interface Web", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('📱 *Interface Web do Sistema*\nClique no botão abaixo para abrir:', reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro no comando webapp: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

async def buscar_itens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca itens no banco"""
    try:
        if not context.args:
            await update.message.reply_text("🔍 Digite o termo de busca após o comando: `/buscar nome_do_item`", parse_mode='Markdown')
            return
            
        termo = ' '.join(context.args).strip().lower()
        
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Busca por nome, descrição ou catálogo
            query = """
                SELECT id, nome, descricao, catalogo, quantidade, status, foto_path, foto_id
                FROM itens 
                WHERE lower(nome) LIKE ? OR lower(descricao) LIKE ? OR lower(catalogo) LIKE ?
                ORDER BY data_cadastro DESC
            """
            termo_busca = f"%{termo}%"
            cursor = await db.execute(query, (termo_busca, termo_busca, termo_busca))
            resultados = await cursor.fetchall()
            
        if not resultados:
            await update.message.reply_text(f"🔍 Nenhum item encontrado para '{termo}'.")
            return
            
        # Exibir resultados com foto se disponível
        for item in resultados[:10]:  # Limitar a 10 itens
            mensagem = f"*Item #{item['id']}:* {item['nome']}\n"
            mensagem += f"📝 *Descrição:* {item['descricao'] or 'N/A'}\n"
            mensagem += f"📚 *Catálogo:* {item['catalogo'] or 'N/A'}\n"
            mensagem += f"🔢 *Quantidade:* {item['quantidade']}\n"
            mensagem += f"📊 *Status:* {item['status']}\n"
            
            if item['foto_path']:
                # Enviar com foto
                foto_path = os.path.join(FOTOS_DIR, item['foto_path'])
                if os.path.exists(foto_path):
                    await update.message.reply_photo(
                        photo=open(foto_path, 'rb'),
                        caption=mensagem,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"{mensagem}\n⚠️ Foto registrada mas arquivo não encontrado.", parse_mode='Markdown')
            else:
                await update.message.reply_text(mensagem, parse_mode='Markdown')
                
        if len(resultados) > 10:
            await update.message.reply_text(f"⚠️ Exibindo apenas 10 de {len(resultados)} resultados. Refine sua busca para ver mais itens específicos.")
    except Exception as e:
        logger.error(f"Erro ao buscar itens: {e}")
        await update.message.reply_text("❌ Ocorreu um erro na busca. Por favor, tente novamente.")

async def listar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos os itens"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, nome, quantidade, status FROM itens ORDER BY nome"
            )
            itens = await cursor.fetchall()
            
        if not itens:
            await update.message.reply_text("⚠️ Nenhum item cadastrado no sistema.")
            return
            
        resposta = "*📋 Lista de Itens Cadastrados:*\n\n"
        for i, item in enumerate(itens, 1):
            emoji = "✅" if item['status'].lower() == "disponível" else "🔄"
            resposta += f"{i}. {emoji} *{item['nome']}* - Qtd: {item['quantidade']}\n"
            
            # Enviar em blocos para evitar mensagens muito grandes
            if i % 50 == 0 and i < len(itens):
                await update.message.reply_text(resposta, parse_mode='Markdown')
                resposta = "*📋 Lista de Itens (continuação):*\n\n"
        
        if resposta:
            resposta += f"\n*Total:* {len(itens)} itens\nUse /buscar [nome] para ver detalhes."
            await update.message.reply_text(resposta, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro ao listar itens: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao listar itens. Por favor, tente novamente.")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera relatório de estoque"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Total de itens
            cursor = await db.execute("SELECT COUNT(*) as total FROM itens")
            resultado = await cursor.fetchone()
            total_itens = resultado['total']
            
            # Contagem por status
            cursor = await db.execute(
                "SELECT status, COUNT(*) as contagem FROM itens GROUP BY status"
            )
            status = {row['status']: row['contagem'] for row in await cursor.fetchall()}
            
            # Top 5 itens com maior quantidade
            cursor = await db.execute(
                "SELECT nome, quantidade FROM itens ORDER BY quantidade DESC LIMIT 5"
            )
            maiores = await cursor.fetchall()
            
            # Itens com foto vs sem foto
            cursor = await db.execute(
                "SELECT COUNT(*) as com_foto FROM itens WHERE foto_path IS NOT NULL"
            )
            com_foto = (await cursor.fetchone())['com_foto']
            
        # Montar relatório
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        relatorio = f"*📊 RELATÓRIO DE ESTOQUE - {data_atual}*\n\n"
        relatorio += f"*📦 Total de itens:* {total_itens}\n"
        
        # Status
        relatorio += "\n*Status dos Itens:*\n"
        for s, count in status.items():
            emoji = "✅" if s.lower() == "disponível" else "🔄"
            relatorio += f"{emoji} {s}: {count} itens\n"
        
        # Top 5
        relatorio += "\n*Top 5 - Maior Quantidade:*\n"
        for i, item in enumerate(maiores, 1):
            relatorio += f"{i}. {item['nome']} - {item['quantidade']} unid.\n"
            
        # Fotos
        relatorio += f"\n*📸 Itens com foto:* {com_foto} ({round(com_foto/total_itens*100 if total_itens else 0, 1)}%)"
        relatorio += f"\n*🖼️ Itens sem foto:* {total_itens - com_foto}"
        
        await update.message.reply_text(relatorio, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao gerar relatório. Por favor, tente novamente.")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Faz backup do banco em Excel"""
    try:
        user_id = update.effective_user.id
        if not is_admin(user_id):
            await update.message.reply_text("❌ Acesso negado. Você não é administrador.")
            return
            
        await update.message.reply_text("💾 Gerando backup do banco de dados...")
        
        # Conectar ao banco
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Tabela itens
            cursor = await db.execute("SELECT * FROM itens")
            itens = [dict(row) for row in await cursor.fetchall()]
            
            # Tabela movimentações
            cursor = await db.execute("SELECT * FROM movimentacoes")
            movimentacoes = [dict(row) for row in await cursor.fetchall()]
        
        # Criar DataFrames
        df_itens = pd.DataFrame(itens) if itens else pd.DataFrame()
        df_mov = pd.DataFrame(movimentacoes) if movimentacoes else pd.DataFrame()
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_estoque_{timestamp}.xlsx"
        filepath = os.path.join(os.path.dirname(DB_PATH), filename)
        
        # Criar Excel com múltiplas abas
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            df_itens.to_excel(writer, sheet_name='Itens', index=False)
            df_mov.to_excel(writer, sheet_name='Movimentacoes', index=False)
            
            # Formatação básica
            workbook = writer.book
            fmt_header = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
            
            # Formatar aba de itens
            if not df_itens.empty:
                worksheet = writer.sheets['Itens']
                for col_num, value in enumerate(df_itens.columns.values):
                    worksheet.write(0, col_num, value, fmt_header)
            
            # Formatar aba de movimentações
            if not df_mov.empty:
                worksheet = writer.sheets['Movimentacoes']
                for col_num, value in enumerate(df_mov.columns.values):
                    worksheet.write(0, col_num, value, fmt_header)
        
        # Enviar arquivo
        await update.message.reply_document(
            document=open(filepath, 'rb'),
            filename=filename,
            caption=f"📊 Backup completo do banco - {timestamp}"
        )
    except Exception as e:
        logger.error(f"Erro ao gerar backup: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao gerar backup. Por favor, tente novamente.")

# Funções para gerenciar administradores
async def adminusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia usuários administradores"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Acesso negado. Você não é administrador.")
            return
            
        keyboard = [
            [InlineKeyboardButton("➕ Adicionar Admin", callback_data='add_admin')],
            [InlineKeyboardButton("➖ Remover Admin", callback_data='remove_admin')],
            [InlineKeyboardButton("👥 Listar Admins", callback_data='list_admins')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👑 *Gerenciamento de Administradores*\nEscolha uma opção:", reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro em adminusers: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")

# Handler para botões de callback
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa callbacks de botões"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'buscar_menu':
            await query.message.reply_text("🔍 Digite /buscar seguido do termo para procurar um item.")
        
        elif data == 'listar_todos':
            await listar_todos(query, context)
            
        elif data == 'relatorio_menu':
            await relatorio(query, context)
            
        elif data == 'novo_item_menu':
            await novo_item_inicio(query, context)
            
        elif data == 'editar_item_menu':
            await query.message.reply_text("✏️ Digite /editaritem seguido do ID do item para editar.")
            
        elif data == 'backup_menu':
            await backup(query, context)
        
        elif data == 'add_admin':
            await query.message.reply_text("👑 Envie o ID do usuário que deseja adicionar como administrador.")
            context.user_data['admin_action'] = 'add'
            return ADD_ADMIN
            
        elif data == 'remove_admin':
            await query.message.reply_text("❌ Envie o ID do administrador que deseja remover.")
            context.user_data['admin_action'] = 'remove'
            return REMOVE_ADMIN
            
        elif data == 'list_admins':
            # Listar admins
            try:
                with open(ADMINS_FILE) as f:
                    admins = [line.strip() for line in f if line.strip()]
                
                if not admins:
                    await query.message.reply_text("⚠️ Nenhum administrador registrado.")
                    return
                    
                texto = "*👥 Administradores Registrados:*\n\n"
                for i, admin_id in enumerate(admins, 1):
                    texto += f"{i}. ID: `{admin_id}`\n"
                    
                await query.message.reply_text(texto, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Erro ao listar admins: {e}")
                await query.message.reply_text("❌ Erro ao listar administradores.")
    
    except Exception as e:
        logger.error(f"Erro em handle_callback: {e}")
        await query.message.reply_text("❌ Ocorreu um erro ao processar o comando.")

# Processo de cadastro de novo item
async def novo_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o processo de cadastro de novo item"""
    try:
        user_id = update.effective_user.id
        
        if not is_admin(user_id):
            await update.message.reply_text("❌ Acesso negado. Você não é administrador.")
            return ConversationHandler.END
        
        # Limpar dados anteriores
        context.user_data.clear()
        
        await update.message.reply_text("📝 *Cadastro de Novo Item com FOTO*\n\nDigite o nome do item:", parse_mode='Markdown')
        return NOME_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_inicio: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe nome do item"""
    try:
        nome = update.message.text.strip()
        
        if len(nome) < 3:
            await update.message.reply_text("⚠️ Nome muito curto. Digite pelo menos 3 caracteres:")
            return NOME_ITEM
            
        context.user_data['nome'] = nome
        await update.message.reply_text(f"✅ Nome: *{nome}*\n\nAgora digite a *descrição* do item:", parse_mode='Markdown')
        return DESC_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_nome: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe descrição do item"""
    try:
        descricao = update.message.text.strip()
        context.user_data['descricao'] = descricao
        
        await update.message.reply_text(
            f"✅ Descrição registrada: *{descricao[:20]}...*\n\nAgora digite o *catálogo* do item (ou 'n' se não tiver):",
            parse_mode='Markdown'
        )
        return CATALOGO_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_descricao: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe catálogo do item"""
    try:
        catalogo = update.message.text.strip()
        
        if catalogo.lower() in ['n', 'nao', 'não', '-']:
            catalogo = None
            
        context.user_data['catalogo'] = catalogo
        
        await update.message.reply_text(
            f"✅ Catálogo: *{catalogo or 'Não informado'}*\n\nAgora digite a *quantidade* do item (número):",
            parse_mode='Markdown'
        )
        return QTD_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_catalogo: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe quantidade do item"""
    try:
        qtd_texto = update.message.text.strip()
        
        try:
            quantidade = int(qtd_texto)
            if quantidade < 0:
                raise ValueError("Quantidade negativa")
        except ValueError:
            await update.message.reply_text("⚠️ Digite uma quantidade válida (número inteiro positivo):")
            return QTD_ITEM
            
        context.user_data['quantidade'] = quantidade
        context.user_data['status'] = 'Disponível' if quantidade > 0 else 'Indisponível'
        
        await update.message.reply_text(
            f"✅ Quantidade: *{quantidade}*\n"
            f"Status: *{context.user_data['status']}*\n\n"
            f"🖼️ Por favor, envie uma *foto* do item.\n"
            f"Ou digite 'pular' para cadastrar sem foto.",
            parse_mode='Markdown'
        )
        return FOTO_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_quantidade: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def novo_item_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe foto do item ou finaliza cadastro sem foto"""
    try:
        if update.message.text and update.message.text.lower() in ['pular', 'skip', 'n', 'nao', 'não']:
            # Pular foto
            context.user_data['foto_path'] = None
            context.user_data['foto_id'] = None
            
            return await finalizar_cadastro(update, context)
            
        elif update.message.photo:
            # Processar foto
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            foto_path = await salvar_foto(photo_file, context.user_data['nome'])
            
            if foto_path:
                context.user_data['foto_path'] = foto_path
                context.user_data['foto_id'] = update.message.photo[-1].file_id
                
                return await finalizar_cadastro(update, context)
            else:
                await update.message.reply_text(
                    "❌ Erro ao salvar foto. Tente novamente ou digite 'pular' para cadastrar sem foto:"
                )
                return FOTO_ITEM
        else:
            # Mensagem inválida
            await update.message.reply_text(
                "⚠️ Por favor, envie uma foto ou digite 'pular' para cadastrar sem foto."
            )
            return FOTO_ITEM
    except Exception as e:
        logger.error(f"Erro em novo_item_foto: {e}")
        await update.message.reply_text("❌ Ocorreu um erro. Por favor, tente novamente.")
        return ConversationHandler.END

async def finalizar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finaliza o cadastro salvando no banco"""
    try:
        # Dados do item
        nome = context.user_data['nome']
        descricao = context.user_data['descricao']
        catalogo = context.user_data['catalogo']
        quantidade = context.user_data['quantidade']
        status = context.user_data['status']
        foto_path = context.user_data.get('foto_path')
        foto_id = context.user_data.get('foto_id')
        
        # Salvar no banco
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                '''
                INSERT INTO itens (nome, descricao, catalogo, quantidade, status, foto_path, foto_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (nome, descricao, catalogo, quantidade, status, foto_path, foto_id)
            )
            item_id = cursor.lastrowid
            
            # Registrar movimentação
            user_name = update.effective_user.first_name
            await db.execute(
                '''
                INSERT INTO movimentacoes (item_id, usuario, acao, detalhes)
                VALUES (?, ?, ?, ?)
                ''',
                (item_id, user_name, "cadastro", f"Cadastro inicial - Qtd: {quantidade}")
            )
            
            await db.commit()
        
        # Responder usuário
        await update.message.reply_text(
            f"✅ Item cadastrado com sucesso!\n\n"
            f"*ID:* {item_id}\n"
            f"*Nome:* {nome}\n"
            f"*Quantidade:* {quantidade}\n"
            f"*Foto:* {'✅ Sim' if foto_path else '❌ Não'}\n",
            parse_mode='Markdown'
        )
        
        # Se tiver foto, mostrar
        if foto_path and os.path.exists(os.path.join(FOTOS_DIR, foto_path)):
            await update.message.reply_photo(
                photo=open(os.path.join(FOTOS_DIR, foto_path), 'rb'),
                caption=f"📸 Foto do item: {nome}"
            )
        
        # Limpar dados
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erro ao finalizar cadastro: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao salvar o item. Por favor, tente novamente.")
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela qualquer processo de conversação"""
    try:
        context.user_data.clear()
        await update.message.reply_text("❌ Operação cancelada pelo usuário.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Erro em cancelar: {e}")
        return ConversationHandler.END

async def error_handler(update, context):
    """Manipulador global de erros"""
    logger.error(f"Erro não tratado: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro interno no sistema. Por favor, tente novamente mais tarde."
            )
    except:
        pass

def signal_handler(sig, frame):
    """Handler para sinais de interrupção"""
    print("\n⚠️ Sinal de interrupção recebido. Encerrando bot...")
    sys.exit(0)

async def init():
    """Função de inicialização do banco e outros recursos"""
    try:
        # Inicializar banco de dados
        await init_database()
        return True
    except Exception as e:
        print(f"❌ Erro fatal na inicialização: {e}")
        return False

def main():
    """Função principal"""
    try:
        print("🚀 Iniciando Bot Completo com FOTOS...")
        print(f"🔑 Token: {TOKEN[:10]}...")
        print(f"🌐 WebApp: {WEBAPP_URL}")
        print(f"👑 Admins: {ADMINS_FILE}")
        print(f"📸 Fotos: {FOTOS_DIR}")
        
        # Verificar instância única
        lock_fd = obter_lock_exclusivo()
        if not lock_fd:
            print("❌ Outra instância do bot já está em execução. Saindo.")
            sys.exit(1)
            
        # Registrar handlers de sinais
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar recursos no loop de eventos
        loop = asyncio.new_event_loop()
        if not loop.run_until_complete(init()):
            print("❌ Falha na inicialização. Saindo.")
            sys.exit(1)
        
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
        app.add_handler(CommandHandler('adminusers', adminusers))
        app.add_handler(CommandHandler('backup', backup))
        app.add_handler(conv_handler)
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Bot com FOTOS iniciado!")
        print("📋 Comandos registrados:")
        print("   • /start, /menu, /ajuda")
        print("   • /buscar, /listar, /relatorio") 
        print("   • /novoitem (COM FOTOS), /webapp")
        print("   • /adminusers, /backup")
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
