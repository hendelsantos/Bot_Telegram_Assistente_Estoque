#!/usr/bin/env python3
"""
API REST Ultra Simples - Apenas bibliotecas padrão do Python
Sistema de Estoque - Funcional e pronta para uso
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import os
import time
import urllib.parse
from datetime import datetime
import logging

# Configurações
API_VERSION = 'v1'
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/estoque.db')
PORT = 5000

# Rate limiting simples
request_counts = {}
RATE_LIMIT = 100

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EstoqueAPIHandler(BaseHTTPRequestHandler):
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Define headers da resposta"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()
    
    def _authenticate(self):
        """Verifica autenticação"""
        api_key = self.headers.get('X-API-Key')
        if not api_key:
            return False
        
        # Rate limiting básico
        client_ip = self.client_address[0]
        now = time.time()
        hour_ago = now - 3600
        
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        
        request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] if req_time > hour_ago]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return False
        
        request_counts[client_ip].append(now)
        return True
    
    def _get_db_connection(self):
        """Conexão com banco SQLite"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # A tabela já existe com estrutura diferente, não precisamos criar
        return conn
    
    def _success_response(self, data, message="Success"):
        """Resposta de sucesso padronizada"""
        return json.dumps({
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False, indent=2)
    
    def _error_response(self, message, status_code=400):
        """Resposta de erro padronizada"""
        self._set_headers(status_code)
        response = json.dumps({
            'success': False,
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        }, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode())
    
    def _parse_body(self):
        """Parse do corpo da requisição"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode())
            return {}
        except:
            return {}
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        path_parts = self.path.split('?')
        path = path_parts[0]
        query_params = {}
        
        if len(path_parts) > 1:
            query_params = dict(urllib.parse.parse_qsl(path_parts[1]))
        
        # Rotas
        if path == f'/api/{API_VERSION}/':
            self._handle_api_info()
        elif path == f'/api/{API_VERSION}/items':
            self._handle_get_items(query_params)
        elif path.startswith(f'/api/{API_VERSION}/items/') and path.endswith('/search'):
            self._handle_search_items(query_params)
        elif path.startswith(f'/api/{API_VERSION}/items/'):
            code = path.split('/')[-1]
            self._handle_get_item(code)
        elif path == f'/api/{API_VERSION}/categories':
            self._handle_get_categories()
        elif path == f'/api/{API_VERSION}/reports/dashboard':
            self._handle_dashboard()
        else:
            self._error_response("Endpoint não encontrado", 404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == f'/api/{API_VERSION}/items':
            self._handle_create_item()
        else:
            self._error_response("Endpoint não encontrado", 404)
    
    def do_PUT(self):
        """Handle PUT requests"""
        if self.path.startswith(f'/api/{API_VERSION}/items/'):
            code = self.path.split('/')[-1]
            self._handle_update_item(code)
        else:
            self._error_response("Endpoint não encontrado", 404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith(f'/api/{API_VERSION}/items/'):
            code = self.path.split('/')[-1]
            self._handle_delete_item(code)
        else:
            self._error_response("Endpoint não encontrado", 404)
    
    def _handle_api_info(self):
        """Informações da API"""
        self._set_headers()
        response = self._success_response({
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
            'authentication': 'Header: X-API-Key'
        })
        self.wfile.write(response.encode())
    
    def _handle_get_items(self, params):
        """Listar itens"""
        if not self._authenticate():
            self._error_response("API key required ou rate limit exceeded", 401)
            return
        
        try:
            limit = min(int(params.get('limit', 50)), 1000)
            offset = int(params.get('offset', 0))
            category = params.get('category')
            low_stock = params.get('low_stock', '').lower() == 'true'
            
            with self._get_db_connection() as conn:
                query = "SELECT * FROM itens WHERE 1=1"
                query_params = []
                
                if category:
                    query += " AND categoria = ?"
                    query_params.append(category)
                
                if low_stock:
                    query += " AND quantidade < 5"
                
                query += " ORDER BY nome LIMIT ? OFFSET ?"
                query_params.extend([limit, offset])
                
                cursor = conn.execute(query, query_params)
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
            
            self._set_headers()
            response = self._success_response({
                'items': items,
                'pagination': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total
                }
            })
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao buscar itens: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_get_item(self, code):
        """Obter item específico"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM itens WHERE codigo = ?", (code,))
                item = cursor.fetchone()
                
                if not item:
                    self._error_response("Item não encontrado", 404)
                    return
                
                self._set_headers()
                response = self._success_response(dict(item))
                self.wfile.write(response.encode())
                
        except Exception as e:
            logger.error(f"Erro ao buscar item {code}: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_create_item(self):
        """Criar novo item"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            data = self._parse_body()
            
            if not data or not data.get('nome'):
                self._error_response("Nome é obrigatório")
                return
            
            # Gerar código automático
            nome = data['nome'].upper()
            prefixo = ''.join([c for c in nome.split()[0][:4] if c.isalpha()])
            
            with self._get_db_connection() as conn:
                # Buscar próximo número
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM itens WHERE codigo LIKE ?", 
                    (f"{prefixo}-%",)
                )
                count = cursor.fetchone()[0] + 1
                codigo = f"{prefixo}-{count:03d}"
                
                # Inserir item
                # Inserir item
            conn.execute("""
                INSERT INTO itens (codigo, nome, descricao, quantidade, categoria, 
                                 localizacao, status, data_cadastro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                data['nome'],
                data.get('descricao', ''),
                data.get('quantidade', 0),
                data.get('categoria', ''),
                data.get('localizacao', ''),
                'ativo',
                datetime.now().isoformat()
            ))
            conn.commit()
            
            self._set_headers(201)
            response = self._success_response({
                'codigo': codigo,
                'nome': data['nome']
            }, "Item criado com sucesso")
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao criar item: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_update_item(self, code):
        """Atualizar item"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            data = self._parse_body()
            
            if not data:
                self._error_response("Dados não fornecidos")
                return
            
            with self._get_db_connection() as conn:
                # Verificar se item existe
                cursor = conn.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
                if not cursor.fetchone():
                    self._error_response("Item não encontrado", 404)
                    return
                
            # Construir query de update
            update_fields = []
            params = []
            
            allowed_fields = ['nome', 'descricao', 'quantidade', 'categoria', 
                            'localizacao', 'status']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if not update_fields:
                self._error_response("Nenhum campo válido para atualizar")
                return
            
            update_fields.append("data_cadastro = ?")
            params.append(datetime.now().isoformat())
            params.append(code)
            
            query = f"UPDATE itens SET {', '.join(update_fields)} WHERE codigo = ?"
            conn.execute(query, params)
            conn.commit()
            
            self._set_headers()
            response = self._success_response({
                'codigo': code,
                'updated_fields': [k for k in data.keys() if k in allowed_fields]
            }, "Item atualizado com sucesso")
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao atualizar item {code}: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_delete_item(self, code):
        """Remover item"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("SELECT id FROM itens WHERE codigo = ?", (code,))
                if not cursor.fetchone():
                    self._error_response("Item não encontrado", 404)
                    return
                
                conn.execute("DELETE FROM itens WHERE codigo = ?", (code,))
                conn.commit()
            
            self._set_headers()
            response = self._success_response({'codigo': code}, "Item removido com sucesso")
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao remover item {code}: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_search_items(self, params):
        """Buscar itens"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            query_term = params.get('q', '').strip()
            limit = min(int(params.get('limit', 20)), 100)
            
            if not query_term:
                self._error_response("Termo de busca é obrigatório")
                return
            
            with self._get_db_connection() as conn:
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
            
            self._set_headers()
            response = self._success_response({
                'query': query_term,
                'results': items,
                'count': len(items)
            })
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_get_categories(self):
        """Listar categorias"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            with self._get_db_connection() as conn:
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
            
            self._set_headers()
            response = self._success_response(categories)
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            self._error_response("Erro interno do servidor", 500)
    
    def _handle_dashboard(self):
        """Estatísticas para dashboard"""
        if not self._authenticate():
            self._error_response("API key required", 401)
            return
        
        try:
            with self._get_db_connection() as conn:
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
                
            # Valor total - removido pois não há coluna preco_unitario
            # stats['total_value'] = 0.0                # Top categorias
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
            
            self._set_headers()
            response = self._success_response(stats)
            self.wfile.write(response.encode())
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            self._error_response("Erro interno do servidor", 500)

def run_server():
    """Iniciar servidor"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, EstoqueAPIHandler)
    
    print(f"🚀 API REST iniciando na porta {PORT}")
    print(f"📚 Endpoints: http://localhost:{PORT}/api/v1/")
    print(f"🔑 Use o header: X-API-Key: test-key-123")
    print("\n🔗 Endpoints disponíveis:")
    print(f"  - GET  http://localhost:{PORT}/api/v1/items")
    print(f"  - POST http://localhost:{PORT}/api/v1/items")
    print(f"  - GET  http://localhost:{PORT}/api/v1/items/{{code}}")
    print(f"  - PUT  http://localhost:{PORT}/api/v1/items/{{code}}")
    print(f"  - DELETE http://localhost:{PORT}/api/v1/items/{{code}}")
    print(f"  - GET  http://localhost:{PORT}/api/v1/items/search?q=termo")
    print(f"  - GET  http://localhost:{PORT}/api/v1/categories")
    print(f"  - GET  http://localhost:{PORT}/api/v1/reports/dashboard")
    print("\nPara parar: Ctrl+C")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
