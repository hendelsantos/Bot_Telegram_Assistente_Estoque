#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface de Cadastro Otimizada com Códigos Automáticos
Autor: GitHub Copilot
Data: 16/09/2025
"""

import sqlite3
import sys
import os
from typing import Dict, List, Optional
import json

# Adiciona o diretório utils ao path
sys.path.append('/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/utils')

from code_generator import CodeGenerator
from smart_search import SmartSearch

class SmartRegistration:
    """Sistema de cadastro inteligente com códigos automáticos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.code_generator = CodeGenerator(db_path)
        self.smart_search = SmartSearch(db_path)
    
    def register_item(self, 
                     nome: str,
                     categoria: str = '',
                     descricao: str = '',
                     quantidade: int = 1,
                     status: str = 'ativo',
                     localizacao: str = '',
                     marca: str = '',
                     modelo: str = '',
                     numero_serie: str = '') -> Dict:
        """
        Cadastra um novo item com códigos automáticos
        
        Returns:
            Dict com informações do item criado, incluindo códigos gerados
        """
        try:
            # Gera códigos automáticos
            codes = self.code_generator.generate_complete_item_codes(nome, categoria)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insere item
                cursor.execute("""
                    INSERT INTO itens (
                        nome, descricao, quantidade, status, categoria, 
                        localizacao, codigo, codigo_barras, marca, modelo, numero_serie
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome, descricao, quantidade, status, categoria,
                    localizacao, codes['codigo_mnemonico'], codes['codigo_barras'],
                    marca, modelo, numero_serie
                ))
                
                item_id = cursor.lastrowid
                
                # Busca item completo
                cursor.execute("SELECT * FROM itens WHERE id = ?", (item_id,))
                row = cursor.fetchone()
                
                if row:
                    # Converte para dict
                    columns = [description[0] for description in cursor.description]
                    item_data = dict(zip(columns, row))
                    
                    # Gera QR code
                    qr_code = self.code_generator.generate_qr_code(item_data)
                    
                    # Atualiza com QR code
                    cursor.execute("UPDATE itens SET qr_code = ? WHERE id = ?", (qr_code, item_id))
                    conn.commit()
                    
                    item_data['qr_code'] = qr_code
                    
                    return {
                        'success': True,
                        'item': item_data,
                        'codes': codes,
                        'message': f'Item cadastrado com sucesso! Código: {codes["codigo_mnemonico"]}'
                    }
                
                return {
                    'success': False,
                    'message': 'Erro ao recuperar item cadastrado'
                }
                
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                # Tenta gerar novos códigos
                return self._retry_with_new_codes(nome, categoria, descricao, quantidade, 
                                                status, localizacao, marca, modelo, numero_serie)
            else:
                return {
                    'success': False,
                    'message': f'Erro de integridade: {e}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao cadastrar item: {e}'
            }
    
    def register_bulk_items(self, items_list: List[Dict]) -> Dict:
        """Cadastra múltiplos itens em lote"""
        results = {
            'success': 0,
            'errors': 0,
            'items': [],
            'error_details': []
        }
        
        for item_data in items_list:
            result = self.register_item(**item_data)
            
            if result['success']:
                results['success'] += 1
                results['items'].append(result['item'])
            else:
                results['errors'] += 1
                results['error_details'].append({
                    'item': item_data.get('nome', 'N/A'),
                    'error': result['message']
                })
        
        results['message'] = f"Cadastro em lote: {results['success']} sucessos, {results['errors']} erros"
        
        return results
    
    def update_item_codes(self, item_id: int) -> Dict:
        """Atualiza códigos de um item existente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Busca item
                cursor.execute("SELECT * FROM itens WHERE id = ?", (item_id,))
                row = cursor.fetchone()
                
                if not row:
                    return {
                        'success': False,
                        'message': 'Item não encontrado'
                    }
                
                columns = [description[0] for description in cursor.description]
                item_data = dict(zip(columns, row))
                
                # Gera novos códigos
                codes = self.code_generator.generate_complete_item_codes(
                    item_data['nome'], 
                    item_data.get('categoria', '')
                )
                
                # Gera novo QR code
                item_data.update(codes)
                qr_code = self.code_generator.generate_qr_code(item_data)
                
                # Atualiza no banco
                cursor.execute("""
                    UPDATE itens 
                    SET codigo = ?, codigo_barras = ?, qr_code = ?
                    WHERE id = ?
                """, (codes['codigo_mnemonico'], codes['codigo_barras'], qr_code, item_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'item_id': item_id,
                    'codes': codes,
                    'message': f'Códigos atualizados! Novo código: {codes["codigo_mnemonico"]}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao atualizar códigos: {e}'
            }
    
    def search_and_suggest(self, query: str) -> Dict:
        """Busca itens e oferece sugestões"""
        # Busca principal
        results = self.smart_search.search_items(query, limit=10)
        
        # Sugestões
        suggestions = self.smart_search.get_search_suggestions(query)
        
        # Busca por similaridade se poucos resultados
        similar = []
        if len(results) < 3 and len(query) > 2:
            similar = self.smart_search.search_similar_names(query, threshold=0.4)
        
        return {
            'query': query,
            'results': results,
            'suggestions': suggestions,
            'similar': similar,
            'total': len(results)
        }
    
    def get_category_suggestions(self, partial: str) -> List[str]:
        """Sugestões de categorias baseadas em entrada parcial"""
        categories = [
            'informatica', 'notebook', 'desktop', 'monitor', 'impressora',
            'mouse', 'teclado', 'smartphone', 'tablet', 'camera',
            'projetor', 'servidor', 'switch', 'roteador', 'modem',
            'hd', 'ssd', 'memoria', 'processador', 'placa_mae',
            'fonte', 'gabinete', 'mobiliario', 'mesa', 'cadeira',
            'armario', 'estante', 'prateleira', 'arquivo',
            'eletronicos', 'televisao', 'radio', 'telefone', 'fax',
            'ar_condicionado', 'ventilador', 'geladeira', 'microondas',
            'cafeteira', 'bebedouro', 'outros'
        ]
        
        if not partial:
            return categories[:10]
        
        partial_lower = partial.lower()
        matches = [cat for cat in categories if partial_lower in cat]
        
        return matches[:10]
    
    def _retry_with_new_codes(self, nome, categoria, descricao, quantidade, 
                             status, localizacao, marca, modelo, numero_serie) -> Dict:
        """Tenta cadastrar novamente com novos códigos em caso de conflito"""
        try:
            # Gera código aleatório como fallback
            fallback_code = self.code_generator.generate_random_code()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO itens (
                        nome, descricao, quantidade, status, categoria, 
                        localizacao, codigo, codigo_barras, marca, modelo, numero_serie
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome, descricao, quantidade, status, categoria,
                    localizacao, fallback_code, fallback_code,
                    marca, modelo, numero_serie
                ))
                
                item_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'success': True,
                    'item_id': item_id,
                    'codes': {'codigo_mnemonico': fallback_code, 'codigo_barras': fallback_code},
                    'message': f'Item cadastrado com código alternativo: {fallback_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao tentar código alternativo: {e}'
            }

