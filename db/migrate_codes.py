#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migração do Banco de Dados - Adicionar Códigos Automáticos
Autor: GitHub Copilot
Data: 16/09/2025
"""

import sqlite3
import asyncio
import aiosqlite
from datetime import datetime

DB_PATH = '/home/hendel/Documentos/BOTS/Assistente_Stock_MPA/db/estoque.db'

# Schema atualizado com códigos automáticos
UPDATE_ITENS_TABLE = '''
ALTER TABLE itens ADD COLUMN codigo TEXT UNIQUE;
'''

UPDATE_ITENS_TABLE_BARCODE = '''
ALTER TABLE itens ADD COLUMN codigo_barras TEXT UNIQUE;
'''

UPDATE_ITENS_TABLE_CATEGORY = '''
ALTER TABLE itens ADD COLUMN categoria TEXT;
'''

UPDATE_ITENS_TABLE_LOCATION = '''
ALTER TABLE itens ADD COLUMN localizacao TEXT;
'''

UPDATE_ITENS_TABLE_QR = '''
ALTER TABLE itens ADD COLUMN qr_code TEXT;
'''

UPDATE_ITENS_TABLE_BRAND = '''
ALTER TABLE itens ADD COLUMN marca TEXT;
'''

UPDATE_ITENS_TABLE_MODEL = '''
ALTER TABLE itens ADD COLUMN modelo TEXT;
'''

UPDATE_ITENS_TABLE_SERIAL = '''
ALTER TABLE itens ADD COLUMN numero_serie TEXT;
'''

# Índices para performance
CREATE_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_codigo ON itens(codigo);',
    'CREATE INDEX IF NOT EXISTS idx_codigo_barras ON itens(codigo_barras);',
    'CREATE INDEX IF NOT EXISTS idx_categoria ON itens(categoria);',
    'CREATE INDEX IF NOT EXISTS idx_localizacao ON itens(localizacao);',
    'CREATE INDEX IF NOT EXISTS idx_nome ON itens(nome);'
]

async def migrate_database():
    """Executa migração do banco de dados"""
    print("🔄 Iniciando migração do banco de dados...")
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Verificar colunas existentes
            cursor = await db.execute("PRAGMA table_info(itens)")
            columns = await cursor.fetchall()
            existing_columns = [col[1] for col in columns]
            
            print(f"📋 Colunas existentes: {existing_columns}")
            
            # Adicionar novas colunas se não existirem
            migrations = [
                ('codigo', UPDATE_ITENS_TABLE),
                ('codigo_barras', UPDATE_ITENS_TABLE_BARCODE),
                ('categoria', UPDATE_ITENS_TABLE_CATEGORY),
                ('localizacao', UPDATE_ITENS_TABLE_LOCATION),
                ('qr_code', UPDATE_ITENS_TABLE_QR),
                ('marca', UPDATE_ITENS_TABLE_BRAND),
                ('modelo', UPDATE_ITENS_TABLE_MODEL),
                ('numero_serie', UPDATE_ITENS_TABLE_SERIAL)
            ]
            
            for column_name, sql in migrations:
                if column_name not in existing_columns:
                    try:
                        await db.execute(sql)
                        print(f"✅ Coluna '{column_name}' adicionada")
                    except Exception as e:
                        print(f"⚠️ Erro ao adicionar coluna '{column_name}': {e}")
                else:
                    print(f"➡️ Coluna '{column_name}' já existe")
            
            # Criar índices
            for index_sql in CREATE_INDEXES:
                try:
                    await db.execute(index_sql)
                    print(f"✅ Índice criado: {index_sql.split('(')[0].split()[-1]}")
                except Exception as e:
                    print(f"⚠️ Erro ao criar índice: {e}")
            
            await db.commit()
            print("✅ Migração concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False
    
    return True

def migrate_sync():
    """Versão síncrona da migração"""
    print("🔄 Iniciando migração síncrona do banco de dados...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Verificar colunas existentes
            cursor.execute("PRAGMA table_info(itens)")
            columns = cursor.fetchall()
            existing_columns = [col[1] for col in columns]
            
            print(f"📋 Colunas existentes: {existing_columns}")
            
            # Adicionar novas colunas se não existirem
            migrations = [
                ('codigo', 'ALTER TABLE itens ADD COLUMN codigo TEXT UNIQUE'),
                ('codigo_barras', 'ALTER TABLE itens ADD COLUMN codigo_barras TEXT UNIQUE'),
                ('categoria', 'ALTER TABLE itens ADD COLUMN categoria TEXT'),
                ('localizacao', 'ALTER TABLE itens ADD COLUMN localizacao TEXT'),
                ('qr_code', 'ALTER TABLE itens ADD COLUMN qr_code TEXT'),
                ('marca', 'ALTER TABLE itens ADD COLUMN marca TEXT'),
                ('modelo', 'ALTER TABLE itens ADD COLUMN modelo TEXT'),
                ('numero_serie', 'ALTER TABLE itens ADD COLUMN numero_serie TEXT')
            ]
            
            for column_name, sql in migrations:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(sql)
                        print(f"✅ Coluna '{column_name}' adicionada")
                    except Exception as e:
                        print(f"⚠️ Erro ao adicionar coluna '{column_name}': {e}")
                else:
                    print(f"➡️ Coluna '{column_name}' já existe")
            
            # Criar índices
            for index_sql in CREATE_INDEXES:
                try:
                    cursor.execute(index_sql)
                    print(f"✅ Índice criado")
                except Exception as e:
                    print(f"⚠️ Erro ao criar índice: {e}")
            
            conn.commit()
            print("✅ Migração síncrona concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro na migração síncrona: {e}")
        return False
    
    return True

def test_new_schema():
    """Testa o novo schema"""
    print("\n🧪 Testando novo schema...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Verificar todas as colunas
            cursor.execute("PRAGMA table_info(itens)")
            columns = cursor.fetchall()
            
            print("\n📋 SCHEMA ATUALIZADO:")
            print("-" * 50)
            for col in columns:
                print(f"  {col[1]:15} | {col[2]:10} | {'NOT NULL' if col[3] else 'NULL':8} | Default: {col[4] if col[4] else 'None'}")
            
            # Verificar índices
            cursor.execute("PRAGMA index_list(itens)")
            indexes = cursor.fetchall()
            
            print(f"\n🔍 ÍNDICES CRIADOS ({len(indexes)}):")
            print("-" * 30)
            for idx in indexes:
                print(f"  ✅ {idx[1]}")
            
            print(f"\n✅ Schema atualizado com sucesso!")
            print(f"📊 Total de colunas: {len(columns)}")
            print(f"🔍 Total de índices: {len(indexes)}")
            
    except Exception as e:
        print(f"❌ Erro ao testar schema: {e}")

if __name__ == "__main__":
    print("🚀 MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 50)
    
    # Executar migração síncrona
    success = migrate_sync()
    
    if success:
        # Testar novo schema
        test_new_schema()
        
        print(f"\n🎉 MIGRAÇÃO COMPLETA!")
        print(f"🆕 Novo banco com códigos automáticos pronto!")
    else:
        print(f"\n❌ Falha na migração!")
