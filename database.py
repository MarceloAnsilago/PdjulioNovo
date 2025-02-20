import sqlite3
import datetime
import uuid

def criar_banco_de_dados():
    """
    Cria (ou conecta) ao BD 'usuarios.db' e garante que as tabelas existam.
    Também adiciona a coluna 'imagem_url' na tabela 'produtos' se ainda não existir.
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    # Criar tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            perm_cadastrar_produtos  INTEGER DEFAULT 0,
            perm_estornar_produtos   INTEGER DEFAULT 0,
            perm_emitir_venda        INTEGER DEFAULT 0,
            perm_financeiro          INTEGER DEFAULT 0,
            perm_gerenciar_usuarios  INTEGER DEFAULT 0
        );
    """)

    # Criar tabela de produtos (sem a coluna imagem_url ainda)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            info_complementar TEXT,
            status TEXT NOT NULL DEFAULT 'Ativo',
            preco REAL NOT NULL DEFAULT 0
        );
    """)

    # Verificar se a coluna imagem_url já existe
    cursor.execute("PRAGMA table_info(produtos);")
    colunas = [col[1] for col in cursor.fetchall()]
    
    if "imagem_url" not in colunas:
        cursor.execute("ALTER TABLE produtos ADD COLUMN imagem_url TEXT;")
        print("✅ Coluna 'imagem_url' adicionada à tabela 'produtos'.")

    # Criar tabela de movimentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_operacao TEXT,
            data TEXT NOT NULL,
            nome TEXT NOT NULL,
            custo_inicial REAL NOT NULL,
            preco_venda REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            usuario TEXT NOT NULL,
            metodo_pagamento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativo',
            total REAL NOT NULL
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Banco de dados atualizado com sucesso!")

# ----------------------------
# Funções para USUÁRIOS
# ----------------------------

def cadastrar_usuario_bd(login, senha,
                         perm_cadastrar_produtos,
                         perm_estornar_produtos,
                         perm_emitir_venda,
                         perm_financeiro,
                         perm_gerenciar_usuarios):
    """
    Insere um novo usuário na tabela 'usuarios'.
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (
                login,
                senha,
                perm_cadastrar_produtos,
                perm_estornar_produtos,
                perm_emitir_venda,
                perm_financeiro,
                perm_gerenciar_usuarios
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            login,
            senha,
            int(perm_cadastrar_produtos),
            int(perm_estornar_produtos),
            int(perm_emitir_venda),
            int(perm_financeiro),
            int(perm_gerenciar_usuarios)
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def listar_usuarios_bd():
    """
    Retorna todos os usuários (8 colunas):
      id, login, senha,
      perm_cadastrar_produtos,
      perm_estornar_produtos,
      perm_emitir_venda,
      perm_financeiro,
      perm_gerenciar_usuarios
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            login,
            senha,
            perm_cadastrar_produtos,
            perm_estornar_produtos,
            perm_emitir_venda,
            perm_financeiro,
            perm_gerenciar_usuarios
        FROM usuarios
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def buscar_usuario_bd(login, senha):
    """
    Busca usuário pelo login e senha (8 colunas).
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            login,
            senha,
            perm_cadastrar_produtos,
            perm_estornar_produtos,
            perm_emitir_venda,
            perm_financeiro,
            perm_gerenciar_usuarios
        FROM usuarios
        WHERE login = ? AND senha = ?
    """, (login, senha))
    row = cursor.fetchone()
    conn.close()
    return row

def atualizar_usuario_bd(user_id, nova_senha,
                         cad_produtos,
                         est_prod,
                         emit_venda,
                         financeiro,
                         gerenciar_usuarios):
    """
    Atualiza senha e permissões (8 colunas) do usuário.
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuarios
        SET senha = ?,
            perm_cadastrar_produtos  = ?,
            perm_estornar_produtos   = ?,
            perm_emitir_venda        = ?,
            perm_financeiro          = ?,
            perm_gerenciar_usuarios  = ?
        WHERE id = ?
    """, (
        nova_senha,
        int(cad_produtos),
        int(est_prod),
        int(emit_venda),
        int(financeiro),
        int(gerenciar_usuarios),
        user_id
    ))
    conn.commit()
    conn.close()

def excluir_usuario_bd(user_id):
    """Exclui um usuário pelo ID."""
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# ----------------------------
# Funções para PRODUTOS
# ----------------------------

def cadastrar_produto_bd(nome, info, status, preco, imagem_url):
    """Insere um produto na tabela 'produtos' com a URL da imagem."""
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO produtos (nome, info_complementar, status, preco, imagem_url)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, info, status, preco, imagem_url))
        conn.commit()
        produto_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return produto_id


def listar_produtos_bd():
    """Retorna todos os produtos cadastrados, incluindo a imagem."""
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, info_complementar, status, preco, imagem_url
        FROM produtos
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Substituir None por string vazia na coluna imagem_url para evitar erros
    produtos_corrigidos = [[p[0], p[1], p[2], p[3], p[4], p[5] if p[5] else ""] for p in rows]

    return produtos_corrigidos


def atualizar_produto_bd(produto_id, novo_nome, nova_info, novo_status, novo_preco, nova_imagem_url):
    """Atualiza os dados de um produto, incluindo a URL da imagem."""
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE produtos
        SET nome = ?,
            info_complementar = ?,
            status = ?,
            preco = ?,
            imagem_url = ?
        WHERE id = ?
    """, (novo_nome, nova_info, novo_status, novo_preco, nova_imagem_url, produto_id))
    conn.commit()
    conn.close()


