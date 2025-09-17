#!/usr/bin/env python3
"""
Bot Telegram COMPLETO para Railway - Todas as funcionalidades operacionais
Versão com cadastro, edição, busca, relatórios e gestão administrativa
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import json
import asyncio

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

# Estados da conversação
(NOME_ITEM, DESC_ITEM, QTD_ITEM, 
 EDITAR_ESCOLHA, EDITAR_CAMPO, EDITAR_VALOR,
 ADD_ADMIN, REMOVE_ADMIN) = range(8)

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
        with open(ADMINS_FILE, 'r') as f:
            admins = [line.strip() for line in f if line.strip()]
        
        if str(user_id) in admins:
            admins.remove(str(user_id))
            with open(ADMINS_FILE, 'w') as f:
                for admin in admins:
                    f.write(admin + '\n')
            return True
        return False
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    is_user_admin = is_admin(user_id)
    
    texto = f'🤖 *Assistente de Estoque - Sistema Completo*\n\n'
    texto += f'Olá, {user_name}!\n\n'
    
    if is_user_admin:
        texto += '👑 *Você é ADMINISTRADOR*\n\n'
        texto += '*Comandos Administrativos:*\n'
        texto += '• /novoitem - ➕ Cadastrar novo item\n'
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
            [InlineKeyboardButton("➕ Novo Item", callback_data='novo_item_menu')],
            [InlineKeyboardButton("✏️ Editar Item", callback_data='editar_item_menu')],
            [InlineKeyboardButton("💾 Backup", callback_data='backup_menu')],
            [InlineKeyboardButton("👥 Gerenciar Admins", callback_data='admin_users_menu')],
        ])
    
    keyboard.append([InlineKeyboardButton("📱 WebApp", callback_data='webapp_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('📋 *Menu Principal*\n\nEscolha uma opção:', 
                                    reply_markup=reply_markup, parse_mode='Markdown')

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buscar itens"""
    if not context.args:
        await update.message.reply_text(
            '🔍 *Buscar Itens*\n\n'
            'Use: `/buscar <termo>`\n\n'
            'Exemplos:\n'
            '• `/buscar notebook`\n'
            '• `/buscar mouse`',
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
            await update.message.reply_text(f'❌ Nenhum item encontrado para: *{termo}*', 
                                          parse_mode='Markdown')
            return
        
        texto = f'🔍 *Resultados para: {termo}*\n\n'
        for i, item in enumerate(resultados, 1):
            status_emoji = '✅' if item[4] == 'ativo' else '⚠️'
            texto += f'{i}. {status_emoji} *{item[1]}*\n'
            texto += f'   📝 {item[2][:80]}...\n' if item[2] else ''
            texto += f'   📦 Qtd: {item[3]} | 🆔 ID: {item[0]}\n\n'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro na busca: {e}")
        await update.message.reply_text('❌ Erro ao buscar itens.')

async def listar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listar todos os itens"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                'SELECT id, nome, quantidade, status FROM itens ORDER BY nome LIMIT 20'
            )
            itens = await cursor.fetchall()
        
        if not itens:
            await update.message.reply_text('📦 Nenhum item cadastrado ainda.')
            return
        
        texto = '📦 *Todos os Itens*\n\n'
        for i, item in enumerate(itens, 1):
            status_emoji = '✅' if item[3] == 'ativo' else '⚠️'
            texto += f'{i}. {status_emoji} *{item[1]}*\n'
            texto += f'   📦 Qtd: {item[2]} | 🆔 ID: {item[0]}\n\n'
        
        if len(itens) == 20:
            texto += '\n_Mostrando primeiros 20 itens. Use /buscar para encontrar itens específicos._'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro ao listar: {e}")
        await update.message.reply_text('❌ Erro ao listar itens.')

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Relatório completo"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Estatísticas gerais
            cursor = await db.execute('SELECT COUNT(*) FROM itens')
            total = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM itens WHERE status = 'ativo'")
            ativos = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT SUM(quantidade) FROM itens WHERE status = "ativo"')
            qtd_total = (await cursor.fetchone())[0] or 0
            
            cursor = await db.execute('SELECT COUNT(*) FROM itens WHERE quantidade < 5 AND status = "ativo"')
            estoque_baixo = (await cursor.fetchone())[0]
            
            # Itens com maior quantidade
            cursor = await db.execute(
                'SELECT nome, quantidade FROM itens WHERE status = "ativo" '
                'ORDER BY quantidade DESC LIMIT 5'
            )
            top_quantidade = await cursor.fetchall()
            
            # Itens recentes
            cursor = await db.execute(
                'SELECT nome FROM itens ORDER BY data_cadastro DESC LIMIT 5'
            )
            recentes = await cursor.fetchall()
        
        texto = (
            f'📊 *Relatório Completo do Estoque*\n\n'
            f'📈 *Estatísticas Gerais:*\n'
            f'• Total de itens: {total}\n'
            f'• Itens ativos: {ativos}\n'
            f'• Quantidade total: {qtd_total}\n'
            f'• ⚠️ Estoque baixo: {estoque_baixo}\n\n'
        )
        
        if top_quantidade:
            texto += '🔝 *Maiores Estoques:*\n'
            for item in top_quantidade:
                texto += f'• {item[0]}: {item[1]} unidades\n'
            texto += '\n'
        
        if recentes:
            texto += '🆕 *Últimos Cadastrados:*\n'
            for item in recentes:
                texto += f'• {item[0]}\n'
            texto += '\n'
        
        texto += f'📅 Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro no relatório: {e}")
        await update.message.reply_text('❌ Erro ao gerar relatório.')

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ajuda - Lista todos os comandos"""
    user_id = update.effective_user.id
    is_user_admin = is_admin(user_id)
    
    texto = '❓ *Central de Ajuda*\n\n'
    
    texto += '*📋 Comandos Gerais:*\n'
    texto += '• `/menu` - Menu principal com botões\n'
    texto += '• `/buscar <termo>` - Buscar itens no estoque\n'
    texto += '• `/listar` - Listar todos os itens\n'
    texto += '• `/relatorio` - Relatório completo do estoque\n'
    texto += '• `/webapp` - Abrir interface web\n'
    texto += '• `/ajuda` - Esta mensagem de ajuda\n\n'
    
    if is_user_admin:
        texto += '*👑 Comandos Administrativos:*\n'
        texto += '• `/novoitem` - Cadastrar novo item\n'
        texto += '• `/editaritem` - Editar item existente\n'
        texto += '• `/deletaritem` - Deletar item\n'
        texto += '• `/backup` - Fazer backup do banco\n'
        texto += '• `/adminusers` - Gerenciar administradores\n\n'
        
        texto += '*💡 Dicas Administrativas:*\n'
        texto += '• Use o menu `/menu` para acesso rápido\n'
        texto += '• Comandos de edição funcionam por ID ou nome\n'
        texto += '• Backup é salvo em formato JSON\n\n'
    
    texto += '*🔍 Exemplos de Uso:*\n'
    texto += '• `/buscar notebook` - Busca por "notebook"\n'
    texto += '• `/novoitem` - Inicia cadastro guiado\n'
    texto += '• `/editaritem` - Busca item para editar\n\n'
    
    texto += f'📅 Sistema atualizado em: {datetime.now().strftime("%d/%m/%Y")}'
    
    await update.message.reply_text(texto, parse_mode='Markdown')

async def webapp_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            '• `/novoitem` - Cadastrar item',
            parse_mode='Markdown'
        )

# =============================================================================
# FUNCIONALIDADES ADMINISTRATIVAS
# =============================================================================

async def novo_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia cadastro de novo item"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        '➕ *Cadastrar Novo Item*\n\n'
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
        'Digite a *quantidade* inicial:',
        parse_mode='Markdown'
    )
    return QTD_ITEM

async def novo_item_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe a quantidade e salva o item"""
    try:
        quantidade = int(update.message.text)
        
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
            
            # Obter ID do item criado
            cursor = await db.execute('SELECT last_insert_rowid()')
            item_id = (await cursor.fetchone())[0]
        
        texto = (
            f'✅ *Item cadastrado com sucesso!*\n\n'
            f'🆔 ID: {item_id}\n'
            f'📝 Nome: {context.user_data["nome"]}\n'
            f'📄 Descrição: {context.user_data["descricao"]}\n'
            f'📦 Quantidade: {quantidade}\n'
            f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n\n'
            f'Use /menu para ver mais opções'
        )
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            '❌ Digite um número válido para a quantidade.\n\n'
            'Exemplo: 10'
        )
        return QTD_ITEM
    except Exception as e:
        logging.error(f"Erro ao salvar item: {e}")
        await update.message.reply_text('❌ Erro ao salvar item. Tente novamente.')
        return ConversationHandler.END

