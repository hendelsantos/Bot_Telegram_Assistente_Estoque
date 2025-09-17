#!/usr/bin/env python3
"""
API REST Simplificada para Sistema de Estoque
Funcional e pronta para uso
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from functools import wraps
import sqlite3
import json
import os
import time
import hashlib
from datetime import datetime
import logging

# Configuração
app = Flask(__name__)
CORS(app)

# Configurações
API_VERSION = 'v1'
BASE_PATH = f'/api/{API_VERSION}'
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')

# Rate limiting simples
request_counts = {}
RATE_LIMIT = 100

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== AUTENTICAÇÃO ====================

def require_api_key(f):
    """Decorator para exigir API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required', 'success': False}), 401
        
        # Rate limiting básico
        client_ip = request.remote_addr
        now = time.time()
        hour_ago = now - 3600
        
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        
        request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] if req_time > hour_ago]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return jsonify({'error': 'Rate limit exceeded', 'success': False}), 429
        
        request_counts[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

# ==================== UTILITÁRIOS ====================

def get_db_connection():
    """Conexão com banco SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para retornar como dicionário
    return conn

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

# ==================== ENDPOINTS ====================

@app.route(f'{BASE_PATH}/')
def api_info():
    """Informações da API"""
    return success_response({
        'name': 'Sistema de Estoque API',
        'version': API_VERSION,
        'description': 'API REST para gerenciamento de estoque',
        'endpoints': [
            'GET /api/v1/items - Listar itens',
            'GET /api/v1/items/{code} - Item específico',
            'POST /api/v1/items - Criar item',
            'PUT /api/v1/items/{code} - Atualizar item',
            'DELETE /api/v1/items/{code} - Remover item',
            'GET /api/v1/items/search - Buscar itens',
            'GET /api/v1/categories - Listar categorias',
            'GET /api/v1/reports/dashboard - Estatísticas'
        ],
        'authentication': 'Header: X-API-Key',
        'documentation': f'{BASE_PATH}/docs'
    })

@app.route(f'{BASE_PATH}/docs')
def api_docs():
    """Documentação da API"""
    try:
        return send_from_directory('static', 'api-docs.html')
    except:
        return jsonify({
            'message': 'Documentação disponível em HTML',
            'endpoints': 'Veja /api/v1/ para lista de endpoints'
        })

@app.route(f'{BASE_PATH}/items', methods=['GET'])
@require_api_key
def get_items():
    """Listar todos os itens"""
    try:
        limit = min(int(request.args.get('limit', 50)), 1000)
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        low_stock = request.args.get('low_stock', '').lower() == 'true'
        
        with get_db_connection() as conn:
            query = "SELECT * FROM itens WHERE 1=1"
            params = []
            
            if category:
                query += " AND categoria = ?"
                params.append(category)
            
            if low_stock:
                query += " AND quantidade < 5"
            
            query += " ORDER BY nome LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            items = [dict(row) for row in cursor.fetchall()]
            
            # Contar total
            count_query = "SELECT COUNT(*) FROM itens WHERE 1=1"
            count_params = []
            if category:
                count_query += " AND categoria = ?"
                count_params.append(category)
            if low_stock:
                count_query += " AND quantidade < 5"
                
            total = conn.execute(count_query, count_params).fetchone()[0]
        
        return success_response({
            'items': items,
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
def get_item(code):
    """Obter item específico por código"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM itens WHERE codigo = ?", (code,))
            item = cursor.fetchone()
            
            if not item:
                return error_response("Item não encontrado", 404)
            
            return success_response(dict(item))
        
    except Exception as e:
        logger.error(f"Erro ao buscar item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items', methods=['POST'])
@require_api_key
def create_item():
    """Criar novo item"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return error_response("Nome é obrigatório")
        
        # Gerar código automático simples
        nome = data['nome'].upper()
        prefixo = ''.join([c for c in nome.split()[0][:4] if c.isalpha()])
        
        with get_db_connection() as conn:
            # Buscar próximo número
            cursor = conn.execute(
                "SELECT COUNT(*) FROM itens WHERE codigo LIKE ?", 
                (f"{prefixo}-%",)
            )
            count = cursor.fetchone()[0] + 1
            codigo = f"{prefixo}-{count:03d}"
            
            # Inserir item
            conn.execute("""
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
            conn.commit()
        
        return success_response({
            'codigo': codigo,
            'nome': data['nome']
        }, "Item criado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao criar item: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/<code>', methods=['PUT'])
@require_api_key
def update_item(code):
    """Atualizar item existente"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Dados não fornecidos")
        
        with get_db_connection() as conn:
            # Verificar se item existe
            cursor = conn.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
            if not cursor.fetchone():
                return error_response("Item não encontrado", 404)
            
            # Construir query de update
            update_fields = []
            params = []
            
            allowed_fields = ['nome', 'descricao', 'quantidade', 'categoria', 
                            'localizacao', 'fornecedor', 'preco_unitario']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if not update_fields:
                return error_response("Nenhum campo válido para atualizar")
            
            update_fields.append("data_atualizacao = ?")
            params.append(datetime.now().isoformat())
            params.append(code)
            
            query = f"UPDATE itens SET {', '.join(update_fields)} WHERE codigo = ?"
            conn.execute(query, params)
            conn.commit()
        
        return success_response({
            'codigo': code,
            'updated_fields': [k for k in data.keys() if k in allowed_fields]
        }, "Item atualizado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/<code>', methods=['DELETE'])
@require_api_key
def delete_item(code):
    """Remover item"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
            if not cursor.fetchone():
                return error_response("Item não encontrado", 404)
            
            conn.execute("DELETE FROM itens WHERE codigo = ?", (code,))
            conn.commit()
        
        return success_response({'codigo': code}, "Item removido com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao remover item {code}: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/items/search', methods=['GET'])
@require_api_key
def search_items():
    """Buscar itens"""
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query_term:
            return error_response("Termo de busca é obrigatório")
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM itens 
                WHERE nome LIKE ? OR codigo LIKE ? OR descricao LIKE ? OR categoria LIKE ?
                ORDER BY 
                    CASE 
                        WHEN nome LIKE ? THEN 1
                        WHEN codigo LIKE ? THEN 2
                        ELSE 3
                    END
                LIMIT ?
            """, (
                f'%{query_term}%', f'%{query_term}%', f'%{query_term}%', f'%{query_term}%',
                f'%{query_term}%', f'%{query_term}%', limit
            ))
            
            items = [dict(row) for row in cursor.fetchall()]
        
        return success_response({
            'query': query_term,
            'results': items,
            'count': len(items)
        })
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/categories', methods=['GET'])
@require_api_key
def get_categories():
    """Listar categorias"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT categoria, COUNT(*) as count, SUM(quantidade) as total_quantity
                FROM itens 
                WHERE categoria IS NOT NULL AND categoria != ''
                GROUP BY categoria 
                ORDER BY count DESC
            """)
            
            categories = [
                {
                    'name': row['categoria'],
                    'item_count': row['count'],
                    'total_quantity': row['total_quantity'] or 0
                }
                for row in cursor.fetchall()
            ]
        
        return success_response(categories)
        
    except Exception as e:
        logger.error(f"Erro ao buscar categorias: {e}")
        return error_response("Erro interno do servidor", 500)

@app.route(f'{BASE_PATH}/reports/dashboard', methods=['GET'])
@require_api_key
def dashboard_stats():
    """Estatísticas para dashboard"""
    try:
        with get_db_connection() as conn:
            stats = {}
            
            # Total de itens
            stats['total_items'] = conn.execute("SELECT COUNT(*) FROM itens").fetchone()[0]
            
            # Quantidade total
            result = conn.execute("SELECT SUM(quantidade) FROM itens").fetchone()[0]
            stats['total_quantity'] = result or 0
            
            # Estoque baixo
            stats['low_stock_items'] = conn.execute(
                "SELECT COUNT(*) FROM itens WHERE quantidade < 5"
            ).fetchone()[0]
            
            # Valor total
            result = conn.execute("SELECT SUM(quantidade * preco_unitario) FROM itens").fetchone()[0]
            stats['total_value'] = float(result or 0)
            
            # Top categorias
            cursor = conn.execute("""
                SELECT categoria, COUNT(*) as count 
                FROM itens 
                WHERE categoria IS NOT NULL AND categoria != ''
                GROUP BY categoria 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats['top_categories'] = [
                {'category': row['categoria'], 'count': row['count']} 
                for row in cursor.fetchall()
            ]
            
            # Itens recentes
            cursor = conn.execute("""
                SELECT codigo, nome, data_cadastro 
                FROM itens 
                ORDER BY data_cadastro DESC 
                LIMIT 5
            """)
            stats['recent_items'] = [
                {'code': row['codigo'], 'name': row['nome'], 'date': row['data_cadastro']}
                for row in cursor.fetchall()
            ]
        
        return success_response(stats)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return error_response("Erro interno do servidor", 500)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return error_response("Endpoint não encontrado", 404)

@app.errorhandler(500)
def internal_error(error):
    return error_response("Erro interno do servidor", 500)

# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 API REST iniciando na porta {port}")
    logger.info(f"📚 Documentação: http://localhost:{port}/api/v1/docs")
    logger.info(f"🔗 Endpoints: http://localhost:{port}/api/v1/")
    
    app.run(host='0.0.0.0', port=port, debug=True)
