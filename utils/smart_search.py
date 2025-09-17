#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Busca Inteligente para Itens
Autor: GitHub Copilot
Data: 16/09/2025
"""

import sqlite3
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import unicodedata

class SmartSearch:
    """Sistema de busca inteligente para itens do estoque"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para busca (remove acentos, lowercase, etc.)"""
        if not text:
            return ""
        
        # Remove acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Lowercase e remove caracteres especiais
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        
        # Remove espaços extras
        text = ' '.join(text.split())
        
        return text
    
    def search_items(self, 
                    query: str, 
                    category: str = None,
                    location: str = None,
                    status: str = None,
                    limit: int = 50) -> List[Dict]:
        """
        Busca itens no banco com múltiplos critérios
        
        Args:
            query: Termo de busca (nome, código, descrição)
            category: Filtro por categoria
            location: Filtro por localização
            status: Filtro por status
            limit: Limite de resultados
        
        Returns:
            Lista de itens encontrados com score de relevância
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Base query
                sql_parts = []
                params = []
                
                # Query principal
                base_query = """
                    SELECT 
                        id, nome, descricao, quantidade, status, categoria, 
                        localizacao, codigo, codigo_barras, marca, modelo, 
                        numero_serie, data_cadastro
                    FROM itens 
                    WHERE 1=1
                """
                
                # Filtros específicos
                if category:
                    base_query += " AND LOWER(categoria) LIKE ?"
                    params.append(f"%{category.lower()}%")
                
                if location:
                    base_query += " AND LOWER(localizacao) LIKE ?"
                    params.append(f"%{location.lower()}%")
                
                if status:
                    base_query += " AND LOWER(status) LIKE ?"
                    params.append(f"%{status.lower()}%")
                
                # Busca por termo
                if query:
                    normalized_query = self.normalize_text(query)
                    terms = normalized_query.split()
                    
                    # Busca em múltiplas colunas
                    search_conditions = []
                    
                    for term in terms:
                        term_condition = """(
                            LOWER(nome) LIKE ? OR 
                            LOWER(descricao) LIKE ? OR 
                            LOWER(codigo) LIKE ? OR 
                            LOWER(codigo_barras) LIKE ? OR
                            LOWER(marca) LIKE ? OR
                            LOWER(modelo) LIKE ? OR
                            LOWER(numero_serie) LIKE ?
                        )"""
                        search_conditions.append(term_condition)
                        # Adiciona o termo para cada coluna na condição
                        for _ in range(7):  # 7 colunas na busca
                            params.append(f"%{term}%")
                    
                    if search_conditions:
                        base_query += " AND (" + " AND ".join(search_conditions) + ")"
                
                # Ordenação por relevância (itens com códigos primeiro)
                base_query += " ORDER BY (CASE WHEN codigo IS NOT NULL THEN 0 ELSE 1 END), nome"
                
                if limit:
                    base_query += f" LIMIT {limit}"
                
                # Executar busca
                cursor.execute(base_query, params)
                rows = cursor.fetchall()
                
                # Converter para lista de dicionários com score
                results = []
                for row in rows:
                    item = dict(row)
                    
                    # Calcular score de relevância
                    if query:
                        score = self._calculate_relevance_score(item, query)
                        item['relevance_score'] = score
                    else:
                        item['relevance_score'] = 0.5
                    
                    results.append(item)
                
                # Ordenar por relevância
                if query:
                    results.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                return results
                
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """Busca item por código específico (exato ou parcial)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Busca exata primeiro
                cursor.execute("""
                    SELECT * FROM itens 
                    WHERE codigo = ? OR codigo_barras = ?
                """, (code, code))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                # Busca parcial
                cursor.execute("""
                    SELECT * FROM itens 
                    WHERE codigo LIKE ? OR codigo_barras LIKE ?
                    ORDER BY codigo
                    LIMIT 10
                """, (f"%{code}%", f"%{code}%"))
                
                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
                
                return None
                
        except Exception as e:
            print(f"Erro na busca por código: {e}")
            return None
    
    def search_similar_names(self, name: str, threshold: float = 0.6) -> List[Dict]:
        """Busca itens com nomes similares (fuzzy search)"""
        try:
            # Primeiro busca todos os nomes
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM itens ORDER BY nome")
                all_items = cursor.fetchall()
                
                # Calcula similaridade
                similar_items = []
                normalized_target = self.normalize_text(name)
                
                for item in all_items:
                    item_dict = dict(item)
                    normalized_name = self.normalize_text(item_dict['nome'])
                    
                    # Calcula similaridade
                    similarity = SequenceMatcher(None, normalized_target, normalized_name).ratio()
                    
                    if similarity >= threshold:
                        item_dict['similarity_score'] = similarity
                        similar_items.append(item_dict)
                
                # Ordena por similaridade
                similar_items.sort(key=lambda x: x['similarity_score'], reverse=True)
                
                return similar_items
                
        except Exception as e:
            print(f"Erro na busca por similaridade: {e}")
            return []
    
    def search_by_category_tree(self, category: str) -> List[Dict]:
        """Busca itens organizados por árvore de categorias"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Busca hierárquica de categorias
                cursor.execute("""
                    SELECT categoria, COUNT(*) as count
                    FROM itens 
                    WHERE categoria LIKE ?
                    GROUP BY categoria
                    ORDER BY categoria
                """, (f"%{category}%",))
                
                categories = cursor.fetchall()
                
                result = []
                for cat in categories:
                    # Busca itens de cada categoria
                    cursor.execute("""
                        SELECT * FROM itens 
                        WHERE categoria = ?
                        ORDER BY nome
                    """, (cat['categoria'],))
                    
                    items = cursor.fetchall()
                    
                    result.append({
                        'category': cat['categoria'],
                        'count': cat['count'],
                        'items': [dict(item) for item in items]
                    })
                
                return result
                
        except Exception as e:
            print(f"Erro na busca por árvore de categorias: {e}")
            return []
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Retorna sugestões de busca baseadas no termo parcial"""
        try:
            if len(partial_query) < 2:
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Busca sugestões em várias colunas
                suggestions = set()
                
                # Nomes
                cursor.execute("""
                    SELECT DISTINCT nome FROM itens 
                    WHERE LOWER(nome) LIKE ? 
                    LIMIT 5
                """, (f"%{partial_query.lower()}%",))
                
                for row in cursor.fetchall():
                    suggestions.add(row[0])
                
                # Categorias
                cursor.execute("""
                    SELECT DISTINCT categoria FROM itens 
                    WHERE categoria IS NOT NULL AND LOWER(categoria) LIKE ? 
                    LIMIT 3
                """, (f"%{partial_query.lower()}%",))
                
                for row in cursor.fetchall():
                    if row[0]:
                        suggestions.add(row[0])
                
                # Marcas
                cursor.execute("""
                    SELECT DISTINCT marca FROM itens 
                    WHERE marca IS NOT NULL AND LOWER(marca) LIKE ? 
                    LIMIT 3
                """, (f"%{partial_query.lower()}%",))
                
                for row in cursor.fetchall():
                    if row[0]:
                        suggestions.add(row[0])
                
                return sorted(list(suggestions))
                
        except Exception as e:
            print(f"Erro ao obter sugestões: {e}")
            return []
    
    def _calculate_relevance_score(self, item: Dict, query: str) -> float:
        """Calcula score de relevância de um item para a query"""
        score = 0.0
        normalized_query = self.normalize_text(query).lower()
        query_terms = normalized_query.split()
        
        # Pesos por campo
        field_weights = {
            'codigo': 1.0,
            'codigo_barras': 1.0,
            'nome': 0.8,
            'marca': 0.6,
            'modelo': 0.6,
            'categoria': 0.4,
            'descricao': 0.3
        }
        
        for field, weight in field_weights.items():
            field_value = str(item.get(field, ''))
            normalized_field = self.normalize_text(field_value).lower()
            
            # Match exato
            if normalized_query in normalized_field:
                score += weight * 1.0
            
            # Match parcial por termo
            for term in query_terms:
                if term in normalized_field:
                    score += weight * 0.5
            
            # Similaridade de sequência
            if normalized_field and normalized_query:
                similarity = SequenceMatcher(None, normalized_query, normalized_field).ratio()
                if similarity > 0.3:
                    score += weight * similarity * 0.3
        
        return min(score, 1.0)  # Limita a 1.0
    
    def get_search_stats(self) -> Dict:
        """Retorna estatísticas da base de dados para busca"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total de itens
                cursor.execute("SELECT COUNT(*) FROM itens")
                stats['total_items'] = cursor.fetchone()[0]
                
                # Categorias
                cursor.execute("""
                    SELECT categoria, COUNT(*) 
                    FROM itens 
                    WHERE categoria IS NOT NULL 
                    GROUP BY categoria 
                    ORDER BY COUNT(*) DESC
                """)
                stats['categories'] = dict(cursor.fetchall())
                
                # Status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM itens 
                    GROUP BY status 
                    ORDER BY COUNT(*) DESC
                """)
                stats['status'] = dict(cursor.fetchall())
                
                # Localizações
                cursor.execute("""
                    SELECT localizacao, COUNT(*) 
                    FROM itens 
                    WHERE localizacao IS NOT NULL 
                    GROUP BY localizacao 
                    ORDER BY COUNT(*) DESC
                """)
                stats['locations'] = dict(cursor.fetchall())
                
                # Itens com códigos
                cursor.execute("SELECT COUNT(*) FROM itens WHERE codigo IS NOT NULL")
                stats['items_with_code'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM itens WHERE codigo_barras IS NOT NULL")
                stats['items_with_barcode'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}

def test_smart_search():
    """Teste do sistema de busca inteligente"""
    db_path = "/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/db/estoque.db"
    search = SmartSearch(db_path)
    
    print("🔍 TESTE DO SISTEMA DE BUSCA INTELIGENTE")
    print("=" * 60)
    
    # Estatísticas
    stats = search.get_search_stats()
    print(f"\n📊 ESTATÍSTICAS DA BASE:")
    print(f"   Total de itens: {stats.get('total_items', 0)}")
    print(f"   Itens com código: {stats.get('items_with_code', 0)}")
    print(f"   Itens com código de barras: {stats.get('items_with_barcode', 0)}")
    
    if stats.get('categories'):
        print(f"\n📂 CATEGORIAS:")
        for cat, count in list(stats['categories'].items())[:5]:
            print(f"   {cat}: {count} itens")
    
    # Testes de busca
    test_queries = [
        "notebook",
        "mouse",
        "NOTE-001",
        "dell",
        "informatica"
    ]
    
    print(f"\n🔍 TESTES DE BUSCA:")
    for query in test_queries:
        results = search.search_items(query, limit=3)
        print(f"\n   Busca: '{query}' -> {len(results)} resultados")
        
        for result in results[:2]:  # Mostra apenas 2 primeiros
            score = result.get('relevance_score', 0)
            nome = result.get('nome', 'N/A')
            codigo = result.get('codigo', 'N/A')
            print(f"     • {nome} [{codigo}] (relevância: {score:.2f})")
    
    # Teste de sugestões
    print(f"\n💡 SUGESTÕES PARA 'not':")
    suggestions = search.get_search_suggestions('not')
    for suggestion in suggestions[:5]:
        print(f"   • {suggestion}")

if __name__ == "__main__":
    test_smart_search()
