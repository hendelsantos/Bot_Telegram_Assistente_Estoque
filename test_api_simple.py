#!/usr/bin/env python3
"""
Teste da API REST - Versão Simplificada
"""

import requests
import json
import time

# Configurações
BASE_URL = 'http://localhost:5000/api/v1'
API_KEY = 'test-key-123'  # Para desenvolvimento
HEADERS = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def test_api():
    """Testa todos os endpoints da API"""
    
    print("🔥 Testando API REST do Sistema de Estoque")
    print("=" * 50)
    
    # 1. Informações da API
    print("\n📋 1. Informações da API")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 2. Listar itens
    print("\n📦 2. Listar todos os itens")
    try:
        response = requests.get(f"{BASE_URL}/items", headers=HEADERS)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Total de itens: {data['data']['pagination']['total']}")
            print(f"Primeiros itens: {len(data['data']['items'])}")
        else:
            print(f"Erro: {data}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 3. Criar item de teste
    print("\n➕ 3. Criar item de teste")
    test_item = {
        "nome": "Produto Teste API",
        "descricao": "Item criado via API REST",
        "quantidade": 10,
        "categoria": "Teste",
        "localizacao": "Estoque A",
        "fornecedor": "Fornecedor Teste",
        "preco_unitario": 25.50
    }
    
    try:
        response = requests.post(f"{BASE_URL}/items", 
                               headers=HEADERS, 
                               json=test_item)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            test_code = data['data']['codigo']
            print(f"Item criado com código: {test_code}")
            
            # 4. Buscar item específico
            print("\n🔍 4. Buscar item específico")
            response = requests.get(f"{BASE_URL}/items/{test_code}", headers=HEADERS)
            print(f"Status: {response.status_code}")
            if response.json().get('success'):
                print(f"Item encontrado: {response.json()['data']['nome']}")
            
            # 5. Atualizar item
            print("\n✏️ 5. Atualizar item")
            update_data = {"quantidade": 15, "preco_unitario": 30.00}
            response = requests.put(f"{BASE_URL}/items/{test_code}", 
                                  headers=HEADERS, 
                                  json=update_data)
            print(f"Status: {response.status_code}")
            if response.json().get('success'):
                print("Item atualizado com sucesso")
            
            # 6. Deletar item
            print("\n🗑️ 6. Deletar item de teste")
            response = requests.delete(f"{BASE_URL}/items/{test_code}", headers=HEADERS)
            print(f"Status: {response.status_code}")
            if response.json().get('success'):
                print("Item deletado com sucesso")
        else:
            print(f"Erro ao criar item: {data}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 7. Busca
    print("\n🔎 7. Buscar itens")
    try:
        response = requests.get(f"{BASE_URL}/items/search?q=produto&limit=5", 
                              headers=HEADERS)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Resultados encontrados: {data['data']['count']}")
        else:
            print(f"Erro: {data}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 8. Categorias
    print("\n📊 8. Listar categorias")
    try:
        response = requests.get(f"{BASE_URL}/categories", headers=HEADERS)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Categorias encontradas: {len(data['data'])}")
            for cat in data['data'][:3]:  # Primeiras 3
                print(f"  - {cat['name']}: {cat['item_count']} itens")
        else:
            print(f"Erro: {data}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 9. Dashboard
    print("\n📈 9. Estatísticas do dashboard")
    try:
        response = requests.get(f"{BASE_URL}/reports/dashboard", headers=HEADERS)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            stats = data['data']
            print(f"Total de itens: {stats['total_items']}")
            print(f"Quantidade total: {stats['total_quantity']}")
            print(f"Valor total: R$ {stats['total_value']:.2f}")
            print(f"Estoque baixo: {stats['low_stock_items']} itens")
        else:
            print(f"Erro: {data}")
    except Exception as e:
        print(f"Erro: {e}")
    
    # 10. Teste sem API key
    print("\n🔒 10. Teste sem autenticação")
    try:
        response = requests.get(f"{BASE_URL}/items")
        print(f"Status: {response.status_code}")
        print("Deve retornar erro 401 (Unauthorized)")
    except Exception as e:
        print(f"Erro: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testes da API concluídos!")

if __name__ == '__main__':
    test_api()
