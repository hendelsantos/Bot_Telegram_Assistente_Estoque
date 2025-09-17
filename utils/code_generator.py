#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Códigos Automáticos para Itens
Autor: GitHub Copilot
Data: 16/09/2025
"""

import re
import random
import sqlite3
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import qrcode
from io import BytesIO
import base64

class CodeGenerator:
    """Gerador de códigos automáticos para itens do estoque"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Mapeamento de categorias para prefixos
        self.category_prefixes = {
            'informatica': 'INFO',
            'notebook': 'NOTE',
            'desktop': 'DESK',
            'monitor': 'MONI',
            'impressora': 'IMPR',
            'mouse': 'MOUS',
            'teclado': 'TECL',
            'smartphone': 'SMRT',
            'tablet': 'TABL',
            'camera': 'CAME',
            'projetor': 'PROJ',
            'servidor': 'SERV',
            'switch': 'SWIT',
            'roteador': 'ROUT',
            'modem': 'MODE',
            'hd': 'HDDD',
            'ssd': 'SSDD',
            'memoria': 'MEMO',
            'processador': 'PROC',
            'placa_mae': 'PLMA',
            'fonte': 'FONT',
            'gabinete': 'GABI',
            'mobiliario': 'MOBI',
            'mesa': 'MESA',
            'cadeira': 'CADE',
            'armario': 'ARMA',
            'estante': 'ESTA',
            'prateleira': 'PRAT',
            'arquivo': 'ARQU',
            'eletronicos': 'ELET',
            'televisao': 'TELV',
            'radio': 'RADI',
            'telefone': 'TELE',
            'fax': 'FAXX',
            'ar_condicionado': 'ARCO',
            'ventilador': 'VENT',
            'geladeira': 'GELA',
            'microondas': 'MICR',
            'cafeteira': 'CAFE',
            'bebedouro': 'BEBE',
            'outros': 'OUTR'
        }
    
    def normalize_category(self, category: str) -> str:
        """Normaliza categoria para gerar prefixo"""
        if not category:
            return 'outros'
        
        # Remove acentos e caracteres especiais
        category = category.lower().strip()
        category = re.sub(r'[àáâãäå]', 'a', category)
        category = re.sub(r'[èéêë]', 'e', category)
        category = re.sub(r'[ìíîï]', 'i', category)
        category = re.sub(r'[òóôõö]', 'o', category)
        category = re.sub(r'[ùúûü]', 'u', category)
        category = re.sub(r'[ç]', 'c', category)
        category = re.sub(r'[^a-z0-9_]', '_', category)
        
        # Verifica se existe um mapeamento direto
        if category in self.category_prefixes:
            return category
        
        # Busca por palavras-chave
        for key, prefix in self.category_prefixes.items():
            if key in category or category in key:
                return key
        
        return 'outros'
    
    def get_category_prefix(self, category: str) -> str:
        """Obtém prefixo da categoria"""
        normalized = self.normalize_category(category)
        return self.category_prefixes.get(normalized, 'OUTR')
    
    def generate_mnemonic_code(self, name: str, category: str = '') -> str:
        """Gera código mnemônico baseado no nome e categoria"""
        try:
            # Prefixo da categoria
            prefix = self.get_category_prefix(category)
            
            # Próximo número sequencial para esta categoria
            next_number = self._get_next_sequential_number(prefix)
            
            # Formato: PREFIXO-NNN (ex: NOTE-001, MOUS-015)
            code = f"{prefix}-{next_number:03d}"
            
            return code
            
        except Exception as e:
            print(f"Erro ao gerar código mnemônico: {e}")
            # Fallback para código aleatório
            return self.generate_random_code()
    
    def generate_barcode(self, category: str = '') -> str:
        """Gera código de barras único (formato EAN-13 simplificado)"""
        try:
            # Prefixo baseado na categoria (2 dígitos)
            prefix = self._get_category_numeric_prefix(category)
            
            # Timestamp (6 dígitos - HHMMSS)
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Sequencial do dia (3 dígitos)
            sequential = self._get_daily_sequential()
            
            # Dígito verificador (1 dígito)
            partial_code = f"{prefix}{timestamp}{sequential}"
            check_digit = self._calculate_check_digit(partial_code)
            
            # Código final (12 dígitos + 1 verificador = 13 total)
            barcode = f"{partial_code}{check_digit}"
            
            return barcode
            
        except Exception as e:
            print(f"Erro ao gerar código de barras: {e}")
            return self.generate_random_code()
    
    def generate_qr_code(self, item_data: Dict) -> str:
        """Gera QR code com informações do item"""
        try:
            # Dados para o QR code
            qr_data = {
                'id': item_data.get('id', ''),
                'codigo': item_data.get('codigo', ''),
                'nome': item_data.get('nome', ''),
                'categoria': item_data.get('categoria', ''),
                'localizacao': item_data.get('localizacao', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            # Formato compacto para QR code
            qr_text = f"ITEM:{qr_data['id']}|{qr_data['codigo']}|{qr_data['nome'][:30]}|{qr_data['categoria']}"
            
            # Gera QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_text)
            qr.make(fit=True)
            
            # Converte para imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converte para base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            print(f"Erro ao gerar QR code: {e}")
            return ""
    
    def generate_random_code(self) -> str:
        """Gera código aleatório como fallback"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(100, 999)
        return f"ITEM-{timestamp}-{random_suffix}"
    
    def _get_category_numeric_prefix(self, category: str) -> str:
        """Converte categoria para prefixo numérico (2 dígitos)"""
        category_map = {
            'informatica': '10',
            'notebook': '11',
            'desktop': '12',
            'monitor': '13',
            'impressora': '14',
            'mouse': '15',
            'teclado': '16',
            'smartphone': '20',
            'tablet': '21',
            'camera': '22',
            'mobiliario': '30',
            'mesa': '31',
            'cadeira': '32',
            'armario': '33',
            'eletronicos': '40',
            'televisao': '41',
            'radio': '42',
            'outros': '99'
        }
        
        normalized = self.normalize_category(category)
        return category_map.get(normalized, '99')
    
    def _get_next_sequential_number(self, prefix: str) -> int:
        """Obtém próximo número sequencial para o prefixo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Busca o maior número usado para este prefixo
                cursor.execute("""
                    SELECT codigo FROM itens 
                    WHERE codigo LIKE ? 
                    ORDER BY codigo DESC 
                    LIMIT 1
                """, (f"{prefix}-%",))
                
                result = cursor.fetchone()
                if result:
                    # Extrai o número do código (ex: NOTE-015 -> 15)
                    last_code = result[0]
                    match = re.search(r'-(\d+)$', last_code)
                    if match:
                        return int(match.group(1)) + 1
                
                return 1  # Primeiro item desta categoria
                
        except Exception as e:
            print(f"Erro ao obter número sequencial: {e}")
            return random.randint(1, 999)
    
    def _get_daily_sequential(self) -> str:
        """Obtém sequencial do dia (3 dígitos)"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Conta itens criados hoje
                cursor.execute("""
                    SELECT COUNT(*) FROM itens 
                    WHERE DATE(data_cadastro) = ?
                """, (today,))
                
                count = cursor.fetchone()[0]
                return f"{count + 1:03d}"
                
        except Exception as e:
            print(f"Erro ao obter sequencial diário: {e}")
            return f"{random.randint(1, 999):03d}"
    
    def _calculate_check_digit(self, code: str) -> str:
        """Calcula dígito verificador para código de barras"""
        try:
            # Algoritmo simples de verificação
            total = 0
            for i, digit in enumerate(code):
                weight = 3 if i % 2 == 1 else 1
                total += int(digit) * weight
            
            check = (10 - (total % 10)) % 10
            return str(check)
            
        except Exception as e:
            print(f"Erro ao calcular dígito verificador: {e}")
            return "0"
    
    def validate_code_uniqueness(self, code: str) -> bool:
        """Valida se o código é único no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM itens WHERE codigo = ?", (code,))
                count = cursor.fetchone()[0]
                return count == 0
                
        except Exception as e:
            print(f"Erro ao validar unicidade: {e}")
            return False
    
    def generate_complete_item_codes(self, name: str, category: str = '') -> Dict[str, str]:
        """Gera todos os códigos para um item"""
        try:
            # Gera códigos únicos
            attempts = 0
            max_attempts = 10
            
            while attempts < max_attempts:
                mnemonic = self.generate_mnemonic_code(name, category)
                barcode = self.generate_barcode(category)
                
                # Verifica unicidade
                if (self.validate_code_uniqueness(mnemonic) and 
                    self.validate_code_uniqueness(barcode)):
                    
                    return {
                        'codigo_mnemonico': mnemonic,
                        'codigo_barras': barcode,
                        'categoria_normalizada': self.normalize_category(category)
                    }
                
                attempts += 1
            
            # Fallback com código aleatório único
            random_code = self.generate_random_code()
            return {
                'codigo_mnemonico': random_code,
                'codigo_barras': random_code,
                'categoria_normalizada': 'outros'
            }
            
        except Exception as e:
            print(f"Erro ao gerar códigos completos: {e}")
            # Fallback mínimo
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            fallback_code = f"ITEM-{timestamp}"
            
            return {
                'codigo_mnemonico': fallback_code,
                'codigo_barras': fallback_code,
                'categoria_normalizada': 'outros'
            }

def test_code_generator():
    """Teste do gerador de códigos"""
    db_path = "/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/db/estoque.db"
    generator = CodeGenerator(db_path)
    
    # Testes
    test_items = [
        {'nome': 'Notebook Dell Inspiron', 'categoria': 'notebook'},
        {'nome': 'Mouse Logitech', 'categoria': 'mouse'},
        {'nome': 'Cadeira de Escritório', 'categoria': 'mobiliario'},
        {'nome': 'Monitor Samsung 24', 'categoria': 'monitor'},
        {'nome': 'Item Genérico', 'categoria': ''}
    ]
    
    print("🧪 TESTE DO GERADOR DE CÓDIGOS")
    print("=" * 50)
    
    for item in test_items:
        codes = generator.generate_complete_item_codes(item['nome'], item['categoria'])
        print(f"\n📦 {item['nome']}")
        print(f"   Categoria: {item['categoria']} -> {codes['categoria_normalizada']}")
        print(f"   Código Mnemônico: {codes['codigo_mnemonico']}")
        print(f"   Código de Barras: {codes['codigo_barras']}")

if __name__ == "__main__":
    test_code_generator()
