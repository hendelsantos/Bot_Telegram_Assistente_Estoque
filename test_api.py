#!/usr/bin/env python3
"""
Script de teste para a API REST
Demonstra como usar todos os endpoints
"""

import requests
import json
import time

# Configuração
BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "test-api-key-123"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api():
    """Testa todos os endpoints da API"""
    print("🚀 Testando API REST do Sistema de Estoque\n")
    
    # 1. Informações da API
    print("1️⃣ Testando informações da API...")
    try:
        response = requests.get(f"{BASE_URL}/", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 2. Listar itens
    print("2️⃣ Testando listagem de itens...")
    try:
        response = requests.get(f"{BASE_URL}/items?limit=5", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Total de itens: {data['data']['pagination']['total']}")
            print(f"Itens retornados: {len(data['data']['items'])}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 3. Criar novo item
    print("3️⃣ Testando criação de item...")
    novo_item = {
        "nome": "Mouse Gamer RGB",
        "descricao": "Mouse para jogos com iluminação RGB",
        "quantidade": 25,
        "categoria": "perifericos",
        "localizacao": "Estoque B2",
        "fornecedor": "Logitech",
        "preco_unitario": 150.00
    }
    
    try:
        response = requests.post(f"{BASE_URL}/items", 
                               headers=headers, 
                               json=novo_item)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            codigo_criado = data['data']['codigo']
            print(f"Item criado com código: {codigo_criado}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
        codigo_criado = "MOUS-001"  # Fallback para continuar testes
    print("\n" + "="*50 + "\n")
    
    # 4. Buscar item específico
    print("4️⃣ Testando busca de item específico...")
    try:
        response = requests.get(f"{BASE_URL}/items/{codigo_criado}", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            item = data['data']
            print(f"Item encontrado: {item['nome']} (Qtd: {item['quantidade']})")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 5. Atualizar item
    print("5️⃣ Testando atualização de item...")
    update_data = {
        "quantidade": 30,
        "preco_unitario": 140.00
    }
    
    try:
        response = requests.put(f"{BASE_URL}/items/{codigo_criado}", 
                              headers=headers, 
                              json=update_data)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Item {codigo_criado} atualizado com sucesso")
            print(f"Campos atualizados: {data['data']['updated_fields']}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 6. Buscar itens
    print("6️⃣ Testando busca de itens...")
    try:
        response = requests.get(f"{BASE_URL}/items/search?q=mouse&limit=3", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Termo buscado: {data['data']['query']}")
            print(f"Resultados encontrados: {data['data']['count']}")
            for item in data['data']['results']:
                print(f"  - {item['codigo']}: {item['nome']}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 7. Listar categorias
    print("7️⃣ Testando listagem de categorias...")
    try:
        response = requests.get(f"{BASE_URL}/categories", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print("Categorias encontradas:")
            for cat in data['data']:
                print(f"  - {cat['name']}: {cat['item_count']} itens")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 8. Dashboard stats
    print("8️⃣ Testando estatísticas do dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/reports/dashboard", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            stats = data['data']
            print(f"Total de itens: {stats['total_items']}")
            print(f"Quantidade total: {stats['total_quantity']}")
            print(f"Itens com estoque baixo: {stats['low_stock_items']}")
            print(f"Valor total: R$ {stats['total_value']:.2f}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")
    print("\n" + "="*50 + "\n")
    
    # 9. Teste de rate limiting (opcional)
    print("9️⃣ Testando rate limiting...")
    print("Fazendo múltiplas requisições...")
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/", headers=headers)
            print(f"Requisição {i+1}: Status {response.status_code}")
            time.sleep(0.1)
        except Exception as e:
            print(f"Erro na requisição {i+1}: {e}")
    print("\n" + "="*50 + "\n")
    
    print("✅ Testes concluídos!")

def test_webhook():
    """Testa configuração de webhook"""
    print("🔔 Testando webhook...")
    webhook_data = {
        "webhook_url": "https://webhook.site/unique-id",
        "threshold": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/webhooks/stock-alert", 
                               headers=headers, 
                               json=webhook_data)
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print("Webhook configurado com sucesso!")
            print(f"URL: {data['data']['webhook_url']}")
            print(f"Threshold: {data['data']['threshold']}")
        else:
            print(f"Erro: {data.get('error')}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    print("🧪 TESTE DA API REST\n")
    print("Certifique-se de que o servidor da API está rodando em localhost:5000")
    print("Para iniciar: python server/api_rest.py\n")
    
    choice = input("Executar testes? (y/n): ").lower()
    if choice == 'y':
        test_api()
        
        webhook_choice = input("\nTestar webhook também? (y/n): ").lower()
        if webhook_choice == 'y':
            test_webhook()
    else:
        print("Testes cancelados.")
