import os
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import aiosqlite
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
def is_admin(user_id):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'admins.txt')) as f:
            admins = [line.strip() for line in f if line.strip()]
        return str(user_id) in admins
    except Exception:
        return False
from pyzbar.pyzbar import decode
from PIL import Image
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
        # Espera-se que o QR contenha o ID do item
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
from datetime import datetime, timedelta
async def verificar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    LIMITE_ESTOQUE_BAIXO = 2  # pode ser ajustado
    dias_reparo = 7
    hoje = datetime.now()
    # Itens com estoque baixo
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
            # data_cadastro pode ser data de envio para reparo
            try:
                data_envio = datetime.strptime(i[3][:19], '%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
            if (hoje - data_envio).days >= dias_reparo:
                msg += f"ID: {i[0]} | {i[1]} | {i[2]} | Enviado em: {i[3][:19]}\n"
    import logging
    import os
    from datetime import datetime, timedelta
    from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
    import aiosqlite
    import pandas as pd
    from pyzbar.pyzbar import decode
    from PIL import Image
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
    FOTOS_DIR = os.path.join(os.path.dirname(__file__), '../fotos')

    async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
# Estado para exclusão
EXCLUIR_CONFIRMA = 500
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
# Estado para retorno de reparo
RETORNO_CONFIRMA = 400
async def retornar_reparo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await db.commit()
    await update.message.reply_text('Item retornou ao estoque com sucesso!')
    return ConversationHandler.END
# Estados para envio de reparo
REPARO_FORNECEDOR, REPARO_DATA = range(300, 302)
async def enviar_reparo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        # Atualiza status, info_reparo e decrementa quantidade
        await db.execute("UPDATE itens SET status = 'Em Reparo Externo', info_reparo = ?, quantidade = quantidade - 1 WHERE id = ?", (info_reparo, item_id))
        await db.commit()
    await update.message.reply_text('Item enviado para reparo externo com sucesso!')
    return ConversationHandler.END
# Estados para atualização
ATUAL_ESCOLHA, ATUAL_NOME, ATUAL_DESC, ATUAL_QTD, ATUAL_FOTO = range(200, 205)
async def atualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem atualizar itens.')
        return ConversationHandler.END
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem enviar itens para reparo.')
        return ConversationHandler.END
    if not is_admin(update.effective_user.id):
        await update.message.reply_text('Apenas administradores podem registrar retorno de reparo.')
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
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton('Cadastrar Novo Item', callback_data='menu_novoitem')],
        [InlineKeyboardButton('Buscar Itens', callback_data='menu_buscar')],
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
    if query.data == 'menu_novoitem':
        await query.message.reply_text('Use /novoitem para cadastrar um novo item.')
    elif query.data == 'menu_buscar':
        await query.message.reply_text('Use /buscar <palavra-chave> para buscar itens.')
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
import logging
import os
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler)
import aiosqlite
from datetime import datetime


# Estados para ConversationHandler
FOTO, NOME, DESCRICAO, QUANTIDADE, CONFIRMACAO = range(5)

# Estados para busca
BUSCA_ESCOLHA = range(100, 101)
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

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
FOTOS_DIR = os.path.join(os.path.dirname(__file__), '../fotos')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá! Eu sou o Assistente de Estoque. Use /novoitem para cadastrar um novo item.')

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

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Operação cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app.add_handler(CommandHandler('ajuda', ajuda))
    app.add_handler(CommandHandler('backup', backup))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.CaptionRegex('^/restaurar'), restaurar))
    app.add_handler(CommandHandler('gerar_qr', gerar_qr))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex('^/buscar_qr'), buscar_qr))
    app.add_handler(CommandHandler('verificar_alertas', verificar_alertas))
    app.add_handler(CommandHandler('historico', historico))
    app.add_handler(CommandHandler('relatorio', relatorio))
    excluir_conv = ConversationHandler(
        entry_points=[CommandHandler('excluir', excluir)],
        states={
            EXCLUIR_CONFIRMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_exclusao)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    app.add_handler(excluir_conv)
    retorno_reparo_conv = ConversationHandler(
        entry_points=[CommandHandler('retornar_reparo', retornar_reparo)],
        states={
            RETORNO_CONFIRMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_retorno)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    app.add_handler(retorno_reparo_conv)
    enviar_reparo_conv = ConversationHandler(
        entry_points=[CommandHandler('enviar_reparo', enviar_reparo)],
        states={
            REPARO_FORNECEDOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_fornecedor)],
            REPARO_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_data_envio)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    app.add_handler(enviar_reparo_conv)
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
    app.add_handler(atualizar_conv)
    app.add_handler(CommandHandler('menu', menu))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r'^menu_'))
    import asyncio
    import sys
    logging.basicConfig(level=logging.INFO)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print('Defina a variável de ambiente TELEGRAM_BOT_TOKEN')
        sys.exit(1)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
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

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('buscar', buscar))
    app.add_handler(CallbackQueryHandler(mostrar_detalhe_item))

    app.run_polling()

if __name__ == '__main__':
    main()
