#!/usr/bin/env python3
"""
Servidor Flask para hospedar o WebApp de Inventário
Fornece endpoints para servir arquivos estáticos e APIs
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import aiosqlite
import asyncio

# Configurações
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), '../webapp')
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 8080))

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para desenvolvimento

# Configurar logs
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Servir página principal do WebApp"""
    return send_from_directory(WEBAPP_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Servir arquivos estáticos (CSS, JS, etc.)"""
    return send_from_directory(WEBAPP_DIR, filename)

@app.route('/api/health')
def health_check():
    """Endpoint de verificação de saúde"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'webapp_url': f'http://{HOST}:{PORT}'
    })

@app.route('/api/items/<int:item_id>')
def get_item(item_id):
    """Buscar item por ID"""
    try:
        # Conectar ao banco SQLite
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        cursor = conn.cursor()
        
        # Buscar item
        cursor.execute('SELECT * FROM itens WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Item não encontrado'}), 404
        
        # Converter para dicionário
        item = dict(row)
        
        # Adicionar log de acesso
        logger.info(f'Item {item_id} acessado: {item["nome"]}')
        
        conn.close()
        
        return jsonify(item)
        
    except Exception as e:
        logger.error(f'Erro ao buscar item {item_id}: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/items/search')
def search_items():
    """Buscar itens por termo"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query:
            return jsonify({'items': []})
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar em nome, código e categoria
        search_query = f'%{query}%'
        cursor.execute('''
            SELECT * FROM itens 
            WHERE nome LIKE ? OR codigo LIKE ? OR categoria LIKE ?
            ORDER BY nome
            LIMIT ?
        ''', (search_query, search_query, search_query, limit))
        
        rows = cursor.fetchall()
        items = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({'items': items, 'count': len(items)})
        
    except Exception as e:
        logger.error(f'Erro na busca: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/inventory/finish', methods=['POST'])
def finish_inventory():
    """Receber dados do inventário finalizado"""
    try:
        data = request.get_json()
        
        if not data or 'items' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Salvar dados do inventário
        inventory_data = {
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'user_id': data.get('user', {}).get('id'),
            'user_name': data.get('user', {}).get('name'),
            'total_items': len(data['items']),
            'items': data['items'],
            'summary': data.get('summary', {})
        }
        
        # Salvar em arquivo para processamento posterior
        save_inventory_data(inventory_data)
        
        # Log da operação
        logger.info(f'Inventário finalizado: {inventory_data["total_items"]} itens')
        
        return jsonify({
            'status': 'success',
            'message': 'Inventário recebido com sucesso',
            'inventory_id': inventory_data['timestamp']
        })
        
    except Exception as e:
        logger.error(f'Erro ao finalizar inventário: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

def save_inventory_data(data):
    """Salvar dados do inventário em arquivo JSON"""
    try:
        # Criar diretório se não existir
        inventory_dir = os.path.join(os.path.dirname(__file__), '../inventarios')
        os.makedirs(inventory_dir, exist_ok=True)
        
        # Nome do arquivo baseado no timestamp
        timestamp = data['timestamp'].replace(':', '-').replace('.', '-')
        filename = f'inventario_{timestamp}.json'
        filepath = os.path.join(inventory_dir, filename)
        
        # Salvar arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f'Inventário salvo em: {filepath}')
        
    except Exception as e:
        logger.error(f'Erro ao salvar inventário: {str(e)}')

@app.route('/api/inventories')
def list_inventories():
    """Listar inventários salvos"""
    try:
        inventory_dir = os.path.join(os.path.dirname(__file__), '../inventarios')
        
        if not os.path.exists(inventory_dir):
            return jsonify({'inventories': []})
        
        inventories = []
        for filename in sorted(os.listdir(inventory_dir), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(inventory_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    inventories.append({
                        'filename': filename,
                        'timestamp': data.get('timestamp'),
                        'user_name': data.get('user_name'),
                        'total_items': data.get('total_items', 0),
                        'summary': data.get('summary', {})
                    })
                except Exception as e:
                    logger.warning(f'Erro ao ler {filename}: {str(e)}')
        
        return jsonify({'inventories': inventories})
        
    except Exception as e:
        logger.error(f'Erro ao listar inventários: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/inventories/<filename>')
def get_inventory(filename):
    """Obter dados completos de um inventário"""
    try:
        inventory_dir = os.path.join(os.path.dirname(__file__), '../inventarios')
        filepath = os.path.join(inventory_dir, filename)
        
        if not os.path.exists(filepath) or not filename.endswith('.json'):
            return jsonify({'error': 'Inventário não encontrado'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f'Erro ao obter inventário {filename}: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/stats')
def get_stats():
    """Obter estatísticas do sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar itens totais
        cursor.execute('SELECT COUNT(*) FROM itens')
        total_items = cursor.fetchone()[0]
        
        # Contar por categoria
        cursor.execute('''
            SELECT categoria, COUNT(*) as count 
            FROM itens 
            GROUP BY categoria 
            ORDER BY count DESC
        ''')
        categories = [{'name': row[0] or 'Sem categoria', 'count': row[1]} 
                     for row in cursor.fetchall()]
        
        # Valor total do estoque (se houver campo valor)
        cursor.execute('SELECT SUM(quantidade) FROM itens')
        total_quantity = cursor.fetchone()[0] or 0
        
        conn.close()
        
        # Contar inventários
        inventory_dir = os.path.join(os.path.dirname(__file__), '../inventarios')
        inventory_count = 0
        if os.path.exists(inventory_dir):
            inventory_count = len([f for f in os.listdir(inventory_dir) if f.endswith('.json')])
        
        return jsonify({
            'total_items': total_items,
            'total_quantity': total_quantity,
            'categories': categories,
            'inventory_count': inventory_count,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Erro ao obter estatísticas: {str(e)}')
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    logger.error(f'Erro interno: {str(error)}')
    return jsonify({'error': 'Erro interno do servidor'}), 500

def create_directories():
    """Criar diretórios necessários"""
    directories = [
        os.path.join(os.path.dirname(__file__), '../inventarios'),
        os.path.join(os.path.dirname(__file__), '../logs')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f'Diretório criado/verificado: {directory}')

def check_database():
    """Verificar se o banco de dados existe"""
    if not os.path.exists(DB_PATH):
        logger.warning(f'Banco de dados não encontrado: {DB_PATH}')
        logger.info('Execute: python db/init_db.py para criar o banco')
        return False
    return True

if __name__ == '__main__':
    logger.info('Iniciando servidor WebApp...')
    
    # Criar diretórios necessários
    create_directories()
    
    # Verificar banco de dados
    if not check_database():
        logger.error('Banco de dados não encontrado!')
        exit(1)
    
    # Exibir informações de inicialização
    logger.info(f'WebApp disponível em: http://{HOST}:{PORT}')
    logger.info(f'Diretório WebApp: {WEBAPP_DIR}')
    logger.info(f'Banco de dados: {DB_PATH}')
    
    # Iniciar servidor
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=False,  # Definir como True apenas para desenvolvimento
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info('Servidor parado pelo usuário')
    except Exception as e:
        logger.error(f'Erro ao iniciar servidor: {str(e)}')
        exit(1)
