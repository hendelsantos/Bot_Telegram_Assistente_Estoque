#!/usr/bin/env python3
"""
Bot do Telegram para Railway
Versão simplificada sem dependências problemáticas
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import aiosqlite
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json

# Constantes
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
FOTOS_DIR = os.path.join(os.path.dirname(__file__), '../fotos')

# URL do WebApp (configurar com sua URL pública)
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8080')

# Estados para ConversationHandler
FOTO, NOME, DESCRICAO, QUANTIDADE, CONFIRMACAO = range(5)
BUSCA_ESCOLHA = range(100, 101)
ATUAL_ESCOLHA, ATUAL_NOME, ATUAL_DESC, ATUAL_QTD, ATUAL_FOTO = range(200, 205)

def is_admin(user_id):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'admins.txt')) as f:
            admins = [line.strip() for line in f if line.strip()]
        return str(user_id) in admins
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🤖 *Assistente de Estoque - Versão Railway*\n\n'
        'Olá! Eu sou seu assistente de estoque.\n\n'
        '📱 Use /menu para ver as opções disponíveis\n'
        '🔍 Use /buscar para procurar itens\n'
        '📊 Use /webapp para interface completa\n'
        '❓ Use /ajuda para ver todos os comandos',
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
        keyboard.insert(1, [InlineKeyboardButton("➕ Novo Item", callback_data='novoitem')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Escolha uma opção:', reply_markup=reply_markup)

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        '🤖 *Assistente de Estoque - Railway*\n\n'
        '*Comandos Principais:*\n'
        '/menu - Menu rápido com botões\n'
        '/webapp - 📱 Abrir WebApp\n'
        '/buscar <palavra> - Buscar itens\n'
        '/relatorio - Relatório do estoque\n'
        '/ajuda - Esta mensagem\n\n'
        '*Comandos Admin:*\n'
        '/novoitem - Cadastrar novo item\n\n'
        '💡 *Dica:* Use o WebApp para funcionalidades completas!'
    )
    await update.message.reply_text(texto, parse_mode='Markdown')

async def webapp_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificar se a URL é HTTPS (requerido pelo Telegram)
    if not WEBAPP_URL.startswith('https://'):
        await update.message.reply_text(
            '⚠️ *WebApp não disponível*\n\n'
            'O Telegram WebApp requer HTTPS. Configure uma URL HTTPS para usar esta funcionalidade.\n\n'
            'Use os comandos do bot como alternativa:\n'
            '• /buscar - Buscar itens\n'
            '• /menu - Menu principal'
        )
        return
    
    # Criar botão do WebApp
    keyboard = [[InlineKeyboardButton(
        text="📱 Abrir WebApp",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '📱 *Interface WebApp*\n\n'
        'Clique no botão abaixo para abrir a interface completa:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

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
        
        texto = (
            f'📊 *Relatório do Estoque*\n\n'
            f'📦 Total de itens: {total}\n'
            f'✅ Itens ativos: {ativos}\n'
            f'📋 Quantidade total: {qtd_total}\n'
            f'⚠️ Estoque baixo: {estoque_baixo}\n\n'
            f'📅 Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        )
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro no relatório: {e}")
        await update.message.reply_text('❌ Erro ao gerar relatório.')

# Callbacks dos botões
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'buscar':
        await query.edit_message_text(
            '🔍 *Buscar Itens*\n\n'
            'Use: `/buscar <palavra-chave>`\n\n'
            'Exemplo: `/buscar notebook`',
            parse_mode='Markdown'
        )
    elif query.data == 'webapp':
        await webapp_comando(query, context)
    elif query.data == 'relatorio':
        await relatorio(query, context)
    elif query.data == 'ajuda':
        await ajuda(query, context)
    elif query.data == 'novoitem':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                '➕ *Cadastrar Novo Item*\n\n'
                '⚠️ Função administrativa não disponível na versão Railway.\n'
                'Use o WebApp para cadastrar novos itens.',
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text('❌ Acesso negado. Apenas administradores.')

def main():
    logging.basicConfig(level=logging.INFO)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print('❌ Defina a variável de ambiente TELEGRAM_BOT_TOKEN')
        return
    
    print(f'🚀 Iniciando Bot Railway...')
    print(f'🔑 Token configurado: {TOKEN[:10]}...')
    print(f'🌐 WebApp URL: {WEBAPP_URL}')
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CommandHandler('ajuda', ajuda))
    app.add_handler(CommandHandler('webapp', webapp_comando))
    app.add_handler(CommandHandler('buscar', buscar))
    app.add_handler(CommandHandler('relatorio', relatorio))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print('✅ Bot Railway iniciado com sucesso!')
    app.run_polling()

if __name__ == '__main__':
    main()
