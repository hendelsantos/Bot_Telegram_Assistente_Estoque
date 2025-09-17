#!/usr/bin/env python3
"""
Bot Telegram com Funcionalidade de FOTOS - Sistema Completo de Estoque
Versão com upload, armazenamento e exibição de fotos dos itens
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import json
import asyncio
import uuid

# Carregar variáveis de ambiente
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
import aiosqlite
import pandas as pd

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
    except:
        return False

def add_admin(user_id):
    """Adiciona novo administrador"""
    try:
        with open(ADMINS_FILE, 'a') as f:
            f.write(str(user_id) + '\n')
        return True
    except:
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
    except:
        return False

async def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Tabela principal com campos para fotos e catálogo
        await db.execute('''
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
        await db.execute('''
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
        
        await db.commit()

async def salvar_foto(photo_file, item_nome):
    """Salva a foto no diretório e retorna o caminho"""
    try:
        # Gerar nome único para a foto
        filename = f"{uuid.uuid4().hex}_{item_nome.replace(' ', '_')[:30]}.jpg"
        filepath = os.path.join(FOTOS_DIR, filename)
        
        # Baixar e salvar foto
        await photo_file.download_to_drive(filepath)
        return filename
    except Exception as e:
        logging.error(f"Erro ao salvar foto: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
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
    texto += '• /ajuda - ❓ Ver comandos\n\n'
    texto += '🆕 *NOVIDADE:* Agora você pode cadastrar itens com fotos!'
    
    await update.message.reply_text(texto, parse_mode='Markdown')

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal com botões"""
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
            [InlineKeyboardButton("📸 Novo Item (com foto)", callback_data='novo_item_menu')],
            [InlineKeyboardButton("✏️ Editar Item", callback_data='editar_item_menu')],
            [InlineKeyboardButton("💾 Backup", callback_data='backup_menu')],
            [InlineKeyboardButton("👥 Gerenciar Admins", callback_data='admin_users_menu')],
        ])
    
    keyboard.append([InlineKeyboardButton("📱 WebApp", callback_data='webapp_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '📸 *Menu Principal - Sistema com Fotos*\n\nEscolha uma opção:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def buscar_itens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buscar itens no estoque com foto"""
    if not context.args:
        await update.message.reply_text(
            '🔍 *Como usar:*\n\n'
            '`/buscar termo_de_busca`\n\n'
            'Exemplo: `/buscar mouse`',
            parse_mode='Markdown'
        )
        return
    
    termo = ' '.join(context.args)
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                'SELECT id, nome, descricao, catalogo, quantidade, status, foto_path FROM itens '
                'WHERE nome LIKE ? OR descricao LIKE ? OR catalogo LIKE ? LIMIT 10',
                (f'%{termo}%', f'%{termo}%', f'%{termo}%')
            )
            resultados = await cursor.fetchall()
        
        if not resultados:
            await update.message.reply_text(f'❌ Nenhum item encontrado para: *{termo}*', 
                                          parse_mode='Markdown')
            return
        
        for i, item in enumerate(resultados, 1):
            status_emoji = '✅' if item[5] == 'ativo' else '⚠️'
            foto_emoji = '📸' if item[6] else '📄'
            
            texto = f'{i}. {status_emoji} {foto_emoji} *{item[1]}*\n'
            if item[2]:  # descrição
                texto += f'   📝 {item[2][:80]}...\n' if len(item[2]) > 80 else f'   📝 {item[2]}\n'
            if item[3]:  # catálogo
                texto += f'   📋 Catálogo: {item[3]}\n'
            texto += f'   📦 Qtd: {item[4]} | 🆔 ID: {item[0]}\n'
            
            # Enviar foto se existir
            if item[6]:  # foto_path
                foto_path = os.path.join(FOTOS_DIR, item[6])
                if os.path.exists(foto_path):
                    try:
                        with open(foto_path, 'rb') as foto:
                            await update.message.reply_photo(
                                photo=foto,
                                caption=texto,
                                parse_mode='Markdown'
                            )
                    except:
                        await update.message.reply_text(texto, parse_mode='Markdown')
                else:
                    await update.message.reply_text(texto, parse_mode='Markdown')
            else:
                await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro na busca: {e}")
        await update.message.reply_text('❌ Erro ao buscar itens.')

async def listar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listar todos os itens"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                'SELECT id, nome, catalogo, quantidade, status, foto_path FROM itens ORDER BY nome LIMIT 20'
            )
            itens = await cursor.fetchall()
        
        if not itens:
            await update.message.reply_text('📦 Nenhum item cadastrado ainda.')
            return
        
        texto = '📦 *Todos os Itens*\n\n'
        for i, item in enumerate(itens, 1):
            status_emoji = '✅' if item[4] == 'ativo' else '⚠️'
            foto_emoji = '📸' if item[5] else '📄'
            catalogo_info = f' | 📋 {item[2]}' if item[2] else ''
            
            texto += f'{i}. {status_emoji} {foto_emoji} *{item[1]}*\n'
            texto += f'   📦 Qtd: {item[3]} | 🆔 ID: {item[0]}{catalogo_info}\n\n'
        
        if len(itens) == 20:
            texto += '\n_Mostrando primeiros 20 itens. Use /buscar para encontrar itens específicos._'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro ao listar: {e}")
        await update.message.reply_text('❌ Erro ao listar itens.')

# =============================================================================
# FUNCIONALIDADES ADMINISTRATIVAS COM FOTOS
# =============================================================================

async def novo_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia cadastro de novo item com foto"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        '📸 *Cadastrar Novo Item com Foto*\n\n'
        'Digite o *nome* do item:\n\n'
        '💡 _Use /cancelar para cancelar a operação_',
        parse_mode='Markdown'
    )
    return NOME_ITEM

async def novo_item_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome do item"""
    context.user_data['nome'] = update.message.text
    await update.message.reply_text(
        f'✅ Nome: *{update.message.text}*\n\n'
        'Agora digite a *descrição* do item:',
        parse_mode='Markdown'
    )
    return DESC_ITEM

async def novo_item_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a descrição do item"""
    context.user_data['descricao'] = update.message.text
    await update.message.reply_text(
        f'✅ Descrição: *{update.message.text}*\n\n'
        'Digite o *catálogo/código* do item (opcional, digite "skip" para pular):',
        parse_mode='Markdown'
    )
    return CATALOGO_ITEM

async def novo_item_catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o catálogo do item"""
    catalogo = None if update.message.text.lower() == 'skip' else update.message.text
    context.user_data['catalogo'] = catalogo
    
    catalogo_texto = catalogo if catalogo else "Não informado"
    await update.message.reply_text(
        f'✅ Catálogo: *{catalogo_texto}*\n\n'
        'Digite a *quantidade* inicial:',
        parse_mode='Markdown'
    )
    return QTD_ITEM

async def novo_item_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a quantidade e solicita foto"""
    try:
        quantidade = int(update.message.text)
        context.user_data['quantidade'] = quantidade
        
        await update.message.reply_text(
            f'✅ Quantidade: *{quantidade}*\n\n'
            '📸 Agora envie uma *foto* do item ou digite "skip" para cadastrar sem foto:',
            parse_mode='Markdown'
        )
        return FOTO_ITEM
        
    except ValueError:
        await update.message.reply_text(
            '❌ Digite um número válido para a quantidade.\n\n'
            'Exemplo: 10'
        )
        return QTD_ITEM

async def novo_item_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a foto e salva o item"""
    foto_path = None
    foto_id = None
    
    # Se enviou foto
    if update.message.photo:
        # Pegar a maior resolução
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        foto_id = photo.file_id
        
        # Salvar foto
        foto_path = await salvar_foto(photo_file, context.user_data['nome'])
        
        if not foto_path:
            await update.message.reply_text('❌ Erro ao salvar foto. Item será cadastrado sem foto.')
    
    # Se digitou "skip" ou não enviou foto
    elif update.message.text and update.message.text.lower() == 'skip':
        pass  # foto_path permanece None
    else:
        await update.message.reply_text(
            '❌ Envie uma foto ou digite "skip" para pular.'
        )
        return FOTO_ITEM
    
    # Salvar no banco
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO itens (nome, descricao, catalogo, quantidade, status, foto_path, foto_id, data_cadastro)
                VALUES (?, ?, ?, ?, 'ativo', ?, ?, ?)
            ''', (
                context.user_data['nome'],
                context.user_data['descricao'],
                context.user_data.get('catalogo'),
                context.user_data['quantidade'],
                foto_path,
                foto_id,
                datetime.now().isoformat()
            ))
            await db.commit()
            
            # Obter ID do item criado
            cursor = await db.execute('SELECT last_insert_rowid()')
            item_id = (await cursor.fetchone())[0]
        
        foto_emoji = '📸' if foto_path else '📄'
        catalogo_info = f'\n📋 Catálogo: {context.user_data.get("catalogo")}' if context.user_data.get('catalogo') else ''
        
        texto = (
            f'✅ {foto_emoji} *Item cadastrado com sucesso!*\n\n'
            f'🆔 ID: {item_id}\n'
            f'📝 Nome: {context.user_data["nome"]}\n'
            f'📄 Descrição: {context.user_data["descricao"]}{catalogo_info}\n'
            f'📦 Quantidade: {context.user_data["quantidade"]}\n'
            f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n\n'
            f'Use /menu para ver mais opções'
        )
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logging.error(f"Erro ao salvar item: {e}")
        await update.message.reply_text('❌ Erro ao cadastrar item.')
        return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela a operação atual"""
    context.user_data.clear()
    await update.message.reply_text(
        '❌ Operação cancelada.\n\n'
        'Use /menu para ver as opções disponíveis.'
    )
    return ConversationHandler.END

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerar relatório do estoque com estatísticas de fotos"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Estatísticas gerais
            cursor = await db.execute('SELECT COUNT(*) FROM itens')
            total_itens = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT SUM(quantidade) FROM itens WHERE status = "ativo"')
            quantidade_total = (await cursor.fetchone())[0] or 0
            
            cursor = await db.execute('SELECT COUNT(*) FROM itens WHERE quantidade < 5 AND status = "ativo"')
            estoque_baixo = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM itens WHERE foto_path IS NOT NULL')
            itens_com_foto = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM itens WHERE foto_path IS NULL')
            itens_sem_foto = (await cursor.fetchone())[0]
            
            # Maiores estoques
            cursor = await db.execute(
                'SELECT nome, quantidade, foto_path FROM itens WHERE status = "ativo" '
                'ORDER BY quantidade DESC LIMIT 5'
            )
            maiores_estoques = await cursor.fetchall()
            
            # Menores estoques
            cursor = await db.execute(
                'SELECT nome, quantidade, foto_path FROM itens WHERE status = "ativo" AND quantidade > 0 '
                'ORDER BY quantidade ASC LIMIT 5'
            )
            menores_estoques = await cursor.fetchall()
        
        texto = (
            f'📊 *Relatório Completo do Estoque*\n\n'
            f'• 📦 Total de itens: {total_itens}\n'
            f'• 🔢 Quantidade total: {quantidade_total}\n'
            f'• ⚠️ Estoque baixo: {estoque_baixo}\n'
            f'• 📸 Itens com foto: {itens_com_foto}\n'
            f'• 📄 Itens sem foto: {itens_sem_foto}\n\n'
        )
        
        if maiores_estoques:
            texto += '🔝 *Maiores Estoques:*\n'
            for item in maiores_estoques:
                foto_emoji = '📸' if item[2] else '📄'
                texto += f'   {foto_emoji} {item[0]}: {item[1]}\n'
            texto += '\n'
        
        if menores_estoques:
            texto += '⚠️ *Menores Estoques:*\n'
            for item in menores_estoques:
                foto_emoji = '📸' if item[2] else '📄'
                texto += f'   {foto_emoji} {item[0]}: {item[1]}\n'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro no relatório: {e}")
        await update.message.reply_text('❌ Erro ao gerar relatório.')

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de ajuda"""
    user_id = update.effective_user.id
    
    texto = '❓ *Comandos Disponíveis*\n\n'
    texto += '*Comandos Gerais:*\n'
    texto += '• `/start` - Iniciar o bot\n'
    texto += '• `/menu` - Menu principal interativo\n'
    texto += '• `/buscar <termo>` - Buscar itens no estoque\n'
    texto += '• `/listar` - Listar todos os itens\n'
    texto += '• `/relatorio` - Relatório completo do estoque\n'
    texto += '• `/webapp` - Abrir interface web\n'
    texto += '• `/ajuda` - Mostrar esta ajuda\n\n'
    
    if is_admin(user_id):
        texto += '*Comandos Administrativos:*\n'
        texto += '• `/novoitem` - Cadastrar novo item COM FOTO\n'
        texto += '• `/editaritem` - Editar item existente\n'
        texto += '• `/deletaritem` - Deletar item\n'
        texto += '• `/backup` - Fazer backup do banco\n'
        texto += '• `/adminusers` - Gerenciar administradores\n\n'
    
    texto += '📸 *NOVIDADE:* Sistema com suporte a fotos!\n'
    texto += 'Agora você pode cadastrar itens com fotos para facilitar a identificação.'
    
    await update.message.reply_text(texto, parse_mode='Markdown')

async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /webapp"""
    if WEBAPP_URL.startswith('https://'):
        keyboard = [[InlineKeyboardButton(
            "📱 Abrir WebApp",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            '📱 *Interface WebApp*\n\nClique no botão abaixo para abrir:',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            '⚠️ *WebApp não disponível*\n\n'
            'O Telegram WebApp requer HTTPS.\n'
            'Configure uma URL HTTPS para usar esta funcionalidade.\n\n'
            'Enquanto isso, use os comandos do bot:\n'
            '• `/menu` - Menu principal\n'
            '• `/buscar` - Buscar itens\n'
            '• `/novoitem` - Cadastrar item com foto',
            parse_mode='Markdown'
        )

# =============================================================================
# HANDLERS DE CALLBACK
# =============================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'buscar_menu':
        await query.edit_message_text(
            '🔍 *Buscar Itens*\n\n'
            'Digite: `/buscar termo_de_busca`\n\n'
            'Exemplo: `/buscar mouse`',
            parse_mode='Markdown'
        )
    
    elif query.data == 'listar_todos':
        await listar_todos(query, context)
    
    elif query.data == 'relatorio_menu':
        await relatorio(query, context)
    
    elif query.data == 'novo_item_menu':
        if is_admin(query.from_user.id):
            await query.edit_message_text(
                '📸 *Cadastrar Novo Item*\n\n'
                'Use o comando: `/novoitem`\n\n'
                'O sistema irá guiá-lo pelo processo de cadastro com foto!'
            )
        else:
            await query.edit_message_text('❌ Acesso negado. Apenas administradores.')
    
    elif query.data == 'webapp_menu':
        await webapp_command(query, context)

# =============================================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# =============================================================================

def main():
    """Função principal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print('❌ Defina TELEGRAM_BOT_TOKEN')
        return
    
    print(f'🚀 Iniciando Bot Completo com FOTOS...')
    print(f'🔑 Token: {TOKEN[:10]}...')
    print(f'🌐 WebApp: {WEBAPP_URL}')
    print(f'👑 Admins: {ADMINS_FILE}')
    print(f'📸 Fotos: {FOTOS_DIR}')
    
    app = ApplicationBuilder().token(TOKEN).build()
    
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
    
    # Inicializar banco e rodar bot
    async def init_and_run():
        await init_database()
    
    asyncio.run(init_and_run())
    app.run_polling()

if __name__ == '__main__':
    main()
