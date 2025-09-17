#!/usr/bin/env python3
"""
API REST Avançada para Sistema de Estoque
Endpoints profissionais com documentação OpenAPI
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from functools import wraps
import sqlite3
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
import logging

# Configuração
app = Flask(__name__)
CORS(app)

# Configurações de segurança
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
API_VERSION = 'v1'
BASE_PATH = f'/api/{API_VERSION}'

# Rate limiting simples
request_counts = {}
RATE_LIMIT = 100  # requests por hora

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')

# ==================== AUTENTICAÇÃO ====================

def generate_api_key(user_id):
    """Gera API key para usuário"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()

def require_api_key(f):
    """Decorator para exigir API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Verificar rate limiting
        client_ip = request.remote_addr
        now = time.time()
        hour_ago = now - 3600
        
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        
        # Limpar requests antigos
        request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] if req_time > hour_ago]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        request_counts[client_ip].append(now)
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== UTILITÁRIOS ====================

def get_db_connection():
    """Conexão com banco SQLite"""
    return sqlite3.connect(DB_PATH)

def success_response(data, message="Success"):
    """Resposta de sucesso padronizada"""
    return jsonify({
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    })

def error_response(message, code=400):
    """Resposta de erro padronizada"""
    return jsonify({
        'success': False,
        'error': message,
        'timestamp': datetime.utcnow().isoformat()
    }), code

# ==================== ENDPOINTS DE DOCUMENTAÇÃO ====================

@app.route(f'{BASE_PATH}/')
def api_info():
    """Informações da API"""
    return success_response({
        'name': 'Sistema de Estoque API',
        'version': API_VERSION,
        'description': 'API REST para gerenciamento de estoque',
        'endpoints': {
            'items': f'{BASE_PATH}/items',
            'search': f'{BASE_PATH}/items/search',
            'categories': f'{BASE_PATH}/categories',
            'reports': f'{BASE_PATH}/reports',
            'webhooks': f'{BASE_PATH}/webhooks'
        },
        'documentation': f'{BASE_PATH}/docs'
    })

@app.route(f'{BASE_PATH}/docs')
def api_docs():
    """Documentação da API em formato OpenAPI"""
    return send_from_directory('static', 'api-docs.html')

# ==================== ENDPOINTS DE ITENS ====================

@app.route(f'{BASE_PATH}/items', methods=['GET'])
@require_api_key
def get_items():
    """
    Listar todos os itens
    Query params:
    - limit: número máximo de itens (padrão: 50)
    - offset: pular N itens (padrão: 0)
    - category: filtrar por categoria
    - low_stock: apenas itens com estoque baixo (true/false)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        low_stock = request.args.get('low_stock', '').lower() == 'true'
        
        with get_db_connection() as db:
            query = "SELECT * FROM itens WHERE 1=1"
            params = []
            
            if category:
                query += " AND categoria = ?"
                params.append(category)
            
            if low_stock:
                query += " AND quantidade < 5"
            
            query += " ORDER BY nome LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = db.execute(query, params)
            items = cursor.fetchall()
            
            # Converter para dicionários
            columns = [description[0] for description in cursor.description]
            items_list = [dict(zip(columns, item)) for item in items]
            
            # Contar total
            count_query = "SELECT COUNT(*) FROM itens WHERE 1=1"
            count_params = []
            if category:
                count_query += " AND categoria = ?"
                count_params.append(category)
            if low_stock:
                count_query += " AND quantidade < 5"
                
            cursor = db.execute(count_query, count_params)
            total = cursor.fetchone()[0]
        
        return success_response({
            'items': items_list,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar itens: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/<code>', methods=['GET'])
@require_api_key
async def get_item(code):
    """Obter item específico por código"""
    try:
        async with await get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM itens WHERE codigo = ?", (code,))
            item = await cursor.fetchone()
            
            if not item:
                return error_response("Item não encontrado", 404)
            
            columns = [description[0] for description in cursor.description]
            item_dict = dict(zip(columns, item))
        
        return success_response(item_dict)
        
    except Exception as e:
        logger.error(f"Erro ao buscar item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items', methods=['POST'])
@require_api_key
async def create_item():
    """
    Criar novo item
    Body JSON:
    {
        "nome": "string",
        "descricao": "string",
        "quantidade": number,
        "categoria": "string",
        "localizacao": "string",
        "fornecedor": "string",
        "preco_unitario": number
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return error_response("Nome é obrigatório")
        
        # Gerar código automático
        from utils.code_generator import CodeGenerator
        code_gen = CodeGenerator(DB_PATH)
        codigo = await code_gen.generate_code(data['nome'])
        
        async with await get_db_connection() as db:
            await db.execute("""
                INSERT INTO itens (codigo, nome, descricao, quantidade, categoria, 
                                 localizacao, fornecedor, preco_unitario, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                data['nome'],
                data.get('descricao', ''),
                data.get('quantidade', 0),
                data.get('categoria', ''),
                data.get('localizacao', ''),
                data.get('fornecedor', ''),
                data.get('preco_unitario', 0.0),
                datetime.now().isoformat()
            ))
            await db.commit()
        
        return success_response({
            'codigo': codigo,
            'message': f'Item {codigo} criado com sucesso'
        }, "Item criado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao criar item: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/<code>', methods=['PUT'])
@require_api_key
async def update_item(code):
    """Atualizar item existente"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Dados não fornecidos")
        
        # Verificar se item existe
        async with await get_db_connection() as db:
            cursor = await db.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
            item = await cursor.fetchone()
            
            if not item:
                return error_response("Item não encontrado", 404)
            
            # Construir query de update dinamicamente
            update_fields = []
            params = []
            
            for field in ['nome', 'descricao', 'quantidade', 'categoria', 
                         'localizacao', 'fornecedor', 'preco_unitario']:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if not update_fields:
                return error_response("Nenhum campo para atualizar")
            
            update_fields.append("data_atualizacao = ?")
            params.append(datetime.now().isoformat())
            params.append(code)
            
            query = f"UPDATE itens SET {', '.join(update_fields)} WHERE codigo = ?"
            await db.execute(query, params)
            await db.commit()
        
        return success_response({
            'codigo': code,
            'updated_fields': list(data.keys())
        }, "Item atualizado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/<code>', methods=['DELETE'])
@require_api_key
async def delete_item(code):
    """Remover item"""
    try:
        async with await get_db_connection() as db:
            cursor = await db.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
            item = await cursor.fetchone()
            
            if not item:
                return error_response("Item não encontrado", 404)
            
            await db.execute("DELETE FROM itens WHERE codigo = ?", (code,))
            await db.commit()
        
        return success_response({
            'codigo': code
        }, "Item removido com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao remover item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== ENDPOINTS DE BUSCA ====================

@app.route(f'{BASE_PATH}/items/search', methods=['GET'])
@require_api_key
async def search_items():
    """
    Buscar itens
    Query params:
    - q: termo de busca
    - limit: máximo de resultados
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query_term:
            return error_response("Termo de busca é obrigatório")
        
        async with await get_db_connection() as db:
            cursor = await db.execute("""
                SELECT * FROM itens 
                WHERE nome LIKE ? OR codigo LIKE ? OR descricao LIKE ? OR categoria LIKE ?
                ORDER BY 
                    CASE 
                        WHEN nome LIKE ? THEN 1
                        WHEN codigo LIKE ? THEN 2
                        WHEN categoria LIKE ? THEN 3
                        ELSE 4
                    END
                LIMIT ?
            """, (
                f'%{query_term}%', f'%{query_term}%', f'%{query_term}%', f'%{query_term}%',
                f'%{query_term}%', f'%{query_term}%', f'%{query_term}%',
                limit
            ))
            
            items = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            items_list = [dict(zip(columns, item)) for item in items]
        
        return success_response({
            'query': query_term,
            'results': items_list,
            'count': len(items_list)
        })
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== ENDPOINTS DE CATEGORIAS ====================

@app.route(f'{BASE_PATH}/categories', methods=['GET'])
@require_api_key
async def get_categories():
    """Listar todas as categorias com contagem"""
    try:
        async with await get_db_connection() as db:
            cursor = await db.execute("""
                SELECT categoria, COUNT(*) as count, SUM(quantidade) as total_quantity
                FROM itens 
                WHERE categoria IS NOT NULL AND categoria != ''
                GROUP BY categoria 
                ORDER BY count DESC
            """)
            categories = await cursor.fetchall()
            
            categories_list = [
                {
                    'name': cat[0],
                    'item_count': cat[1],
                    'total_quantity': cat[2]
                }
                for cat in categories
            ]
        
        return success_response(categories_list)
        
    except Exception as e:
        logger.error(f"Erro ao buscar categorias: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== ENDPOINTS DE RELATÓRIOS ====================

@app.route(f'{BASE_PATH}/reports/dashboard', methods=['GET'])
@require_api_key
async def dashboard_stats():
    """Estatísticas para dashboard"""
    try:
        async with await get_db_connection() as db:
            # Estatísticas gerais
            stats = {}
            
            # Total de itens
            cursor = await db.execute("SELECT COUNT(*) FROM itens")
            stats['total_items'] = (await cursor.fetchone())[0]
            
            # Quantidade total
            cursor = await db.execute("SELECT SUM(quantidade) FROM itens")
            stats['total_quantity'] = (await cursor.fetchone())[0] or 0
            
            # Estoque baixo
            cursor = await db.execute("SELECT COUNT(*) FROM itens WHERE quantidade < 5")
            stats['low_stock_items'] = (await cursor.fetchone())[0]
            
            # Valor total do estoque
            cursor = await db.execute("SELECT SUM(quantidade * preco_unitario) FROM itens")
            stats['total_value'] = (await cursor.fetchone())[0] or 0
            
            # Top categorias
            cursor = await db.execute("""
                SELECT categoria, COUNT(*) as count 
                FROM itens 
                WHERE categoria IS NOT NULL AND categoria != ''
                GROUP BY categoria 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats['top_categories'] = [
                {'category': row[0], 'count': row[1]} 
                for row in await cursor.fetchall()
            ]
            
            # Itens recentes
            cursor = await db.execute("""
                SELECT codigo, nome, data_cadastro 
                FROM itens 
                ORDER BY data_cadastro DESC 
                LIMIT 5
            """)
            stats['recent_items'] = [
                {'code': row[0], 'name': row[1], 'date': row[2]}
                for row in await cursor.fetchall()
            ]
        
        return success_response(stats)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== WEBHOOKS ====================

@app.route(f'{BASE_PATH}/webhooks/stock-alert', methods=['POST'])
@require_api_key
async def stock_alert_webhook():
    """Webhook para alertas de estoque baixo"""
    try:
        data = request.get_json()
        webhook_url = data.get('webhook_url')
        threshold = data.get('threshold', 5)
        
        if not webhook_url:
            return error_response("URL do webhook é obrigatória")
        
        # Buscar itens com estoque baixo
        async with await get_db_connection() as db:
            cursor = await db.execute("""
                SELECT codigo, nome, quantidade 
                FROM itens 
                WHERE quantidade < ?
            """, (threshold,))
            low_stock_items = await cursor.fetchall()
        
        if low_stock_items:
            # Aqui você enviaria para o webhook
            # requests.post(webhook_url, json={'low_stock_items': low_stock_items})
            pass
        
        return success_response({
            'webhook_url': webhook_url,
            'threshold': threshold,
            'low_stock_count': len(low_stock_items)
        }, "Webhook configurado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
