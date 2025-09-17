CREATE_MOVIMENTACOES = '''
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    usuario TEXT,
    acao TEXT NOT NULL,
    detalhes TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES itens(id)
);
'''
import aiosqlite
import asyncio

DB_PATH = 'db/estoque.db'

CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade INTEGER NOT NULL,
    catalogo TEXT,
    status TEXT NOT NULL,
    foto_path TEXT,
    foto_id TEXT,
    info_reparo TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        await db.execute(CREATE_MOVIMENTACOES)
        await db.commit()

if __name__ == '__main__':
    asyncio.run(init_db())