def create_sample_items():
    """Cria itens de exemplo para demonstração"""
    db_path = "/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/db/estoque.db"
    registration = SmartRegistration(db_path)
    
    sample_items = [
        {
            'nome': 'Notebook Dell Inspiron 15 3000',
            'categoria': 'notebook',
            'descricao': 'Notebook para uso geral, Intel i5, 8GB RAM, 256GB SSD',
            'quantidade': 1,
            'marca': 'Dell',
            'modelo': 'Inspiron 15 3000',
            'localizacao': 'Sala 101',
            'numero_serie': 'DL123456789'
        },
        {
            'nome': 'Mouse Logitech MX Master 3',
            'categoria': 'mouse',
            'descricao': 'Mouse wireless para produtividade',
            'quantidade': 5,
            'marca': 'Logitech',
            'modelo': 'MX Master 3',
            'localizacao': 'Almoxarifado'
        },
        {
            'nome': 'Monitor Samsung 24" Full HD',
            'categoria': 'monitor',
            'descricao': 'Monitor LED 24 polegadas 1920x1080',
            'quantidade': 3,
            'marca': 'Samsung',
            'modelo': 'F24T450FQL',
            'localizacao': 'Sala 102'
        },
        {
            'nome': 'Cadeira de Escritório Ergonômica',
            'categoria': 'mobiliario',
            'descricao': 'Cadeira com apoio lombar e regulagem de altura',
            'quantidade': 10,
            'marca': 'FlexForm',
            'modelo': 'Ergonomic Pro',
            'localizacao': 'Depósito B'
        },
        {
            'nome': 'Impressora HP LaserJet Pro',
            'categoria': 'impressora',
            'descricao': 'Impressora laser monocromática',
            'quantidade': 2,
            'marca': 'HP',
            'modelo': 'LaserJet Pro M404dn',
            'localizacao': 'Sala 103',
            'numero_serie': 'HP987654321'
        },
        {
            'nome': 'Smartphone iPhone 13',
            'categoria': 'smartphone',
            'descricao': 'Smartphone corporativo para gerência',
            'quantidade': 2,
            'marca': 'Apple',
            'modelo': 'iPhone 13',
            'localizacao': 'Cofre'
        },
        {
            'nome': 'Teclado Mecânico Corsair K95',
            'categoria': 'teclado',
            'descricao': 'Teclado mecânico RGB para desenvolvimento',
            'quantidade': 4,
            'marca': 'Corsair',
            'modelo': 'K95 RGB Platinum',
            'localizacao': 'Sala Dev'
        },
        {
            'nome': 'Projetor Epson PowerLite',
            'categoria': 'projetor',
            'descricao': 'Projetor para apresentações, 3000 lumens',
            'quantidade': 1,
            'marca': 'Epson',
            'modelo': 'PowerLite 1781W',
            'localizacao': 'Sala de Reunião'
        }
    ]
    
    print("📦 CRIANDO ITENS DE EXEMPLO")
    print("=" * 50)
    
    result = registration.register_bulk_items(sample_items)
    
    print(f"\n✅ {result['success']} itens cadastrados com sucesso!")
    
    if result['errors'] > 0:
        print(f"❌ {result['errors']} erros encontrados:")
        for error in result['error_details']:
            print(f"   • {error['item']}: {error['error']}")
    
    print(f"\n📋 ITENS CADASTRADOS:")
    for item in result['items']:
        codigo = item.get('codigo', 'N/A')
        nome = item.get('nome', 'N/A')
        categoria = item.get('categoria', 'N/A')
        print(f"   📦 [{codigo}] {nome} ({categoria})")
    
    return result

