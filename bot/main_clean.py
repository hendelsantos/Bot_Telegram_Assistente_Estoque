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
from pyzbar.pyzbar import decode
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
REPARO_FORNECEDOR, REPARO_DATA = range(300, 302)
RETORNO_CONFIRMA = 400
EXCLUIR_CONFIRMA = 500
# Estados para Inventário
INVENTARIO_QR, INVENTARIO_QTD, INVENTARIO_CONFIRMA = range(600, 603)

def is_admin(user_id):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'admins.txt')) as f:
            admins = [line.strip() for line in f if line.strip()]
        return str(user_id) in admins
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá! Eu sou o Assistente de Estoque. Use /menu para ver as opções disponíveis.')

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        '🤖 <b>Assistente de Estoque - Comandos Principais</b>\n\n'
        '/menu - Menu rápido com botões\n'
        '/webapp - 📱 Abrir WebApp com Scanner QR\n'
        '/novoitem - Cadastrar novo item (admin)\n'
        '/buscar <palavra-chave> - Buscar itens\n'
        '/buscar_qr (foto) - Buscar item por QR Code\n'
        '/atualizar <ID> - Atualizar item (admin)\n'
        '/inventario - Iniciar inventário com QR Code\n'
        '/enviar_reparo <ID> - Enviar item para reparo (admin)\n'
        '/retornar_reparo <ID> - Retornar item de reparo (admin)\n'
        '/excluir <ID> - Excluir item (admin)\n'
        '/relatorio <estoque|reparo|baixados> [csv|pdf] - Gerar relatório\n'
        '/historico <ID> - Ver histórico do item\n'
        '/verificar_alertas - Itens com estoque baixo/reparo longo\n'
        '/gerar_qr <ID> - Gerar QR Code do item\n'
        '/backup - Baixar backup do banco (admin)\n'
        '/restaurar (documento) - Restaurar banco (admin)\n'
        '/ajuda - Exibe esta mensagem\n\n'
        '🚀 <b>Novidade: WebApp com Scanner QR!</b>\n'
        'Use /webapp para scanner em tempo real - muito mais rápido!\n\n'
        'Use /menu para acessar as funções rapidamente!'
    )
    keyboard = [
        [InlineKeyboardButton('Menu', callback_data='menu_novoitem'), InlineKeyboardButton('Buscar', callback_data='menu_buscar')],
        [InlineKeyboardButton('Relatório', callback_data='menu_relatorio'), InlineKeyboardButton('Ajuda', callback_data='menu_ajuda')]
    ]
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('📱 WebApp - Scanner QR', callback_data='menu_webapp')],
        [InlineKeyboardButton('Cadastrar Novo Item', callback_data='menu_novoitem')],
        [InlineKeyboardButton('Buscar Itens', callback_data='menu_buscar')],
        [InlineKeyboardButton('Inventário QR', callback_data='menu_inventario')],
        [InlineKeyboardButton('Atualizar Item', callback_data='menu_atualizar')],
        [InlineKeyboardButton('Enviar para Reparo', callback_data='menu_enviar_reparo')],
        [InlineKeyboardButton('Retornar de Reparo', callback_data='menu_retornar_reparo')],
        [InlineKeyboardButton('Excluir Item', callback_data='menu_excluir')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Menu de Ações:', reply_markup=reply_markup)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'menu_webapp':
        await webapp_inventario(query, context)
    elif query.data == 'menu_novoitem':
        await query.message.reply_text('Use /novoitem para cadastrar um novo item.')
    elif query.data == 'menu_buscar':
        await query.message.reply_text('Use /buscar <palavra-chave> para buscar itens.')
    elif query.data == 'menu_inventario':
        await query.message.reply_text('Use /inventario para iniciar um inventário com QR Code.')
    elif query.data == 'menu_atualizar':
        await query.message.reply_text('Use /atualizar <ID> para atualizar um item.')
    elif query.data == 'menu_enviar_reparo':
        await query.message.reply_text('Use /enviar_reparo <ID> para enviar item para reparo.')
    elif query.data == 'menu_retornar_reparo':
        await query.message.reply_text('Use /retornar_reparo <ID> para registrar retorno de item.')
    elif query.data == 'menu_excluir':
        await query.message.reply_text('Use /excluir <ID> para excluir um item.')
    else:
        await query.message.reply_text('Ação não reconhecida.')

# ==================== WEBAPP FUNCTIONS ====================

async def webapp_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abrir WebApp para inventário com scanner QR em tempo real"""
    
    # Verificar se a URL é HTTPS (requerido pelo Telegram)
    if WEBAPP_URL.startswith('https://'):
        keyboard = [
            [InlineKeyboardButton(
                '📱 Abrir Scanner QR - Inventário',
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        texto = (
            '🚀 <b>WebApp - Inventário com Scanner QR</b>\n\n'
            '📲 Clique no botão abaixo para abrir o scanner QR em tempo real!\n\n'
            '✨ <b>Funcionalidades:</b>\n'
            '• Scanner QR em tempo real com câmera\n'
            '• Busca automática de itens\n'
            '• Controle de quantidades\n'
            '• Relatório final do inventário\n\n'
            '🔥 <b>Muito mais rápido que tirar fotos!</b>'
        )
        
        await update.message.reply_text(
            texto, 
            reply_markup=reply_markup, 
            parse_mode='HTML'
        )
    else:
        # URL HTTP - mostrar instruções para HTTPS
        texto = (
            '🚀 <b>WebApp - Inventário com Scanner QR</b>\n\n'
            '⚠️ <b>Configuração necessária:</b>\n'
            'O Telegram WebApp requer HTTPS. Configure uma URL HTTPS para usar esta funcionalidade.\n\n'
            '🔧 <b>Opções:</b>\n'
            '• Use ngrok: <code>ngrok http 8080</code>\n'
            '• Configure certificado SSL\n'
            '• Use serviço de tunnel como localtunnel\n\n'
            f'📍 <b>URL atual:</b> <code>{WEBAPP_URL}</code>\n'
            '📍 <b>WebApp local:</b> <code>http://localhost:8080</code>\n\n'
            '💡 <b>Enquanto isso:</b>\n'
            'Use /inventario para o método tradicional com fotos.'
        )
        
        await update.message.reply_text(texto, parse_mode='HTML')

async def webapp_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para receber dados do WebApp"""
    if update.message.web_app_data:
        try:
            # Receber dados do WebApp
            data = json.loads(update.message.web_app_data.data)
            
            if data.get('type') == 'inventory_finished':
                await processar_inventario_webapp(update, context, data)
            elif data.get('type') == 'item_lookup':
                await responder_item_lookup(update, context, data)
            else:
                await update.message.reply_text('Tipo de dados não reconhecido.')
                
        except json.JSONDecodeError:
            await update.message.reply_text('Erro ao processar dados do WebApp.')
        except Exception as e:
            logging.error(f'Erro no WebApp handler: {str(e)}')
            await update.message.reply_text('Erro interno ao processar dados.')

async def processar_inventario_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Processar inventário finalizado no WebApp"""
    try:
        items = data.get('items', [])
        summary = data.get('summary', {})
        user_info = data.get('user', {})
        
        if not items:
            await update.message.reply_text('Nenhum item foi inventariado.')
            return
        
        # Salvar inventário no banco
        timestamp = datetime.now().isoformat()
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or 'Usuário'
        
        # Criar relatório
        texto_relatorio = f'📋 <b>Relatório de Inventário</b>\n\n'
        texto_relatorio += f'👤 Usuário: {user_name}\n'
        texto_relatorio += f'📅 Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'
        texto_relatorio += f'📦 Total de itens: {len(items)}\n\n'
        
        # Processar cada item
        for item in items:
            item_id = item.get('id')
            quantidade_inventario = item.get('quantity', 0)
            
            # Buscar dados atuais do item
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT nome, quantidade FROM itens WHERE id = ?", 
                    (item_id,)
                )
                item_atual = await cursor.fetchone()
            
            if item_atual:
                nome_item, quantidade_atual = item_atual
                diferenca = quantidade_inventario - quantidade_atual
                
                texto_relatorio += f'• <b>{nome_item}</b> (ID: {item_id})\n'
                texto_relatorio += f'  Estoque atual: {quantidade_atual}\n'
                texto_relatorio += f'  Inventariado: {quantidade_inventario}\n'
                
                if diferenca > 0:
                    texto_relatorio += f'  📈 Diferença: +{diferenca}\n'
                elif diferenca < 0:
                    texto_relatorio += f'  📉 Diferença: {diferenca}\n'
                else:
                    texto_relatorio += f'  ✅ Sem diferença\n'
                texto_relatorio += '\n'
                
                # Atualizar quantidade no banco
                await db.execute(
                    "UPDATE itens SET quantidade = ? WHERE id = ?",
                    (quantidade_inventario, item_id)
                )
                
                # Registrar movimentação
                await db.execute(
                    "INSERT INTO movimentacoes (item_id, acao, detalhes, usuario, data_hora) VALUES (?, ?, ?, ?, ?)",
                    (item_id, 'Inventário WebApp', f'Ajuste: {quantidade_atual} → {quantidade_inventario}', user_name, timestamp)
                )
                
                await db.commit()
        
        # Resumo
        if summary:
            texto_relatorio += f'📊 <b>Resumo:</b>\n'
            texto_relatorio += f'• Itens adicionados: {summary.get("items_added", 0)}\n'
            texto_relatorio += f'• Diferenças encontradas: {summary.get("differences_found", 0)}\n'
        
        await update.message.reply_text(texto_relatorio, parse_mode='HTML')
        
        # Salvar relatório em arquivo
        relatorio_path = os.path.join(os.path.dirname(__file__), '../inventarios')
        os.makedirs(relatorio_path, exist_ok=True)
        
        filename = f'inventario_webapp_{timestamp.replace(":", "-").replace(".", "-")}.json'
        filepath = os.path.join(relatorio_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'user_id': user_id,
                'user_name': user_name,
                'items': items,
                'summary': summary,
                'total_items': len(items)
            }, f, ensure_ascii=False, indent=2)
        
        await update.message.reply_text(
            f'✅ Inventário salvo com sucesso!\nArquivo: {filename}'
        )
        
    except Exception as e:
        logging.error(f'Erro ao processar inventário WebApp: {str(e)}')
        await update.message.reply_text('Erro ao processar inventário. Tente novamente.')

async def responder_item_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    """Responder lookup de item do WebApp"""
    try:
        item_id = data.get('item_id')
        
        if not item_id:
            await update.message.reply_text('ID do item não fornecido.')
            return
        
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, nome, descricao, quantidade, categoria, status FROM itens WHERE id = ?",
                (item_id,)
            )
            item = await cursor.fetchone()
        
        if item:
            item_data = {
                'id': item[0],
                'nome': item[1],
                'descricao': item[2],
                'quantidade': item[3],
                'categoria': item[4],
                'status': item[5]
            }
            
            # Enviar dados de volta para o WebApp (se necessário)
            texto = f'✅ Item encontrado: {item_data["nome"]}'
            await update.message.reply_text(texto)
        else:
            await update.message.reply_text('❌ Item não encontrado.')
            
    except Exception as e:
        logging.error(f'Erro no lookup de item: {str(e)}')
        await update.message.reply_text('Erro ao buscar item.')

# ==================== END WEBAPP FUNCTIONS ====================

# Cadastro de novos itens
async def novoitem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem cadastrar novos itens.')
        return ConversationHandler.END
    await update.message.reply_text('Por favor, envie uma foto do item.')
    return FOTO

async def receber_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    foto_id = f"{update.message.from_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    foto_path = os.path.join(FOTOS_DIR, foto_id)
    await file.download_to_drive(foto_path)
    context.user_data['foto_path'] = foto_path
    await update.message.reply_text('Agora, informe o nome do item.')
    return NOME

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nome'] = update.message.text
    await update.message.reply_text('Descrição/Observações do item?')
    return DESCRICAO

async def receber_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['descricao'] = update.message.text
    await update.message.reply_text('Quantidade inicial?')
    return QUANTIDADE

async def receber_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantidade = int(update.message.text)
        context.user_data['quantidade'] = quantidade
    except ValueError:
        await update.message.reply_text('Por favor, envie um número inteiro para a quantidade.')
        return QUANTIDADE
    resumo = (f"Resumo:\n"
              f"Nome: {context.user_data['nome']}\n"
              f"Descrição: {context.user_data['descricao']}\n"
              f"Quantidade: {context.user_data['quantidade']}\n"
              f"Foto salva.")
    await update.message.reply_text(resumo + '\n\nConfirma o cadastro? (sim/não)')
    return CONFIRMACAO

async def confirmar_cadastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != 'sim':
        await update.message.reply_text('Cadastro cancelado.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'INSERT INTO itens (nome, descricao, quantidade, status, foto_path) VALUES (?, ?, ?, ?, ?)',
            (context.user_data['nome'], context.user_data['descricao'], context.user_data['quantidade'], 'Em Estoque', context.user_data['foto_path'])
        )
        await db.commit()
        item_id = cursor.lastrowid
        await db.execute(
            'INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)',
            (item_id, str(update.effective_user.id), 'Cadastro', f"Nome: {context.user_data['nome']}")
        )
        await db.commit()
    await update.message.reply_text('Item cadastrado com sucesso!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Busca de itens
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Use: /buscar <palavra-chave>')
        return
    termo = ' '.join(context.args)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, nome FROM itens WHERE nome LIKE ? OR descricao LIKE ?", (f"%{termo}%", f"%{termo}%"))
        resultados = await cursor.fetchall()
    if not resultados:
        await update.message.reply_text('Nenhum item encontrado.')
        return
    botoes = [
        [InlineKeyboardButton(f"{row[1]} (ID: {row[0]})", callback_data=f"detalhe_{row[0]}")]
        for row in resultados
    ]
    reply_markup = InlineKeyboardMarkup(botoes)
    await update.message.reply_text('Itens encontrados:', reply_markup=reply_markup)

async def mostrar_detalhe_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith('detalhe_'):
        return
    item_id = int(query.data.split('_')[1])
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, nome, descricao, quantidade, status, foto_path FROM itens WHERE id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await query.edit_message_text('Item não encontrado.')
        return
    texto = (f"ID: {item[0]}\nNome: {item[1]}\nDescrição: {item[2]}\nQuantidade: {item[3]}\nStatus: {item[4]}")
    if item[5] and os.path.exists(item[5]):
        with open(item[5], 'rb') as f:
            await query.message.reply_photo(f, caption=texto)
        await query.edit_message_text('')
    else:
        await query.edit_message_text(texto)

# Atualização de itens
async def atualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem atualizar itens.')
        return ConversationHandler.END
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /atualizar <ID>')
        return ConversationHandler.END
    item_id = int(context.args[0])
    context.user_data['atualizar_id'] = item_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT nome, descricao, quantidade FROM itens WHERE id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await update.message.reply_text('Item não encontrado.')
        return ConversationHandler.END
    texto = (f"ID: {item_id}\nNome: {item[0]}\nDescrição: {item[1]}\nQuantidade: {item[2]}")
    keyboard = [
        [InlineKeyboardButton('Alterar Nome', callback_data='atual_nome')],
        [InlineKeyboardButton('Alterar Descrição', callback_data='atual_desc')],
        [InlineKeyboardButton('Ajustar Quantidade', callback_data='atual_qtd')],
        [InlineKeyboardButton('Adicionar Foto', callback_data='atual_foto')],
    ]
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard))
    return ATUAL_ESCOLHA

async def atualizar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'atual_nome':
        await query.message.reply_text('Envie o novo nome do item:')
        return ATUAL_NOME
    elif query.data == 'atual_desc':
        await query.message.reply_text('Envie a nova descrição:')
        return ATUAL_DESC
    elif query.data == 'atual_qtd':
        await query.message.reply_text('Envie a nova quantidade (número inteiro):')
        return ATUAL_QTD
    elif query.data == 'atual_foto':
        await query.message.reply_text('Envie a nova foto do item:')
        return ATUAL_FOTO
    else:
        await query.message.reply_text('Ação não reconhecida.')
        return ConversationHandler.END

async def atualizar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    novo_nome = update.message.text
    item_id = context.user_data['atualizar_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET nome = ? WHERE id = ?", (novo_nome, item_id))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Atualização', f'Alterou nome para: {novo_nome}'))
        await db.commit()
    await update.message.reply_text('Nome atualizado com sucesso!')
    return ConversationHandler.END

async def atualizar_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nova_desc = update.message.text
    item_id = context.user_data['atualizar_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET descricao = ? WHERE id = ?", (nova_desc, item_id))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Atualização', f'Alterou descrição para: {nova_desc}'))
        await db.commit()
    await update.message.reply_text('Descrição atualizada com sucesso!')
    return ConversationHandler.END

async def atualizar_qtd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        nova_qtd = int(update.message.text)
    except ValueError:
        await update.message.reply_text('Por favor, envie um número inteiro.')
        return ATUAL_QTD
    item_id = context.user_data['atualizar_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET quantidade = ? WHERE id = ?", (nova_qtd, item_id))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Atualização', f'Ajustou quantidade para: {nova_qtd}'))
        await db.commit()
    await update.message.reply_text('Quantidade atualizada com sucesso!')
    return ConversationHandler.END

async def atualizar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    foto_id = f"atual_{context.user_data['atualizar_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    foto_path = os.path.join(FOTOS_DIR, foto_id)
    await file.download_to_drive(foto_path)
    item_id = context.user_data['atualizar_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET foto_path = ? WHERE id = ?", (foto_path, item_id))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Atualização', 'Atualizou foto'))
        await db.commit()
    await update.message.reply_text('Foto atualizada com sucesso!')
    return ConversationHandler.END

# Envio para reparo
async def enviar_reparo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem enviar itens para reparo.')
        return ConversationHandler.END
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /enviar_reparo <ID>')
        return ConversationHandler.END
    item_id = int(context.args[0])
    context.user_data['reparo_id'] = item_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT nome, quantidade, status FROM itens WHERE id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await update.message.reply_text('Item não encontrado.')
        return ConversationHandler.END
    if item[2] == 'Em Reparo Externo':
        await update.message.reply_text('Este item já está em reparo externo.')
        return ConversationHandler.END
    if item[1] <= 0:
        await update.message.reply_text('Quantidade insuficiente em estoque para enviar para reparo.')
        return ConversationHandler.END
    await update.message.reply_text('Para qual fornecedor/local o item será enviado?')
    return REPARO_FORNECEDOR

async def receber_fornecedor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reparo_fornecedor'] = update.message.text
    await update.message.reply_text('Qual a data de envio? (formato: DD/MM/AAAA)')
    return REPARO_DATA

async def receber_data_envio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data_envio = update.message.text
    item_id = context.user_data['reparo_id']
    fornecedor = context.user_data['reparo_fornecedor']
    info_reparo = f"Fornecedor/Local: {fornecedor} | Data de envio: {data_envio}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET status = 'Em Reparo Externo', info_reparo = ?, quantidade = quantidade - 1 WHERE id = ?", (info_reparo, item_id))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Envio para Reparo', info_reparo))
        await db.commit()
    await update.message.reply_text('Item enviado para reparo externo com sucesso!')
    return ConversationHandler.END

# Retorno de reparo
async def retornar_reparo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem registrar retorno de reparo.')
        return ConversationHandler.END
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /retornar_reparo <ID>')
        return ConversationHandler.END
    item_id = int(context.args[0])
    context.user_data['retorno_id'] = item_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT nome, status FROM itens WHERE id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await update.message.reply_text('Item não encontrado.')
        return ConversationHandler.END
    if item[1] != 'Em Reparo Externo':
        await update.message.reply_text('Este item não está marcado como "Em Reparo Externo".')
        return ConversationHandler.END
    await update.message.reply_text(f'Confirmar retorno do item "{item[0]}" para o estoque? (sim/não)')
    return RETORNO_CONFIRMA

async def confirmar_retorno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != 'sim':
        await update.message.reply_text('Operação cancelada.')
        return ConversationHandler.END
    item_id = context.user_data['retorno_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE itens SET status = 'Em Estoque', info_reparo = NULL, quantidade = quantidade + 1 WHERE id = ?", (item_id,))
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Retorno de Reparo', 'Item retornou ao estoque'))
        await db.commit()
    await update.message.reply_text('Item retornou ao estoque com sucesso!')
    return ConversationHandler.END

# Exclusão de itens
async def excluir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem excluir itens.')
        return ConversationHandler.END
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /excluir <ID>')
        return ConversationHandler.END
    item_id = int(context.args[0])
    context.user_data['excluir_id'] = item_id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT nome FROM itens WHERE id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await update.message.reply_text('Item não encontrado.')
        return ConversationHandler.END
    await update.message.reply_text(f'Tem certeza que deseja excluir o item "{item[0]}" (ID: {item_id})? (sim/não)')
    return EXCLUIR_CONFIRMA

async def confirmar_exclusao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != 'sim':
        await update.message.reply_text('Operação cancelada.')
        return ConversationHandler.END
    item_id = context.user_data['excluir_id']
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO movimentacoes (item_id, usuario, acao, detalhes) VALUES (?, ?, ?, ?)",
            (item_id, str(update.effective_user.id), 'Exclusão', 'Item excluído'))
        await db.execute("DELETE FROM itens WHERE id = ?", (item_id,))
        await db.commit()
    await update.message.reply_text('Item excluído com sucesso!')
    return ConversationHandler.END

# Relatórios
async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0] not in ['estoque', 'reparo', 'baixados']:
        await update.message.reply_text('Use: /relatorio <estoque|reparo|baixados> [csv|pdf]')
        return
    tipo = context.args[0]
    formato = context.args[1] if len(context.args) > 1 else 'csv'
    status_map = {
        'estoque': 'Em Estoque',
        'reparo': 'Em Reparo Externo',
        'baixados': 'Baixado'
    }
    status = status_map[tipo]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, nome, descricao, quantidade, status, data_cadastro FROM itens WHERE status = ?", (status,))
        rows = await cursor.fetchall()
    if not rows:
        await update.message.reply_text('Nenhum item encontrado para esse relatório.')
        return
    df = pd.DataFrame(rows, columns=['ID', 'Nome', 'Descrição', 'Quantidade', 'Status', 'Data Cadastro'])
    file_path = f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{formato}"
    if formato == 'csv':
        df.to_csv(file_path, index=False)
        with open(file_path, 'rb') as f:
            await update.message.reply_document(f, filename=file_path)
    elif formato == 'pdf':
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        c.setFont('Helvetica', 10)
        y = height - 40
        for col in df.columns:
            c.drawString(40 + 100 * list(df.columns).index(col), y, str(col))
        y -= 20
        for _, row in df.iterrows():
            for i, val in enumerate(row):
                c.drawString(40 + 100 * i, y, str(val))
            y -= 20
            if y < 40:
                c.showPage()
                y = height - 40
        c.save()
        with open(file_path, 'rb') as f:
            await update.message.reply_document(f, filename=file_path)
    else:
        await update.message.reply_text('Formato não suportado. Use csv ou pdf.')
        return
    os.remove(file_path)

# Histórico de movimentações
async def historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /historico <ID>')
        return
    item_id = int(context.args[0])
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT acao, detalhes, usuario, data_hora FROM movimentacoes WHERE item_id = ? ORDER BY data_hora DESC", (item_id,))
        rows = await cursor.fetchall()
    if not rows:
        await update.message.reply_text('Nenhuma movimentação encontrada para este item.')
        return
    texto = f"Histórico do item {item_id}:\n\n"
    for acao, detalhes, usuario, data_hora in rows:
        texto += f"[{data_hora}] {acao} por {usuario}: {detalhes}\n"
    await update.message.reply_text(texto)

# Verificação de alertas
async def verificar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LIMITE_ESTOQUE_BAIXO = 2
    dias_reparo = 7
    hoje = datetime.now()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, nome, quantidade FROM itens WHERE quantidade <= ? AND status = 'Em Estoque'", (LIMITE_ESTOQUE_BAIXO,))
        baixos = await cursor.fetchall()
        cursor = await db.execute("SELECT id, nome, info_reparo, data_cadastro FROM itens WHERE status = 'Em Reparo Externo'")
        reparos = await cursor.fetchall()
    msg = ''
    if baixos:
        msg += 'Itens com estoque baixo:\n'
        for i in baixos:
            msg += f"ID: {i[0]} | {i[1]} | Qtd: {i[2]}\n"
        msg += '\n'
    if reparos:
        msg += 'Itens em reparo há mais de 7 dias:\n'
        for i in reparos:
            try:
                data_envio = datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
            if (hoje - data_envio).days >= dias_reparo:
                msg += f"ID: {i[0]} | {i[1]} | {i[2]} | Enviado em: {i[3][:19]}\n"
    if not msg:
        msg = 'Nenhum alerta encontrado.'
    await update.message.reply_text(msg)

# QR Code
async def buscar_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('Envie uma foto do QR Code do item.')
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    qr_path = 'temp_qr.jpg'
    await file.download_to_drive(qr_path)
    try:
        img = Image.open(qr_path)
        decoded = decode(img)
        if not decoded:
            await update.message.reply_text('QR Code não reconhecido.')
            return
        conteudo = decoded[0].data.decode('utf-8')
        if conteudo.isdigit():
            item_id = int(conteudo)
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute("SELECT id, nome, descricao, quantidade, status FROM itens WHERE id = ?", (item_id,))
                item = await cursor.fetchone()
            if not item:
                await update.message.reply_text('Item não encontrado.')
                return
            texto = (f"ID: {item[0]}\nNome: {item[1]}\nDescrição: {item[2]}\nQuantidade: {item[3]}\nStatus: {item[4]}")
            await update.message.reply_text(texto)
        else:
            await update.message.reply_text(f'Conteúdo do QR: {conteudo}')
    finally:
        if os.path.exists(qr_path):
            os.remove(qr_path)

async def gerar_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import qrcode
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text('Use: /gerar_qr <ID>')
        return
    item_id = int(context.args[0])
    qr_img = qrcode.make(str(item_id))
    qr_path = f'qr_{item_id}.png'
    qr_img.save(qr_path)
    with open(qr_path, 'rb') as f:
        await update.message.reply_photo(f, caption=f'QR Code para o item {item_id}')
    os.remove(qr_path)

# Módulo de Inventário
async def inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Inicializar lista de inventário no contexto
    context.user_data['inventario_lista'] = []
    
    await update.message.reply_text(
        '📋 <b>Inventário Iniciado!</b>\n\n'
        'Envie a foto do QR Code do item que deseja inventariar.\n'
        'Para finalizar o inventário, digite /finalizar_inventario',
        parse_mode='HTML'
    )
    return INVENTARIO_QR

async def inventario_receber_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # Processar QR Code da foto
        file = await update.message.photo[-1].get_file()
        qr_path = f'temp_qr_{update.effective_user.id}.jpg'
        await file.download_to_drive(qr_path)
        
        try:
            # Ler QR Code
            img = Image.open(qr_path)
            decoded_objects = decode(img)
            
            if decoded_objects:
                qr_content = decoded_objects[0].data.decode('utf-8')
                
                # Verificar se é um ID válido
                if qr_content.isdigit():
                    item_id = int(qr_content)
                    
                    # Buscar item no banco
                    async with aiosqlite.connect(DB_PATH) as db:
                        cursor = await db.execute('SELECT * FROM itens WHERE id = ?', (item_id,))
                        item = await cursor.fetchone()
                    
                    if item:
                        # Armazenar item atual no contexto
                        context.user_data['item_atual'] = {
                            'id': item[0],
                            'nome': item[1],
                            'codigo': item[2],
                            'categoria': item[3],
                            'localizacao': item[4],
                            'quantidade_sistema': item[5]
                        }
                        
                        await update.message.reply_text(
                            f'📦 <b>Item Encontrado:</b>\n'
                            f'ID: {item[0]}\n'
                            f'Nome: {item[1]}\n'
                            f'Código: {item[2] or "N/A"}\n'
                            f'Categoria: {item[3] or "N/A"}\n'
                            f'Localização: {item[4] or "N/A"}\n'
                            f'Quantidade no Sistema: {item[5]}\n\n'
                            f'Digite a quantidade encontrada no inventário:',
                            parse_mode='HTML'
                        )
                        return INVENTARIO_QTD
                    else:
                        await update.message.reply_text(
                            'Item não encontrado no banco de dados.\n'
                            'Envie outro QR Code ou digite /finalizar_inventario'
                        )
                        return INVENTARIO_QR
                else:
                    await update.message.reply_text(
                        'QR Code não contém um ID válido.\n'
                        'Envie outro QR Code ou digite /finalizar_inventario'
                    )
                    return INVENTARIO_QR
            else:
                await update.message.reply_text(
                    'Não foi possível ler o QR Code.\n'
                    'Envie outro QR Code ou digite /finalizar_inventario'
                )
                return INVENTARIO_QR
                
        except Exception as e:
            await update.message.reply_text(
                f'Erro ao processar QR Code: {str(e)}\n'
                'Envie outro QR Code ou digite /finalizar_inventario'
            )
            return INVENTARIO_QR
        finally:
            if os.path.exists(qr_path):
                os.remove(qr_path)
    else:
        await update.message.reply_text(
            'Por favor, envie uma foto do QR Code ou digite /finalizar_inventario'
        )
        return INVENTARIO_QR

async def inventario_receber_quantidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantidade = int(update.message.text)
        item = context.user_data['item_atual']
        
        # Adicionar à lista de inventário
        inventario_item = {
            'id': item['id'],
            'nome': item['nome'],
            'codigo': item['codigo'],
            'categoria': item['categoria'],
            'localizacao': item['localizacao'],
            'quantidade_sistema': item['quantidade_sistema'],
            'quantidade_inventario': quantidade,
            'diferenca': quantidade - item['quantidade_sistema'],
            'data_inventario': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        context.user_data['inventario_lista'].append(inventario_item)
        
        # Mostrar diferença
        diferenca = quantidade - item['quantidade_sistema']
        emoji = '✅' if diferenca == 0 else '⚠️' if diferenca > 0 else '❌'
        
        await update.message.reply_text(
            f'{emoji} <b>Item Adicionado ao Inventário:</b>\n'
            f'Nome: {item["nome"]}\n'
            f'Sistema: {item["quantidade_sistema"]}\n'
            f'Inventário: {quantidade}\n'
            f'Diferença: {diferenca:+d}\n\n'
            f'Total de itens inventariados: {len(context.user_data["inventario_lista"])}\n\n'
            f'Envie o próximo QR Code ou digite /finalizar_inventario',
            parse_mode='HTML'
        )
        
        return INVENTARIO_QR
        
    except ValueError:
        await update.message.reply_text(
            'Por favor, digite apenas números para a quantidade.'
        )
        return INVENTARIO_QTD

async def finalizar_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'inventario_lista' not in context.user_data or not context.user_data['inventario_lista']:
        await update.message.reply_text('Nenhum item foi inventariado.')
        return ConversationHandler.END
    
    lista = context.user_data['inventario_lista']
    
    # Perguntar formato do relatório
    keyboard = [
        [InlineKeyboardButton('📄 TXT', callback_data='relatorio_txt')],
        [InlineKeyboardButton('📊 CSV', callback_data='relatorio_csv')],
        [InlineKeyboardButton('📗 Excel', callback_data='relatorio_excel')]
    ]
    
    await update.message.reply_text(
        f'📋 <b>Inventário Concluído!</b>\n\n'
        f'Total de itens inventariados: {len(lista)}\n'
        f'Escolha o formato do relatório:',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    return INVENTARIO_CONFIRMA

async def gerar_relatorio_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if 'inventario_lista' not in context.user_data:
        await query.edit_message_text('Erro: dados do inventário não encontrados.')
        return ConversationHandler.END
    
    lista = context.user_data['inventario_lista']
    formato = query.data.split('_')[1]  # txt, csv, ou excel
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if formato == 'txt':
            # Gerar relatório TXT
            filename = f'inventario_{timestamp}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'RELATÓRIO DE INVENTÁRIO\n')
                f.write(f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
                f.write(f'Total de itens: {len(lista)}\n')
                f.write('=' * 80 + '\n\n')
                
                for item in lista:
                    f.write(f'ID: {item["id"]}\n')
                    f.write(f'Nome: {item["nome"]}\n')
                    f.write(f'Código: {item["codigo"] or "N/A"}\n')
                    f.write(f'Categoria: {item["categoria"] or "N/A"}\n')
                    f.write(f'Localização: {item["localizacao"] or "N/A"}\n')
                    f.write(f'Qtd Sistema: {item["quantidade_sistema"]}\n')
                    f.write(f'Qtd Inventário: {item["quantidade_inventario"]}\n')
                    f.write(f'Diferença: {item["diferenca"]:+d}\n')
                    f.write(f'Data Inventário: {item["data_inventario"]}\n')
                    f.write('-' * 50 + '\n')
            
            with open(filename, 'rb') as f:
                await query.message.reply_document(f, filename=filename)
            
        elif formato == 'csv':
            # Gerar relatório CSV
            filename = f'inventario_{timestamp}.csv'
            df = pd.DataFrame(lista)
            df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
            
            with open(filename, 'rb') as f:
                await query.message.reply_document(f, filename=filename)
                
        elif formato == 'excel':
            # Gerar relatório Excel
            filename = f'inventario_{timestamp}.xlsx'
            df = pd.DataFrame(lista)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Inventário', index=False)
                
                # Formatar planilha
                workbook = writer.book
                worksheet = writer.sheets['Inventário']
                
                # Ajustar largura das colunas
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            with open(filename, 'rb') as f:
                await query.message.reply_document(f, filename=filename)
        
        # Limpar dados do inventário
        context.user_data.pop('inventario_lista', None)
        context.user_data.pop('item_atual', None)
        
        await query.edit_message_text(
            f'✅ Relatório de inventário gerado com sucesso!\n'
            f'Formato: {formato.upper()}\n'
            f'Total de itens: {len(lista)}'
        )
        
        # Remover arquivo temporário
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        await query.edit_message_text(f'Erro ao gerar relatório: {str(e)}')
    
    return ConversationHandler.END

async def cancelar_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Limpar dados do inventário
    context.user_data.pop('inventario_lista', None)
    context.user_data.pop('item_atual', None)
    
    await update.message.reply_text(
        '❌ Inventário cancelado.\n'
        'Todos os dados foram limpos.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Backup e restauração
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem fazer backup.')
        return
    db_path = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
    if not os.path.exists(db_path):
        await update.message.reply_text('Banco de dados não encontrado.')
        return
    with open(db_path, 'rb') as f:
        await update.message.reply_document(f, filename='estoque_backup.db')

async def restaurar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem restaurar o banco.')
        return
    if not update.message.document:
        await update.message.reply_text('Envie o arquivo de backup como documento junto com o comando /restaurar.')
        return
    file = await update.message.document.get_file()
    db_path = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
    await file.download_to_drive(db_path)
    await update.message.reply_text('Banco de dados restaurado com sucesso!')

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Operação cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    logging.basicConfig(level=logging.INFO)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print('Defina a variável de ambiente TELEGRAM_BOT_TOKEN')
        return
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handlers
    cadastro_conv = ConversationHandler(
        entry_points=[CommandHandler('novoitem', novoitem)],
        states={
            FOTO: [MessageHandler(filters.PHOTO, receber_foto)],
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao)],
            QUANTIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_quantidade)],
            CONFIRMACAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_cadastro)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    atualizar_conv = ConversationHandler(
        entry_points=[CommandHandler('atualizar', atualizar)],
        states={
            ATUAL_ESCOLHA: [CallbackQueryHandler(atualizar_callback, pattern=r'^atual_')],
            ATUAL_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, atualizar_nome)],
            ATUAL_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, atualizar_desc)],
            ATUAL_QTD: [MessageHandler(filters.TEXT & ~filters.COMMAND, atualizar_qtd)],
            ATUAL_FOTO: [MessageHandler(filters.PHOTO, atualizar_foto)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    enviar_reparo_conv = ConversationHandler(
        entry_points=[CommandHandler('enviar_reparo', enviar_reparo)],
        states={
            REPARO_FORNECEDOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_fornecedor)],
            REPARO_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_data_envio)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    retorno_reparo_conv = ConversationHandler(
        entry_points=[CommandHandler('retornar_reparo', retornar_reparo)],
        states={
            RETORNO_CONFIRMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_retorno)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    excluir_conv = ConversationHandler(
        entry_points=[CommandHandler('excluir', excluir)],
        states={
            EXCLUIR_CONFIRMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_exclusao)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )

    inventario_conv = ConversationHandler(
        entry_points=[CommandHandler('inventario', inventario)],
        states={
            INVENTARIO_QR: [
                MessageHandler(filters.PHOTO, inventario_receber_qr),
                CommandHandler('finalizar_inventario', finalizar_inventario)
            ],
            INVENTARIO_QTD: [MessageHandler(filters.TEXT & ~filters.COMMAND, inventario_receber_quantidade)],
            INVENTARIO_CONFIRMA: [CallbackQueryHandler(gerar_relatorio_inventario, pattern=r'^relatorio_')]
        },
        fallbacks=[CommandHandler('cancelar', cancelar_inventario)],
    )

    # Adicionar handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('ajuda', ajuda))
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CommandHandler('webapp', webapp_inventario))
    app.add_handler(CommandHandler('buscar', buscar))
    app.add_handler(CommandHandler('relatorio', relatorio))
    app.add_handler(CommandHandler('historico', historico))
    app.add_handler(CommandHandler('verificar_alertas', verificar_alertas))
    app.add_handler(CommandHandler('gerar_qr', gerar_qr))
    app.add_handler(CommandHandler('backup', backup))
    app.add_handler(cadastro_conv)
    app.add_handler(atualizar_conv)
    app.add_handler(enviar_reparo_conv)
    app.add_handler(retorno_reparo_conv)
    app.add_handler(excluir_conv)
    app.add_handler(inventario_conv)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))
    app.add_handler(CallbackQueryHandler(mostrar_detalhe_item, pattern=r'^detalhe_'))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex('^/buscar_qr'), buscar_qr))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.CaptionRegex('^/restaurar'), restaurar))
    # Handler para dados do WebApp
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_message_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
