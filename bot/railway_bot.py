#!/usr/bin/env python3
"""
Versão do bot para Railway - sem dependências de sistema
Remove funcionalidades que dependem de bibliotecas não disponíveis
"""

import os
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import aiosqlite
import pandas as pd
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
REPARO_FORNECEDOR, REPARO_DATA = range(300, 302)
RETORNO_CONFIRMA = 400
EXCLUIR_CONFIRMA = 500
# Estados para Inventário
INVENTARIO_QR, INVENTARIO_QTD, INVENTARIO_CONFIRMA = range(600, 603)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import dos utilitários locais
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from utils.code_generator import CodeGenerator
    from utils.smart_search import SmartSearch
    code_generator = CodeGenerator()
    smart_search = SmartSearch()
    logger.info("✅ Utilitários carregados com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Erro ao carregar utilitários: {e}")
    code_generator = None
    smart_search = None

# Função auxiliar para processar QR codes via texto (sem pyzbar)
def process_qr_text(qr_text):
    """Processa texto de QR code sem usar scanner"""
    try:
        # Tentar decodificar se for JSON
        if qr_text.startswith('{'):
            return json.loads(qr_text)
        else:
            # Tratar como código simples
            return {'code': qr_text}
    except:
        return {'code': qr_text}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start"""
    user = update.effective_user
    logger.info(f"Usuário {user.first_name} iniciou o bot")
    
    welcome_message = f"""
🤖 *Assistente de Estoque - Versão Railway*

Olá {user.first_name}! 

🌐 *WebApp Mobile*
Use /webapp para acessar a interface mobile completa

📱 *Comandos Disponíveis:*
• /adicionar - Cadastrar novo item
• /buscar - Buscar itens 
• /atualizar - Atualizar item existente
• /inventario - Realizar inventário
• /relatorio - Gerar relatórios
• /webapp - Abrir interface mobile

🎯 *Sistema de Códigos Automáticos:*
• NOTE-001, MOUS-001, CABO-001
• Nunca mais memorize IDs numéricos!

🚀 *Rodando em produção no Railway!*
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /webapp - Abre o WebApp mobile"""
    logger.info("Comando /webapp executado")
    
    # Verificar se WEBAPP_URL está configurada
    if not WEBAPP_URL or WEBAPP_URL == 'http://localhost:8080':
        await update.message.reply_text(
            "⚠️ *WebApp não configurado*\n\n"
            "A URL do WebApp ainda não foi configurada.\n"
            "Configure a variável WEBAPP_URL no Railway.",
            parse_mode='Markdown'
        )
        return
    
    keyboard = [
        [InlineKeyboardButton(
            "📱 Abrir WebApp Mobile", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌐 *WebApp Mobile - Sistema de Inventário*\n\n"
        "📱 Interface otimizada para celular\n"
        "📷 Scanner QR em tempo real\n"
        "🔍 Busca inteligente\n"
        "🏷️ Códigos automáticos\n\n"
        "👆 Clique no botão abaixo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Resto das funções do bot permanecem iguais...
# (buscar, adicionar, inventario, etc.)

async def buscar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /buscar"""
    if len(context.args) == 0:
        await update.message.reply_text(
            "🔍 *Como usar a busca:*\n\n"
            "`/buscar mouse` - Buscar por nome\n"
            "`/buscar NOTE-001` - Buscar por código\n"
            "`/buscar notebook` - Buscar categoria\n\n"
            "💡 *Dica:* Use o WebApp mobile para busca visual!\n"
            "Digite: /webapp",
            parse_mode='Markdown'
        )
        return
    
    termo = ' '.join(context.args)
    logger.info(f"Busca realizada: {termo}")
    
    try:
        # Busca básica sem smart_search se não estiver disponível
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                SELECT codigo, nome, descricao, quantidade, categoria, localizacao 
                FROM itens 
                WHERE nome LIKE ? OR codigo LIKE ? OR descricao LIKE ? OR categoria LIKE ?
                ORDER BY nome
            """, (f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%'))
            
            resultados = await cursor.fetchall()
        
        if not resultados:
            await update.message.reply_text(
                f"🚫 Nenhum item encontrado para: *{termo}*\n\n"
                "💡 Experimente:\n"
                "• Termos mais gerais\n"
                "• Categoria do item\n"
                "• Use o WebApp: /webapp",
                parse_mode='Markdown'
            )
            return
        
        # Formatar resultados
        resposta = f"🔍 *Resultados para: {termo}*\n\n"
        
        for i, item in enumerate(resultados[:10], 1):  # Máximo 10 resultados
            codigo, nome, descricao, qtd, categoria, loc = item
            resposta += f"*{i}. {codigo}* - {nome}\n"
            resposta += f"   📦 Qtd: {qtd} | 📍 {loc or 'N/A'}\n"
            if descricao:
                resposta += f"   💬 {descricao[:50]}...\n"
            resposta += "\n"
        
        if len(resultados) > 10:
            resposta += f"... e mais {len(resultados)-10} itens\n\n"
            resposta += "💡 Use o WebApp para ver todos: /webapp"
        
        await update.message.reply_text(resposta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        await update.message.reply_text(
            "❌ Erro ao realizar busca. Tente novamente ou use /webapp"
        )

async def status_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status - Status do sistema"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Total de itens
            cursor = await db.execute("SELECT COUNT(*) FROM itens")
            total_itens = (await cursor.fetchone())[0]
            
            # Itens com estoque baixo
            cursor = await db.execute("SELECT COUNT(*) FROM itens WHERE quantidade < 5")
            estoque_baixo = (await cursor.fetchone())[0]
            
            # Últimos itens adicionados
            cursor = await db.execute("""
                SELECT nome, codigo, data_cadastro 
                FROM itens 
                ORDER BY data_cadastro DESC 
                LIMIT 3
            """)
            ultimos = await cursor.fetchall()
        
        status_msg = f"📊 *Status do Sistema*\n\n"
        status_msg += f"📦 Total de itens: *{total_itens}*\n"
        status_msg += f"⚠️ Estoque baixo: *{estoque_baixo}*\n"
        status_msg += f"🌐 WebApp: {'✅ Ativo' if WEBAPP_URL != 'http://localhost:8080' else '⚠️ Local'}\n\n"
        
        if ultimos:
            status_msg += "🆕 *Últimos adicionados:*\n"
            for nome, codigo, data in ultimos:
                data_formatada = data[:10] if data else 'N/A'
                status_msg += f"• {codigo} - {nome} ({data_formatada})\n"
        
        status_msg += f"\n💡 Acesse o WebApp: /webapp"
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        await update.message.reply_text("❌ Erro ao obter status do sistema.")

def main():
    """Função principal"""
    # Obter token do ambiente
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("❌ BOT_TOKEN não encontrado nas variáveis de ambiente!")
        exit(1)
    
    logger.info("🚀 Iniciando bot Railway (sem pyzbar)...")
    
    # Criar aplicação
    application = ApplicationBuilder().token(token).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('webapp', webapp_command))
    application.add_handler(CommandHandler('buscar', buscar_comando))
    application.add_handler(CommandHandler('status', status_comando))
    
    # Iniciar bot
    logger.info("✅ Bot iniciado com sucesso!")
    logger.info(f"🌐 WebApp URL: {WEBAPP_URL}")
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