def excluir_produto_bd(produto_id):
    """Exclui um produto definitivamente da tabela."""
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

# ----------------------------
# Funções para MOVIMENTOS
# ----------------------------

def criar_tabela_movimentos():
    """
    Cria (ou conecta) ao BD 'usuarios.db' e garante que a tabela 'movimentos' exista.
    Essa tabela registra as movimentações (entrada ou saída) de produtos.
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_operacao TEXT,             -- Nova coluna para a referência da operação
            data TEXT NOT NULL,
            nome TEXT NOT NULL,
            custo_inicial REAL NOT NULL,
            preco_venda REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            tipo TEXT NOT NULL,              -- 'entrada' ou 'saída'
            usuario TEXT NOT NULL,
            metodo_pagamento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativo',
            total REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def cadastrar_movimentacao(produto_nome, custo_inicial, preco_venda, quantidade,
                           tipo, usuario, metodo_pagamento, status="Ativo", num_operacao=None):
    """
    Insere uma nova movimentação na tabela 'movimentos'.
    - Se tipo="entrada", total = quantidade * custo_inicial.
    - Se tipo="venda", total = quantidade * preco_venda.
    Gera um número de operação sequencial, a menos que um seja fornecido.
    """
    # Calcular o total conforme o tipo
    if tipo.lower() == "venda":
        total = quantidade * preco_venda
    else:
        total = quantidade * custo_inicial

    data = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    
    # Se nenhum número de operação foi fornecido, gera um novo
    if num_operacao is None:
        cursor.execute("SELECT MAX(CAST(num_operacao AS INTEGER)) FROM movimentos")
        result = cursor.fetchone()[0]
        prox_num = 1 if result is None else int(result) + 1
        num_operacao = f"{prox_num:02d}"  # Formata com 2 dígitos (ex: "01", "02", ...)
    
    cursor.execute("""
        INSERT INTO movimentos (
            num_operacao, data, nome, custo_inicial, preco_venda, quantidade,
            tipo, usuario, metodo_pagamento, status, total
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (num_operacao, data, produto_nome, custo_inicial, preco_venda, quantidade,
          tipo, usuario, metodo_pagamento, status, total))
    conn.commit()
    conn.close()
    return num_operacao



def listar_movimentacoes_bd():
    """
    Retorna todas as movimentações cadastradas.
    """
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, num_operacao, data, nome, custo_inicial, preco_venda, quantidade,
               tipo, usuario, metodo_pagamento, status, total
        FROM movimentos
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def atualizar_movimentacao_venda(id_, nova_quantidade, novo_status):
    import sqlite3
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    # Obter o preço de venda para recalcular o total
    cursor.execute("SELECT preco_venda FROM movimentos WHERE id = ?", (id_,))
    preco_venda = cursor.fetchone()[0]
    novo_total = nova_quantidade * preco_venda
    cursor.execute("""
        UPDATE movimentos
        SET quantidade = ?,
            status = ?,
            total = ?
        WHERE id = ?
    """, (nova_quantidade, novo_status, novo_total, id_))
    conn.commit()
    conn.close()