async def editar_item_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia edição de item"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return ConversationHandler.END
    
    await update.message.reply_text(
        '✏️ *Editar Item*\n\n'
        'Digite o *ID* ou *nome* do item que deseja editar:\n\n'
        '💡 _Use /listar para ver todos os itens_\n'
        '💡 _Use /cancelar para cancelar_',
        parse_mode='Markdown'
    )
    return EDITAR_ESCOLHA

async def editar_item_escolha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca o item para editar"""
    termo = update.message.text
    
    try:
        # Tentar buscar por ID primeiro
        try:
            item_id = int(termo)
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    'SELECT id, nome, descricao, quantidade FROM itens WHERE id = ?',
                    (item_id,)
                )
                item = await cursor.fetchone()
        except ValueError:
            # Buscar por nome
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    'SELECT id, nome, descricao, quantidade FROM itens WHERE nome LIKE ? LIMIT 1',
                    (f'%{termo}%',)
                )
                item = await cursor.fetchone()
        
        if not item:
            await update.message.reply_text(
                f'❌ Item não encontrado: *{termo}*\n\n'
                'Tente novamente com ID ou nome do item.',
                parse_mode='Markdown'
            )
            return EDITAR_ESCOLHA
        
        # Salvar item encontrado
        context.user_data['edit_item'] = {
            'id': item[0],
            'nome': item[1],
            'descricao': item[2],
            'quantidade': item[3]
        }
        
        # Mostrar opções de edição
        keyboard = [
            [InlineKeyboardButton("📝 Nome", callback_data='edit_nome')],
            [InlineKeyboardButton("📄 Descrição", callback_data='edit_descricao')],
            [InlineKeyboardButton("📦 Quantidade", callback_data='edit_quantidade')],
            [InlineKeyboardButton("❌ Cancelar", callback_data='edit_cancelar')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        texto = (
            f'✅ *Item encontrado:*\n\n'
            f'🆔 ID: {item[0]}\n'
            f'📝 Nome: {item[1]}\n'
            f'📄 Descrição: {item[2]}\n'
            f'📦 Quantidade: {item[3]}\n\n'
            f'O que deseja editar?'
        )
        
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
        return ConversationHandler.END  # Continua via callback
        
    except Exception as e:
        logging.error(f"Erro ao buscar item: {e}")
        await update.message.reply_text('❌ Erro ao buscar item.')
        return ConversationHandler.END

async def backup_banco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fazer backup do banco"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado.')
        return
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT * FROM itens ORDER BY id')
            items = await cursor.fetchall()
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'total_items': len(items),
            'items': []
        }
        
        for item in items:
            backup_data['items'].append({
                'id': item[0],
                'nome': item[1],
                'descricao': item[2],
                'quantidade': item[3],
                'status': item[4],
                'data_cadastro': item[5] if len(item) > 5 else None
            })
        
        # Criar arquivo de backup
        backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        # Mostrar resumo do backup
        texto = (
            f'💾 *Backup Realizado*\n\n'
            f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'
            f'📦 Total de itens: {len(items)}\n\n'
            f'*Primeiros itens:*\n'
        )
        
        for i, item in enumerate(items[:5], 1):
            texto += f'{i}. {item[1]} (Qtd: {item[3]})\n'
        
        if len(items) > 5:
            texto += f'... e mais {len(items) - 5} itens'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
        # Enviar arquivo JSON (limitado pelo tamanho)
        if len(backup_json) < 4000:
            await update.message.reply_text(f'```json\n{backup_json}\n```', parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro no backup: {e}")
        await update.message.reply_text('❌ Erro ao fazer backup.')

async def deletar_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletar item do estoque"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return
    
    if not context.args:
        await update.message.reply_text(
            '🗑️ *Deletar Item*\n\n'
            'Use: `/deletaritem <ID ou nome>`\n\n'
            'Exemplos:\n'
            '• `/deletaritem 5` - Deletar por ID\n'
            '• `/deletaritem notebook` - Deletar por nome\n\n'
            '💡 _Use /listar para ver todos os itens_',
            parse_mode='Markdown'
        )
        return
    
    termo = ' '.join(context.args)
    
    try:
        # Tentar buscar por ID primeiro
        try:
            item_id = int(termo)
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    'SELECT id, nome, descricao, quantidade FROM itens WHERE id = ?',
                    (item_id,)
                )
                item = await cursor.fetchone()
        except ValueError:
            # Buscar por nome
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    'SELECT id, nome, descricao, quantidade FROM itens WHERE nome LIKE ? LIMIT 1',
                    (f'%{termo}%',)
                )
                item = await cursor.fetchone()
        
        if not item:
            await update.message.reply_text(
                f'❌ Item não encontrado: *{termo}*\n\n'
                'Verifique o ID ou nome do item.',
                parse_mode='Markdown'
            )
            return
        
        # Confirmar exclusão
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar Exclusão", callback_data=f'delete_confirm_{item[0]}')],
            [InlineKeyboardButton("❌ Cancelar", callback_data='delete_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        texto = (
            f'⚠️ *Confirmar Exclusão*\n\n'
            f'🆔 ID: {item[0]}\n'
            f'📝 Nome: {item[1]}\n'
            f'📄 Descrição: {item[2]}\n'
            f'📦 Quantidade: {item[3]}\n\n'
            f'🚨 *Esta ação não pode ser desfeita!*'
        )
        
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro ao buscar item para deletar: {e}")
        await update.message.reply_text('❌ Erro ao buscar item.')

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerenciar administradores"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('❌ Acesso negado. Apenas administradores.')
        return
    
    try:
        # Ler lista de admins
        with open(ADMINS_FILE, 'r') as f:
            admins = [line.strip() for line in f if line.strip()]
        
        texto = '👥 *Gerenciar Administradores*\n\n'
        texto += f'📊 Total de admins: {len(admins)}\n\n'
        texto += '*Lista atual:*\n'
        
        for i, admin_id in enumerate(admins, 1):
            texto += f'{i}. ID: `{admin_id}`\n'
        
        texto += '\n*Comandos:*\n'
        texto += '• `/adminusers add <ID>` - Adicionar admin\n'
        texto += '• `/adminusers remove <ID>` - Remover admin\n'
        texto += '• `/adminusers list` - Listar admins\n\n'
        texto += f'💡 _Seu ID: {update.effective_user.id}_'
        
        await update.message.reply_text(texto, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Erro ao gerenciar admins: {e}")
        await update.message.reply_text('❌ Erro ao acessar lista de administradores.')

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar operação"""
    await update.message.reply_text('❌ Operação cancelada.')
    context.user_data.clear()
    return ConversationHandler.END