def test_search_system():
    """Testa o sistema de busca com os itens criados"""
    db_path = "/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/db/estoque.db"
    registration = SmartRegistration(db_path)
    
    print(f"\n🔍 TESTANDO SISTEMA DE BUSCA")
    print("=" * 50)
    
    test_queries = [
        "notebook",
        "dell",
        "mouse",
        "NOTE-001",
        "samsung",
        "informatica",
        "sala"
    ]
    
    for query in test_queries:
        result = registration.search_and_suggest(query)
        print(f"\n🔍 Busca: '{query}' -> {result['total']} resultados")
        
        # Mostra primeiros resultados
        for item in result['results'][:2]:
            nome = item.get('nome', 'N/A')[:40]
            codigo = item.get('codigo', 'N/A')
            score = item.get('relevance_score', 0)
            print(f"   📦 [{codigo}] {nome} (score: {score:.2f})")
        
        # Mostra sugestões
        if result['suggestions']:
            print(f"   💡 Sugestões: {', '.join(result['suggestions'][:3])}")

if __name__ == "__main__":
    print("🚀 SISTEMA DE CADASTRO INTELIGENTE")
    print("=" * 60)
    
    # Criar itens de exemplo
    create_sample_items()
    
    # Testar sistema de busca
    test_search_system()
    
    print(f"\n🎉 SISTEMA PRONTO!")
    print(f"💡 Agora você pode:")
    print(f"   • Buscar por nome, código, marca, categoria")
    print(f"   • Códigos automáticos são gerados (NOTE-001, MOUS-001, etc.)")
    print(f"   • QR codes são criados automaticamente")
    print(f"   • Sistema de busca inteligente com sugestões")
