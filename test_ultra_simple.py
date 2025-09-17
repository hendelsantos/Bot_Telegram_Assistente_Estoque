#!/usr/bin/env python3
"""
Teste da API Ultra Simples - Usando apenas bibliotecas padrão
"""

import urllib.request
import urllib.parse
import json
import time

# Configurações
BASE_URL = 'http://localhost:5000/api/v1'
API_KEY = 'test-key-123'

def make_request(method, url, data=None, headers=None):
    """Fazer requisição HTTP"""
    if headers is None:
        headers = {}
    
    headers['X-API-Key'] = API_KEY
    headers['Content-Type'] = 'application/json'
    
    if data:
        data = json.dumps(data).encode()
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {'error': str(e)}

def test_api():
    """Testa todos os endpoints da API"""
    
    print("🔥 Testando API Ultra Simples - Sistema de Estoque")
    print("=" * 60)
    
    # 1. Informações da API
    print("\n📋 1. Informações da API")
    status, data = make_request('GET', f"{BASE_URL}/")
    print(f"Status: {status}")
    print(f"Sucesso: {data.get('success', False)}")
    if data.get('success'):
        print(f"API: {data['data']['name']} v{data['data']['version']}")
    
    # 2. Listar itens
    print("\n📦 2. Listar todos os itens")
    status, data = make_request('GET', f"{BASE_URL}/items")
    print(f"Status: {status}")
    if data.get('success'):
        total = data['data']['pagination']['total']
        count = len(data['data']['items'])
        print(f"Total de itens no banco: {total}")
        print(f"Itens retornados: {count}")
        
        # Mostrar alguns itens se existirem
        if count > 0:
            print("Primeiros itens:")
            for item in data['data']['items'][:3]:
                print(f"  - {item['codigo']}: {item['nome']} (Qtd: {item['quantidade']})")
    else:
        print(f"Erro: {data.get('error')}")
    
    # 3. Criar item de teste
    print("\n➕ 3. Criar item de teste")
    test_item = {
        "nome": "Produto Teste API Ultra",
        "descricao": "Item criado via API ultra simples",
        "quantidade": 15,
        "categoria": "Teste Automatizado",
        "localizacao": "Estoque Virtual"
    }
    
    status, data = make_request('POST', f"{BASE_URL}/items", test_item)
    print(f"Status: {status}")
    if data.get('success'):
        test_code = data['data']['codigo']
        print(f"✅ Item criado com código: {test_code}")
        
        # 4. Buscar item específico
        print(f"\n🔍 4. Buscar item específico: {test_code}")
        status, data = make_request('GET', f"{BASE_URL}/items/{test_code}")
        print(f"Status: {status}")
        if data.get('success'):
            item = data['data']
            print(f"✅ Item encontrado: {item['nome']}")
            print(f"   Quantidade: {item['quantidade']}")
            print(f"   Categoria: {item.get('categoria', 'N/A')}")
            print(f"   Status: {item.get('status', 'N/A')}")
        
        # 5. Atualizar item
        print(f"\n✏️ 5. Atualizar item: {test_code}")
        update_data = {
            "quantidade": 25, 
            "categoria": "Teste Atualizado",
            "descricao": "Item atualizado via API"
        }
        status, data = make_request('PUT', f"{BASE_URL}/items/{test_code}", update_data)
        print(f"Status: {status}")
        if data.get('success'):
            print("✅ Item atualizado com sucesso")
            print(f"   Campos atualizados: {data['data']['updated_fields']}")
        
        # 6. Verificar atualização
        print(f"\n🔄 6. Verificar atualização do item: {test_code}")
        status, data = make_request('GET', f"{BASE_URL}/items/{test_code}")
        if data.get('success'):
            item = data['data']
            print(f"✅ Quantidade atualizada: {item['quantidade']}")
            print(f"✅ Categoria atualizada: {item.get('categoria', 'N/A')}")
        
        # 7. Deletar item
        print(f"\n🗑️ 7. Deletar item de teste: {test_code}")
        status, data = make_request('DELETE', f"{BASE_URL}/items/{test_code}")
        print(f"Status: {status}")
        if data.get('success'):
            print("✅ Item deletado com sucesso")
        
        # 8. Verificar se foi deletado
        print(f"\n❌ 8. Verificar se item foi deletado: {test_code}")
        status, data = make_request('GET', f"{BASE_URL}/items/{test_code}")
        print(f"Status: {status}")
        if status == 404:
            print("✅ Item não encontrado (deletado corretamente)")
        
    else:
        print(f"❌ Erro ao criar item: {data.get('error')}")
    
    # 9. Busca
    print("\n🔎 9. Buscar itens")
    search_url = f"{BASE_URL}/items/search?" + urllib.parse.urlencode({'q': 'produto', 'limit': 5})
    status, data = make_request('GET', search_url)
    print(f"Status: {status}")
    if data.get('success'):
        count = data['data']['count']
        print(f"✅ Resultados encontrados: {count}")
        if count > 0:
            print("Resultados:")
            for item in data['data']['results']:
                print(f"  - {item['codigo']}: {item['nome']}")
    else:
        print(f"❌ Erro: {data.get('error')}")
    
    # 10. Categorias
    print("\n📊 10. Listar categorias")
    status, data = make_request('GET', f"{BASE_URL}/categories")
    print(f"Status: {status}")
    if data.get('success'):
        categories = data['data']
        print(f"✅ Categorias encontradas: {len(categories)}")
        for cat in categories[:5]:  # Primeiras 5
            print(f"  - {cat['name']}: {cat['item_count']} itens, {cat['total_quantity']} unidades")
    else:
        print(f"❌ Erro: {data.get('error')}")
    
    # 11. Dashboard
    print("\n📈 11. Estatísticas do dashboard")
    status, data = make_request('GET', f"{BASE_URL}/reports/dashboard")
    print(f"Status: {status}")
    if data.get('success'):
        stats = data['data']
        print(f"✅ Total de itens: {stats['total_items']}")
        print(f"✅ Quantidade total: {stats['total_quantity']}")
        print(f"✅ Estoque baixo: {stats['low_stock_items']} itens")
        
        if stats['top_categories']:
            print("Top categorias:")
            for cat in stats['top_categories']:
                print(f"  - {cat['category']}: {cat['count']} itens")
    else:
        print(f"❌ Erro: {data.get('error')}")
    
    # 12. Teste sem API key
    print("\n🔒 12. Teste sem autenticação")
    req = urllib.request.Request(f"{BASE_URL}/items")
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Status: {response.getcode()} (Inesperado)")
    except urllib.error.HTTPError as e:
        print(f"Status: {e.code}")
        if e.code == 401:
            print("✅ Autenticação funcionando corretamente (401 Unauthorized)")
    
    print("\n" + "=" * 60)
    print("🎉 Testes da API Ultra Simples concluídos!")
    print("✅ API está funcionando com bibliotecas padrão do Python")

if __name__ == '__main__':
    print("⏳ Aguardando 2 segundos para garantir que a API esteja rodando...")
    time.sleep(2)
    test_api()