# =============================================================================
# CALLBACKS DOS BOTÕES
# =============================================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == 'buscar_menu':
        await query.edit_message_text(
            '🔍 *Buscar Itens*\n\n'
            'Use: `/buscar <termo>`\n\n'
            'Exemplos:\n'
            '• `/buscar notebook`\n'
            '• `/buscar mouse`',
            parse_mode='Markdown'
        )
    
    elif data == 'listar_todos':
        await listar_todos(query, context)
    
    elif data == 'relatorio_menu':
        await relatorio(query, context)
    
    elif data == 'novo_item_menu':
        if is_admin(user_id):
            await query.edit_message_text(
                '➕ *Cadastrar Novo Item*\n\n'
                'Use o comando: `/novoitem`\n\n'
                'O bot irá guiá-lo através do processo de cadastro.',
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text('❌ Acesso negado. Apenas administradores.')
    
    elif data == 'editar_item_menu':
        if is_admin(user_id):
            await query.edit_message_text(
                '✏️ *Editar Item*\n\n'
                'Use o comando: `/editaritem`\n\n'
                'Você poderá buscar o item por ID ou nome.',
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text('❌ Acesso negado.')
    
    elif data == 'backup_menu':
        if is_admin(user_id):
            await backup_banco(query, context)
        else:
            await query.edit_message_text('❌ Acesso negado.')
    
    elif data == 'admin_users_menu':
        if is_admin(user_id):
            await admin_users(query, context)
        else:
            await query.edit_message_text('❌ Acesso negado.')
    
    elif data == 'webapp_menu':
        if WEBAPP_URL.startswith('https://'):
            keyboard = [[InlineKeyboardButton(
                "📱 Abrir WebApp",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                '📱 *Interface WebApp*\n\nClique no botão abaixo:',
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                '⚠️ *WebApp não disponível*\n\n'
                'O WebApp requer HTTPS para funcionar no Telegram.',
                parse_mode='Markdown'
            )
    
    # Callbacks para exclusão de itens
    elif data.startswith('delete_confirm_'):
        if is_admin(user_id):
            item_id = int(data.split('_')[2])
            try:
                async with aiosqlite.connect(DB_PATH) as db:
                    cursor = await db.execute('SELECT nome FROM itens WHERE id = ?', (item_id,))
                    item_nome = (await cursor.fetchone())[0]
                    
                    await db.execute('DELETE FROM itens WHERE id = ?', (item_id,))
                    await db.commit()
                
                await query.edit_message_text(
                    f'✅ *Item Deletado*\n\n'
                    f'🗑️ "{item_nome}" foi removido do estoque.\n'
                    f'🆔 ID: {item_id}',
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Erro ao deletar item: {e}")
                await query.edit_message_text('❌ Erro ao deletar item.')
        else:
            await query.edit_message_text('❌ Acesso negado.')
    
    elif data == 'delete_cancel':
        await query.edit_message_text('❌ Exclusão cancelada.')

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
    
    print(f'🚀 Iniciando Bot Completo Railway...')
    print(f'🔑 Token: {TOKEN[:10]}...')
    print(f'🌐 WebApp: {WEBAPP_URL}')
    print(f'👑 Admins: {ADMINS_FILE}')
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation Handlers - COMANDOS CORRETOS
    novo_item_handler = ConversationHandler(
        entry_points=[CommandHandler('novoitem', novo_item_inicio)],
        states={
            NOME_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_nome)],
            DESC_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_descricao)],
            QTD_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, novo_item_quantidade)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )
    
    editar_item_handler = ConversationHandler(
        entry_points=[CommandHandler('editaritem', editar_item_inicio)],
        states={
            EDITAR_ESCOLHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_item_escolha)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )

    # Comandos básicos
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CommandHandler('buscar', buscar))
    app.add_handler(CommandHandler('listar', listar_todos))
    app.add_handler(CommandHandler('relatorio', relatorio))
    app.add_handler(CommandHandler('ajuda', ajuda))
    app.add_handler(CommandHandler('webapp', webapp_comando))
    
    # Comandos administrativos
    app.add_handler(CommandHandler('backup', backup_banco))
    app.add_handler(CommandHandler('deletaritem', deletar_item))
    app.add_handler(CommandHandler('adminusers', admin_users))
    
    # Conversation handlers
    app.add_handler(novo_item_handler)
    app.add_handler(editar_item_handler)
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print('✅ Bot Completo iniciado!')
    print('📋 Comandos registrados:')
    print('   • /start, /menu, /ajuda')
    print('   • /buscar, /listar, /relatorio')
    print('   • /novoitem, /editaritem, /deletaritem')
    print('   • /backup, /adminusers, /webapp')
    
    app.run_polling()

if __name__ == '__main__':
    main()
