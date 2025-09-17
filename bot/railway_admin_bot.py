#!/usr/bin/env python3
"""
Bot Administrativo do Telegram para Railway
Versão completa com funcionalidades administrativas
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import asyncio

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import aiosqlite
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Constantes
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
FOTOS_DIR = os.path.join(os.path.dirname(__file__), '../fotos')
ADMINS_FILE = os.path.join(os.path.dirname(__file__), 'admins.txt')

# URL do WebApp (configurar com sua URL pública)
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8080')

# Estados para ConversationHandler
FOTO, NOME, DESCRICAO, QUANTIDADE, CONFIRMACAO = range(5)
BUSCA_ESCOLHA = range(100, 101)
ATUAL_ESCOLHA, ATUAL_NOME, ATUAL_DESC, ATUAL_QTD, ATUAL_FOTO = range(200, 205)
ADMIN_ADD_USER, ADMIN_REMOVE_USER = range(300, 302)

def is_admin(user_id):
    """Verifica se o usuário é administrador"""
    try:
        if not os.path.exists(ADMINS_FILE):
            # Criar arquivo com o primeiro admin (você)
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
    """Adiciona um novo administrador"""
    try:
        with open(ADMINS_FILE, 'a') as f:
            f.write(str(user_id) + '\n')
        return True
    except Exception as e:
        logging.error(f"Erro ao adicionar admin: {e}")
        return False

def remove_admin(user_id):
    """Remove um administrador"""
    try:
        with open(ADMINS_FILE, 'r') as f:
            admins = [line.strip() for line in f if line.strip()]
        
        if str(user_id) in admins:
            admins.remove(str(user_id))
            with open(ADMINS_FILE, 'w') as f:
                for admin in admins:
                    f.write(admin + '\n')
            return True
        return False
    except Exception as e:
        logging.error(f"Erro ao remover admin: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    
    texto = (
        '🤖 *Assistente de Estoque - Versão Administrativa Railway*\n\n'
        f'Olá {update.effective_user.first_name}!\n\n'
    )
    
    if is_user_admin:
        texto += (
            '👑 *Você é ADMINISTRADOR*\n\n'
            '🔧 Comandos Administrativos:\n'
            '• /admin_menu - Menu administrativo\n'
            '• /novo_item - Cadastrar item\n'
            '• /editar_item - Editar item\n'
            '• /admin_users - Gerenciar admins\n'
            '• /backup - Backup do banco\n\n'
        )
    
    texto += (
        '📱 Comandos Gerais:\n'
        '• /menu - Menu principal\n'
        '• /buscar - Buscar itens\n'
        '• /relatorio - Relatório\n'
        '• /webapp - Interface web\n'
        '• /ajuda - Ver todos os comandos'
    )
    
    await update.message.reply_text(texto, parse_mode='Markdown')

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Novo Item", callback_data='admin_novo_item')],
        [InlineKeyboardButton("✏️ Editar Item", callback_data='admin_editar_item')],
        [InlineKeyboardButton("👥 Gerenciar Admins", callback_data='admin_users')],
        [InlineKeyboardButton("💾 Backup Banco", callback_data='admin_backup')],
        [InlineKeyboardButton("📊 Estatísticas", callback_data='admin_stats')],
        [InlineKeyboardButton("🔧 Manutenção", callback_data='admin_manutencao')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '👑 *Menu Administrativo*\n\nEscolha uma opção:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Buscar Item", callback_data='buscar')],
        [InlineKeyboardButton("📱 WebApp", callback_data='webapp')],
        [InlineKeyboardButton("📊 Relatório", callback_data='relatorio')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')]
    ]
    
    if is_admin(update.effective_user.id):
        keyboard.insert(0, [InlineKeyboardButton("👑 Admin Menu", callback_data='admin_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Escolha uma opção:', reply_markup=reply_markup)

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            '🔍 *Buscar Itens*\n\n'
            'Use: `/buscar <palavra-chave>`\n\n'
            'Exemplos:\n'
            '• `/buscar notebook`\n'
            '• `/buscar mouse`\n'
            '• `/buscar impressora`',
            parse_mode='Markdown'
        )
        return
    
    termo = ' '.join(context.args)
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                'SELECT id, nome, descricao, quantidade, status FROM itens '
                'WHERE nome LIKE ? OR descricao LIKE ? LIMIT 10',
                (f'%{termo}%', f'%{termo}%')
            )
            resultados = await cursor.fetchall()
        
        if not resultados:
            await update.message.reply_text(f'❌ Nenhum item encontrado para: *{termo}*', parse_mode='Markdown')
            return
        
        texto = f'🔍 *Resultados para: {termo}*\n\n'
        for item in resultados:
            status_emoji = '✅' if item[4] == 'ativo' else '⚠️'
            texto += f'{status_emoji} *{item[1]}*\n'
            if item[2]:
                texto += f'   📝 {item[2][:50]}...\n'
            texto += f'   📦 Quantidade: {item[3]}\n'
            texto += f'   🆔 ID: {item[0]}\n\n'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro na busca: {e}")
        await update.message.reply_text('❌ Erro ao buscar itens. Tente novamente.')

async def novo_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        '➕ *Cadastrar Novo Item*\n\n'
        'Digite o *nome* do item:',
        parse_mode='Markdown'
    )
    return NOME

async def novo_item_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nome'] = update.message.text
    await update.message.reply_text(
        f'Nome: *{update.message.text}*\n\n'
        'Agora digite a *descrição* do item:',
        parse_mode='Markdown'
    )
    return DESCRICAO

async def novo_item_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['descricao'] = update.message.text
    await update.message.reply_text(
        f'Descrição: *{update.message.text}*\n\n'
        'Digite a *quantidade* inicial:',
        parse_mode='Markdown'
    )
    return QUANTIDADE

async def novo_item_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantidade = int(update.message.text)
        context.user_data['quantidade'] = quantidade
        
        # Salvar no banco
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO itens (nome, descricao, quantidade, status, data_cadastro)
                VALUES (?, ?, ?, 'ativo', ?)
            ''', (
                context.user_data['nome'],
                context.user_data['descricao'],
                quantidade,
                datetime.now().isoformat()
            ))
            await db.commit()
        
        texto = (
            '✅ *Item cadastrado com sucesso!*\n\n'
            f'📝 Nome: {context.user_data["nome"]}\n'
            f'📄 Descrição: {context.user_data["descricao"]}\n'
            f'📦 Quantidade: {quantidade}\n'
            f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        )
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text('❌ Digite um número válido para a quantidade.')
        return QUANTIDADE
    except Exception as e:
        logging.error(f"Erro ao salvar item: {e}")
        await update.message.reply_text('❌ Erro ao salvar item. Tente novamente.')
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Operação cancelada.')
    context.user_data.clear()
    return ConversationHandler.END

async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado.')
        return
    
    try:
        # Fazer backup do banco
        backup_path = f'backup_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Exportar dados
            cursor = await db.execute('SELECT * FROM itens')
            items = await cursor.fetchall()
        
        # Criar arquivo de backup em JSON
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'total_items': len(items),
            'items': [
                {
                    'id': item[0],
                    'nome': item[1],
                    'descricao': item[2],
                    'quantidade': item[3],
                    'status': item[4],
                    'data_cadastro': item[5]
                }
                for item in items
            ]
        }
        
        backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        await update.message.reply_text(
            f'💾 *Backup Realizado*\n\n'
            f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'
            f'📦 Total de itens: {len(items)}\n\n'
            f'```json\n{backup_json[:1000]}...\n```',
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logging.error(f"Erro no backup: {e}")
        await update.message.reply_text('❌ Erro ao fazer backup.')

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Total de itens
            cursor = await db.execute('SELECT COUNT(*) FROM itens')
            total = (await cursor.fetchone())[0]
            
            # Itens ativos
            cursor = await db.execute("SELECT COUNT(*) FROM itens WHERE status = 'ativo'")
            ativos = (await cursor.fetchone())[0]
            
            # Quantidade total
            cursor = await db.execute('SELECT SUM(quantidade) FROM itens')
            qtd_total = (await cursor.fetchone())[0] or 0
            
            # Estoque baixo
            cursor = await db.execute('SELECT COUNT(*) FROM itens WHERE quantidade < 5')
            estoque_baixo = (await cursor.fetchone())[0]
            
            # Itens mais recentes
            cursor = await db.execute('SELECT nome FROM itens ORDER BY data_cadastro DESC LIMIT 3')
            recentes = await cursor.fetchall()
        
        texto = (
            f'📊 *Relatório do Estoque*\n\n'
            f'📦 Total de itens: {total}\n'
            f'✅ Itens ativos: {ativos}\n'
            f'📋 Quantidade total: {qtd_total}\n'
            f'⚠️ Estoque baixo: {estoque_baixo}\n\n'
            f'🆕 Últimos cadastrados:\n'
        )
        
        for item in recentes:
            texto += f'• {item[0]}\n'
        
        texto += f'\n📅 Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro no relatório: {e}")
        await update.message.reply_text('❌ Erro ao gerar relatório.')

async def webapp_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WEBAPP_URL.startswith('https://'):
        await update.message.reply_text(
            '⚠️ *WebApp não disponível*\n\n'
            'O Telegram WebApp requer HTTPS. Configure uma URL HTTPS para usar esta funcionalidade.',
            parse_mode='Markdown'
        )
        return
    
    keyboard = [[InlineKeyboardButton(
        text="📱 Abrir WebApp",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '📱 *Interface WebApp*\n\nClique no botão abaixo:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Callbacks dos botões
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'admin_menu':
        if is_admin(query.from_user.id):
            await admin_menu(query, context)
        else:
            await query.edit_message_text('❌ Acesso negado.')
    
    elif query.data == 'admin_novo_item':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                '➕ *Cadastrar Novo Item*\n\n'
                'Use o comando: `/novo_item`',
                parse_mode='Markdown'
            )
    
    elif query.data == 'admin_backup':
        if is_admin(query.from_user.id):
            await admin_backup(query, context)
    
    elif query.data == 'buscar':
        await query.edit_message_text(
            '🔍 *Buscar Itens*\n\n'
            'Use: `/buscar <palavra-chave>`',
            parse_mode='Markdown'
        )
    
    elif query.data == 'webapp':
        await webapp_comando(query, context)
    
    elif query.data == 'relatorio':
        await relatorio(query, context)

def main():
    logging.basicConfig(level=logging.INFO)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print('❌ Defina a variável de ambiente TELEGRAM_BOT_TOKEN')
        return
    
    print(f'🚀 Iniciando Bot Administrativo Railway...')
    print(f'🔑 Token configurado: {TOKEN[:10]}...')
    print(f'🌐 WebApp URL: {WEBAPP_URL}')
    print(f'👑 Arquivo de admins: {ADMINS_FILE}')
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation Handler para novo item
    novo_item_handler = ConversationHandler(
        entry_points=[CommandHandler('novo_item', novo_item_inicio)],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_nome)],
            DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_descricao)],
            QUANTIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_quantidade)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Comandos
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CommandHandler('admin_menu', admin_menu))
    app.add_handler(CommandHandler('buscar', buscar))
    app.add_handler(CommandHandler('relatorio', relatorio))
    app.add_handler(CommandHandler('webapp', webapp_comando))
    app.add_handler(novo_item_handler)
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print('✅ Bot Administrativo Railway iniciado com sucesso!')
    app.run_polling()

if __name__ == '__main__':
    main()
