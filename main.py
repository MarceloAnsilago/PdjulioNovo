import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu  # Biblioteca para menu estilizado
import os
import base64
import requests
import altair as alt
import streamlit as st
import pandas as pd



from database import (
    criar_banco_de_dados,
    buscar_usuario_bd,
    cadastrar_usuario_bd,
    listar_usuarios_bd,
    excluir_usuario_bd,
    atualizar_usuario_bd,
    cadastrar_produto_bd,
    listar_produtos_bd,
    atualizar_produto_bd,
    cadastrar_movimentacao,
    listar_movimentacoes_bd,
    atualizar_movimentacao_venda,
)
################################################
#  IMAGENS
################################################
  

# Configuração do GitHub
GITHUB_USER = "MarceloAnsilago"
GITHUB_REPO = "PDJulio"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # O token deve estar salvo como variável de ambiente

# URL base da API do GitHub para upload
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/images/"

def upload_imagem_git(imagem_bytes, nome_arquivo):
    """Envia uma imagem para o GitHub e retorna o URL público"""
    try:
        img_base64 = base64.b64encode(imagem_bytes).decode()
        upload_url = GITHUB_API_URL + nome_arquivo
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}

        # 🛑 Passo 1: Verificar se a imagem já existe para obter o SHA
        response = requests.get(upload_url, headers=headers)
        sha = None
        if response.status_code == 200:  # Arquivo já existe
            sha = response.json().get("sha")  # Captura o SHA para atualização

        # 🟢 Passo 2: Criar payload (com SHA se existir)
        payload = {
            "message": f"Upload da imagem {nome_arquivo}",
            "content": img_base64,
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha  # Adiciona o SHA se o arquivo já existir

        # 🟢 Passo 3: Fazer upload da imagem
        response = requests.put(upload_url, json=payload, headers=headers)

        if response.status_code in [200, 201]:  # 200 = atualizado, 201 = novo arquivo
            return f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{nome_arquivo}"
        else:
            print(f"❌ Erro ao enviar imagem: {response.json()}")
            return None

    except Exception as e:
        print(f"❌ Erro no upload da imagem: {e}")
        return None







################################################
#  PÁGINAS
################################################

def pagina_cadastrar_produtos():
    st.title("Gerenciar Produtos")

    # Criar as abas
    tab1, tab2 = st.tabs(["Cadastrar/Editar Produtos", "Entrada de Produtos"])

    ################################################
    # Aba 1: Cadastrar/Editar Produtos
    ################################################
    with tab1:
        st.subheader("Cadastrar Novo Produto")

        with st.form("cadastro_novo_produto"):
            nome = st.text_input("Nome do Produto")
            preco = st.number_input("Preço de Venda", min_value=0.0, format="%.2f")
            info = st.text_area("Informações Complementares")
            status = st.selectbox("Status", ["Ativo", "Inativo"])
            imagem = st.file_uploader("Imagem do Produto", type=["jpg", "png", "jpeg"])

            cadastrado = st.form_submit_button("Cadastrar")
        
        if cadastrado:
            imagem_url = None
            if imagem:
                imagem_bytes = imagem.read()
                nome_arquivo = f"{nome.replace(' ', '_')}.jpg"
                imagem_url = upload_imagem_git(imagem_bytes, nome_arquivo)

            produto_id = cadastrar_produto_bd(nome, info, status, preco, imagem_url)
            if produto_id:
                st.success(f"Produto '{nome}' cadastrado com sucesso! (ID={produto_id})")
                st.session_state["produto_cadastrado"] = True  # Sinaliza que um novo produto foi adicionado
                st.rerun()

        st.write("---")
        st.subheader("Lista de Produtos Cadastrados")

        # Buscar produtos no banco de dados apenas se necessário
        if "produtos_cache" not in st.session_state or st.session_state.get("produto_cadastrado", False):
            st.session_state.produtos_cache = listar_produtos_bd()
            st.session_state["produto_cadastrado"] = False  # Resetar flag

        produtos = st.session_state.produtos_cache

        # Verifica se há produtos
        if not produtos:
            st.info("Nenhum produto cadastrado ainda.")
            return

        # Criar DataFrame
        df = pd.DataFrame(produtos, columns=["ID", "Nome", "Info", "Status", "Preço", "Imagem"])
        st.dataframe(df.drop(columns=["Imagem"]), use_container_width=True)

        # Seletor para editar
        opcoes = [f"{p[0]} - {p[1]}" for p in produtos]
        escolha = st.selectbox("Selecione um produto para editar:", opcoes)

        if escolha:
            produto_id = int(escolha.split(" - ")[0])
            produto_info = next((p for p in produtos if p[0] == produto_id), None)

            if produto_info:
                pid, pnome, pinfo, pstatus, ppreco, pimagem = produto_info

                with st.form("editar_produto"):
                    novo_nome = st.text_input("Nome do Produto", value=pnome)
                    novo_preco = st.number_input("Preço de Venda", value=ppreco, min_value=0.0, format="%.2f")
                    nova_info = st.text_area("Informações Complementares", value=pinfo)
                    novo_status = st.selectbox(
                        "Status",
                        ["Ativo", "Inativo"],
                        index=0 if pstatus == "Ativo" else 1
                    )
                    nova_imagem = st.file_uploader("Nova Imagem do Produto (opcional)", type=["jpg", "png", "jpeg"])

                    alterado = st.form_submit_button("Alterar")

                if alterado:
                    nova_imagem_url = pimagem
                    if nova_imagem:
                        imagem_bytes = nova_imagem.read()
                        nome_arquivo = f"{novo_nome.replace(' ', '_')}.jpg"
                        nova_imagem_url = upload_imagem_git(imagem_bytes, nome_arquivo)

                    atualizar_produto_bd(pid, novo_nome, nova_info, novo_status, novo_preco, nova_imagem_url)
                    st.success(f"Produto '{novo_nome}' atualizado com sucesso!")
                    st.session_state["produto_editado"] = True
                    st.rerun()


    ################################################
    # Aba 2: Entrada de Produtos
    ################################################
    with tab2:
        def pagina_entrada_produtos():
            st.title("Entrada de Produtos")

            # Filtra os produtos ativos
            produtos_todos = listar_produtos_bd()
            produtos_ativos = [p for p in produtos_todos if p[3] == "Ativo"]  # p[3] => status

            if produtos_ativos:
                df = pd.DataFrame(produtos_ativos, columns=["ID", "Nome", "Info", "Status", "Preço","Imagem"])
                st.dataframe(df, use_container_width=True)

                # Combobox para selecionar produto
                opcoes = [f"{p[0]} - {p[1]}" for p in produtos_ativos]
                escolha = st.selectbox("Selecione um produto para entrada:", opcoes)

                if escolha:
                    produto_id = int(escolha.split(" - ")[0])
                    produto_info = next((p for p in produtos_ativos if p[0] == produto_id), None)
                    if produto_info:
                        st.write(f"Produto selecionado: {escolha}")
                        # p => (id, nome, info, status, preco)
                        # Vamos buscar as movimentações para calcular o saldo
                        movimentos = listar_movimentacoes_bd()

                        # Calcular entradas
                        entradas = sum(
                            m[6] for m in movimentos
                            if m[3] == produto_info[1]  # m[3] => nome do produto
                               and m[7].lower() == "entrada"
                               and m[10].lower() == "ativo"
                        )
                        # Calcular saídas
                        saidas = sum(
                            m[6] for m in movimentos
                            if m[3] == produto_info[1]
                               and m[7].lower() in ("saída", "saida", "venda")
                               and m[10].lower() == "ativo"
                        )
                        saldo_atual = entradas - saidas

                        with st.form("form_entrada_produto"):
                            # Campos
                            quantidade_nova = st.number_input("Quantidade a Registrar", min_value=1, step=1)
                            custo_inicial = st.number_input("Custo Inicial (por unidade)", min_value=0.0, format="%.2f")
                            preco_venda = st.number_input(
                                "Preço de Venda (por unidade)",
                                min_value=0.0,
                                value=produto_info[4],
                                disabled=True,
                                format="%.2f"
                            )
                            st.number_input("Saldo Atual", value=float(saldo_atual), disabled=True, format="%.0f")
                            metodo_pagamento = st.selectbox("Método de Pagamento", ["Dinheiro", "Cartão", "Cheque", "Outro"])

                            if st.form_submit_button("Registrar Entrada"):
                                usuario = st.session_state.get("usuario_logado", "Desconhecido")
                                try:
                                    operacao = cadastrar_movimentacao(
                                        produto_nome=produto_info[1],
                                        custo_inicial=custo_inicial,
                                        preco_venda=produto_info[4],
                                        quantidade=quantidade_nova,
                                        tipo="entrada",
                                        usuario=usuario,
                                        metodo_pagamento=metodo_pagamento,
                                        status="Ativo"
                                    )
                                    st.success("Operação registrada com sucesso!")
                                    st.info(f"Número da operação: {operacao}")
                                except Exception as e:
                                    st.error(f"Erro ao registrar a operação: {e}")
                                st.rerun()
            else:
                st.info("Nenhum produto ativo cadastrado ainda.")

            st.write("---")
            st.subheader("Relatório de Entradas Ativas")

            movimentos = listar_movimentacoes_bd()
            # Filtra movimentações de entrada com status "Ativo"
            # m[7] => tipo, m[10] => status
            entradas_ativas = [
                m for m in movimentos
                if m[7].lower() == "entrada" and m[10].lower() == "ativo"
            ]
            if entradas_ativas:
                # Lembrando que agora temos 12 colunas:
                # 0:id,1:num_operacao,2:data,3:nome,4:custo_inicial,5:preco_venda,
                # 6:quantidade,7:tipo,8:usuario,9:metodo_pagamento,10:status,11:total
                colunas = [
                    "ID","Operação", "Data", "Produto",
                    "Custo Inicial", "Preço de Venda", "Quantidade",
                    "Tipo", "Usuário", "Método Pagamento",
                    "Status", "Total"
                ]
                df_entradas = pd.DataFrame(entradas_ativas, columns=colunas)
                st.dataframe(df_entradas, use_container_width=True)
            else:
                st.info("Nenhuma movimentação de entrada ativa encontrada.")

        # Chama a função
        pagina_entrada_produtos()

def pagina_emitir_venda():
    st.title("🛒 PDV - Emitir Venda")

    # CSS para forçar duas colunas fixas (mesmo em mobile)
    st.markdown(
        """
        <style>
        /* Força que cada item do grid tenha 50% da largura */
        div[data-baseweb="grid"] > div {
            flex: 0 0 50% !important;
            max-width: 50% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = {}

    num_colunas = 2
    colunas = st.columns(num_colunas)

    def calcular_saldo(produto_nome, movimentos):
        entradas = sum(
            m[6] for m in movimentos
            if m[3] == produto_nome and m[7].lower() == "entrada" and m[10].lower() == "ativo"
        )
        saidas = sum(
            m[6] for m in movimentos
            if m[3] == produto_nome and m[7].lower() in ("venda", "saída", "saida") and m[10].lower() == "ativo"
        )
        return entradas - saidas

    produtos_db = listar_produtos_bd()
    produtos_ativos = [p for p in produtos_db if p[3] == "Ativo"]
    movimentos = listar_movimentacoes_bd()

    for i, p in enumerate(produtos_ativos):
        coluna = colunas[i % num_colunas]
        with coluna:
            pid, nome, info, status, preco, imagem_url = p
            saldo = calcular_saldo(nome, movimentos)

            # Exibir imagem
            if imagem_url:
                image_html = f"""
                <div style="width:150px; height:150px; overflow:hidden; border-radius:8px; border:1px solid #ccc;">
                  <img src="{imagem_url}" style="width:100%; height:100%; object-fit:cover;" />
                </div>
                """
                st.markdown(image_html, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="width:150px; height:150px; background-color:#f0f0f0; border-radius:8px;
                display:flex; align-items:center; justify-content:center; color:#aaa; font-size:14px;">
                  Sem imagem
                </div>
                """, unsafe_allow_html=True)

            # Nome e estoque disponível
            st.markdown(f"**{nome}** ({saldo} disponíveis)")

            # Preço e quantidade (empilhados)
            st.markdown(f"**R$ {preco:.2f}**")
            if saldo > 0:
                qtd_selecionada = st.number_input(
                    label="Qtd",
                    min_value=1,
                    max_value=saldo,
                    value=1,
                    step=1,
                    key=f"qtd_{i}"
                )
                qtd_selecionada = int(qtd_selecionada)
            else:
                st.warning("Estoque esgotado!")
                qtd_selecionada = st.number_input(
                    label="Qtd",
                    min_value=0,
                    max_value=0,
                    value=0,
                    step=1,
                    key=f"qtd_{i}",
                    disabled=True
                )
                qtd_selecionada = int(qtd_selecionada)

            # Botão de adicionar ao carrinho
            msg_container = st.empty()
            if st.button(f"🛍️ Adicionar {nome}", key=f"add_{i}"):
                if qtd_selecionada > saldo:
                    msg_container.error("Quantidade indisponível no estoque!")
                else:
                    if nome in st.session_state.carrinho:
                        st.session_state.carrinho[nome]["quantidade"] += qtd_selecionada
                    else:
                        st.session_state.carrinho[nome] = {"preco": preco, "quantidade": qtd_selecionada}
                    msg_container.success(f"{qtd_selecionada}x {nome} adicionado ao carrinho!")
            st.markdown("---")

    # ======================
    # CARRINHO DE COMPRAS
    # ======================
    st.markdown("## 🛒 Carrinho")
    if st.session_state.carrinho:
        total = 0
        itens_remover = []
        for nome, item in st.session_state.carrinho.items():
            subtotal = item["preco"] * item["quantidade"]
            total += subtotal
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px;
                    margin-bottom: 8px; border: 1px solid #dee2e6;'>
                        <strong>{item['quantidade']}x {nome}</strong><br>
                        <span style='color: #6c757d;'>Preço unitário: R$ {item['preco']:.2f}</span><br>
                        <strong>Total: R$ {subtotal:.2f}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button(f"❌", key=f"remove_{nome}"):
                        itens_remover.append(nome)
        for item in itens_remover:
            del st.session_state.carrinho[item]
            st.warning(f"{item} removido do carrinho.")
            st.rerun()

        st.markdown(f"""
        <div style='background-color: #fffbeb; padding: 10px; border-radius: 8px;
        margin-top: 12px; border: 1px solid #ffd700; text-align: center;'>
            <h4>💳 Total: R$ {total:.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🏦 Escolha o método de pagamento:")
        metodo_pagamento = st.radio("Selecione uma opção:", ["Dinheiro", "Pix", "Cartão", "Outro"])
        if metodo_pagamento == "Outro":
            metodo_personalizado = st.text_input("Digite o método de pagamento:")

        op_num = None
        if st.button("Finalizar Venda"):
            usuario = st.session_state.get("usuario_logado", "Desconhecido")
            for nome, item in st.session_state.carrinho.items():
                quantidade = item["quantidade"]
                preco_unit = item["preco"]
                if op_num is None:
                    op_num = cadastrar_movimentacao(
                        produto_nome=nome,
                        custo_inicial=0,
                        preco_venda=preco_unit,
                        quantidade=quantidade,
                        tipo="venda",
                        usuario=usuario,
                        metodo_pagamento=metodo_pagamento,
                        status="Ativo",
                        num_operacao=None
                    )
                else:
                    cadastrar_movimentacao(
                        produto_nome=nome,
                        custo_inicial=0,
                        preco_venda=preco_unit,
                        quantidade=quantidade,
                        tipo="venda",
                        usuario=usuario,
                        metodo_pagamento=metodo_pagamento,
                        status="Ativo",
                        num_operacao=op_num
                    )
            st.success("Venda finalizada com sucesso!")
            st.info(f"Número da operação: {op_num}")
            st.session_state.carrinho = {}
            st.rerun()

        if st.button("🧹 Limpar Carrinho"):
            st.session_state.carrinho = {}
            st.success("Carrinho limpo!")
            st.rerun()
    else:
        st.markdown(
            "<div style='text-align: center; color: #6c757d; font-size: 18px;'>"
            "🛒 Seu carrinho está vazio.</div>",
            unsafe_allow_html=True,
        )





def pagina_gerenciar_vendas():
    st.title("Gerenciar Vendas")
    
    st.subheader("Relatório de Vendas")
    # Carrega todas as movimentações
    movimentos = listar_movimentacoes_bd()
    
    # Filtra todas as vendas, independentemente do status, para a pesquisa
    vendas = [
        m for m in movimentos
        if m[7].lower() in ("venda", "saida", "saída")
    ]
    
    # Radiobox para filtrar vendas Ativas ou Inativas
    filtro_status = st.radio("Filtrar vendas por status:", ["Ativas", "Inativas"])
    status_filter = "ativo" if filtro_status == "Ativas" else "inativo"
    
    # Filtra as vendas com base no status selecionado
    vendas_filtradas_status = [m for m in vendas if m[10].lower() == status_filter]
    
    if vendas_filtradas_status:
        colunas = [
            "ID", "Operação", "Data", "Produto",
            "Custo Inicial", "Preço de Venda", "Quantidade",
            "Tipo", "Usuário", "Método Pagamento", "Status", "Total"
        ]
        df_vendas = pd.DataFrame(vendas_filtradas_status, columns=colunas)
        st.dataframe(df_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda encontrada para o status selecionado.")
    
    st.markdown("---")
    st.subheader("Pesquisar Venda por Número de Operação")
    # Campo para pesquisa: insere número da operação
    op_num_input = st.number_input("Digite o número da operação", min_value=0, value=0, step=1)
    op_num_str = f"{op_num_input:02d}"
    st.markdown(f"**Procurando operação: {op_num_str}**")
    
    # Filtra as vendas com base no número de operação (além do status selecionado)
    vendas_filtradas = [
        m for m in vendas_filtradas_status if m[1] == op_num_str
    ]
    
    if vendas_filtradas:
        # Cria uma combobox listando os produtos dessa venda
        opcoes = [f"{m[3]} - Qtd: {m[6]} - Total: R$ {m[11]:.2f}" for m in vendas_filtradas]
        selecao = st.selectbox("Selecione um produto da venda para editar/inativar:", opcoes)
        
        if selecao:
            venda_selecionada = next((m for m in vendas_filtradas if f"{m[3]} - Qtd: {m[6]} - Total: R$ {m[11]:.2f}" == selecao), None)
            if venda_selecionada:
                (id_, num_operacao, data, produto, custo_inicial, preco_venda,
                 quantidade, tipo, usuario, metodo_pagamento, status, total) = venda_selecionada
                
                st.markdown("### Dados da Venda Selecionada")
                st.write(f"**Operação:** {num_operacao}")
                st.write(f"**Produto:** {produto}")
                st.write(f"**Quantidade Atual:** {quantidade}")
                st.write(f"**Preço de Venda:** R$ {preco_venda:.2f}")
                st.write(f"**Método de Pagamento:** {metodo_pagamento}")
                st.write(f"**Total:** R$ {total:.2f}")
                st.write(f"**Data:** {data}")
                
                with st.form("editar_venda_produto"):
                    nova_quantidade = st.number_input("Nova Quantidade", min_value=1, value=quantidade, step=1)
                    novo_metodo = st.selectbox(
                        "Novo Método de Pagamento",
                        ["Dinheiro", "Pix", "Cartão", "Cheque", "Outro"],
                        index=["Dinheiro", "Pix", "Cartão", "Cheque", "Outro"].index(metodo_pagamento)
                        if metodo_pagamento in ["Dinheiro", "Pix", "Cartão", "Cheque", "Outro"] else 0
                    )
                    # Checkbox com valor padrão marcado se a venda estiver inativa
                    inativar = st.checkbox("Inativar esta venda", value=(status.lower() == "inativo"))
                    submit = st.form_submit_button("Salvar Alterações")
                    
                    if submit:
                        novo_status = "Inativo" if inativar else "Ativo"
                        novo_total = nova_quantidade * preco_venda
                        atualizar_movimentacao_venda(
                            id_=id_,
                            nova_quantidade=nova_quantidade,
                            novo_metodo=novo_metodo,
                            novo_status=novo_status,
                            novo_total=novo_total
                        )
                        st.success("Venda atualizada com sucesso!")
                        st.rerun()

    else:
        st.info("Nenhuma venda ativa encontrada para esse número de operação.")



def pagina_financeiro():
    st.title("Financeiro")
    st.subheader("Resumo Financeiro")
    
    # Carrega todas as movimentações
    movimentos = listar_movimentacoes_bd()
    # Cada movimento tem 12 colunas:
    # 0: id, 1: num_operacao, 2: data, 3: nome, 4: custo_inicial, 5: preco_venda,
    # 6: quantidade, 7: tipo, 8: usuario, 9: metodo_pagamento, 10: status, 11: total
    
    # Filtra entradas ativas
    entradas = [m for m in movimentos if m[7].lower() == "entrada" and m[10].lower() == "ativo"]
    # Filtra vendas ativas (considerando "venda", "saida" e "saída")
    vendas = [m for m in movimentos if m[7].lower() in ("venda", "saida", "saída") and m[10].lower() == "ativo"]
    
    total_despesa = sum(m[11] for m in entradas)
    total_venda_bruta = sum(m[11] for m in vendas)
    saldo = total_venda_bruta - total_despesa
    
    # Define a cor do card do saldo com base no valor
    if saldo < 0:
        cor_saldo = "#f8d7da"  # vermelho claro para saldo negativo
    else:
        cor_saldo = "#d1ecf1"  # azul claro para saldo positivo

    # Exibir os resultados em três cards com HTML
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; gap: 20px; margin-top: 20px;">
        <div style="background-color: #f8d7da; padding: 20px; border-radius: 8px; text-align: center;">
            <h3>Total Despesa</h3>
            <p style="font-size: 24px; font-weight: bold;">R$ {total_despesa:.2f}</p>
        </div>
        <div style="background-color: #d1ecf1; padding: 20px; border-radius: 8px; text-align: center;">
            <h3>Total Venda Bruta</h3>
            <p style="font-size: 24px; font-weight: bold;">R$ {total_venda_bruta:.2f}</p>
        </div>
        <div style="background-color: {cor_saldo}; padding: 20px; border-radius: 8px; text-align: center;">
            <h3>Saldo</h3>
            <p style="font-size: 24px; font-weight: bold;">R$ {saldo:.2f}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


 # Separador abaixo dos cards
    st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    # --- Abaixo do separador na página Financeiro ---

    st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.subheader("Métricas por Produto")

    # Carrega todas as movimentações
    movimentos = listar_movimentacoes_bd()

    # Filtra as movimentações ativas:
    # Vendas (tipo: venda, saida, saída) e Entradas (tipo: entrada)
    vendas = [m for m in movimentos if m[7].lower() in ("venda", "saida", "saída") and m[10].lower() == "ativo"]
    entradas = [m for m in movimentos if m[7].lower() == "entrada" and m[10].lower() == "ativo"]

    # Agrupar vendas por produto
    vendas_por_produto = {}
    for m in vendas:
        produto = m[3]  # Nome do produto
        quantidade = m[6]
        total_venda = m[11]
        if produto not in vendas_por_produto:
            vendas_por_produto[produto] = {"quantidade": 0, "total_venda": 0}
        vendas_por_produto[produto]["quantidade"] += quantidade
        vendas_por_produto[produto]["total_venda"] += total_venda

    # Agrupar entradas por produto
    entradas_por_produto = {}
    for m in entradas:
        produto = m[3]  # Nome do produto
        total_entrada = m[11]
        if produto not in entradas_por_produto:
            entradas_por_produto[produto] = 0
        entradas_por_produto[produto] += total_entrada

    # Define quantas colunas por linha (exemplo: 3)
    num_colunas = 3
    cols = st.columns(num_colunas)

    i = 0
    for produto, dados in vendas_por_produto.items():
        total_venda = dados["total_venda"]
        quantidade = dados["quantidade"]
        total_entrada = entradas_por_produto.get(produto, 0)
        lucro = total_venda - total_entrada
        valor_formatado = f"R$ {lucro:.2f}"
        # Exibe o card de métrica para o produto
        cols[i % num_colunas].metric(label=produto, value=valor_formatado, delta=f"{quantidade} vendidos")
        i += 1

    # Separador abaixo dos cards financeiros
    st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.subheader("Distribuição dos Métodos de Pagamento nas Vendas")

    # Filtra as vendas ativas (assumindo que vendas é a lista filtrada com:
    # m[9] => método de pagamento, m[7] => tipo, m[10] => status)
    vendas = [m for m in listar_movimentacoes_bd() if m[7].lower() in ("venda", "saida", "saída") and m[10].lower() == "ativo"]

    # Contabiliza os métodos de pagamento
    metodos = {}
    for m in vendas:
        metodo = m[9]
        # Normaliza os valores:
        if metodo.lower() in ["dinheiro"]:
            key = "Dinheiro"
        elif metodo.lower() in ["pix"]:
            key = "Pix"
        elif metodo.lower() in ["cartão", "cartao"]:
            key = "Cartão"
        else:
            key = "Outro"
        metodos[key] = metodos.get(key, 0) + 1

    # Cria um DataFrame para o gráfico
    df_metodos = pd.DataFrame({
        "Método": list(metodos.keys()),
        "Quantidade": list(metodos.values())
    })
    df_metodos["Porcentagem"] = df_metodos["Quantidade"] / df_metodos["Quantidade"].sum() * 100

    # Base do gráfico
    base = alt.Chart(df_metodos).encode(
        theta=alt.Theta(field="Quantidade", type="quantitative"),
        color=alt.Color(field="Método", type="nominal", legend=alt.Legend(title="Método"))
    )

    # Gráfico de rosca (donut chart)
    arc = base.mark_arc(innerRadius=50)
    # Rótulos: exibe a quantidade dentro de cada segmento
    text = base.mark_text(radius=80, color="black").encode(
        text=alt.Text(field="Quantidade", type="quantitative")
    )
    text = base.mark_text(radius=80, color="black", fontSize=20).encode(
    text=alt.Text(field="Quantidade", type="quantitative")
    )

    chart = (arc + text).properties(
        title="Métodos de Pagamento nas Vendas"
    )

    st.altair_chart(chart, use_container_width=True)





def pagina_gerenciar_usuarios():
    st.title("Gerenciar Usuários")

    st.subheader("Cadastrar Novo Usuário")
    with st.form("cadastro_novo_usuario"):
        novo_login  = st.text_input("Novo Login")
        nova_senha = st.text_input("Senha", type="password")
        st.write("Permissões do Novo Usuário:")
        perm_cad_produtos  = st.checkbox("Cadastrar Produtos")
        perm_ger_vendas    = st.checkbox("Gerenciar Vendas")
        perm_emit_venda    = st.checkbox("Emitir Venda")
        perm_financeiro    = st.checkbox("Financeiro")
        perm_geren_user    = st.checkbox("Gerenciar Usuários")

        if st.form_submit_button("Cadastrar"):
            sucesso = cadastrar_usuario_bd(
                login=novo_login,
                senha=nova_senha,
                perm_cadastrar_produtos=perm_cad_produtos,
                perm_estornar_produtos=perm_ger_vendas,
                perm_emitir_venda=perm_emit_venda,
                perm_financeiro=perm_financeiro,
                perm_gerenciar_usuarios=perm_geren_user
            )
            if sucesso:
                st.success(f"Usuário '{novo_login}' cadastrado com sucesso!")
            else:
                st.error(f"Não foi possível cadastrar. Usuário '{novo_login}' já existe ou erro no banco.")

    st.write("---")
    st.subheader("Lista de Usuários Cadastrados")
    usuarios = listar_usuarios_bd()
    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
        return

    colunas = [
        "id", "login", "senha",
        "perm_cadastrar_produtos", "perm_gerenciar_vendas",
        "perm_emit_venda", "perm_financeiro", "perm_gerenciar_usuarios"
    ]
    df = pd.DataFrame(usuarios, columns=colunas)
    st.dataframe(df, use_container_width=True)

    opcoes = [f"{u[0]} - {u[1]}" for u in usuarios]
    escolha = st.selectbox("Selecione um usuário:", opcoes)
    if escolha:
        user_id = int(escolha.split(" - ")[0])
        user_info = next((u for u in usuarios if u[0] == user_id), None)
        if user_info:
            (id_, login_, senha_,
             p_cad_prod, p_est_prod,
             p_emit_venda, p_fin,
             p_gerenciar) = user_info

            st.write(f"**Editando usuário:** {login_} (ID={id_})")
            with st.form("editar_usuario"):
                nova_senha = st.text_input("Nova Senha (vazio = não alterar)", type="password")
                cad_prod_edit   = st.checkbox("Cadastrar Produtos", value=bool(p_cad_prod))
                est_prod_edit   = st.checkbox("Gerenciar Vendas", value=bool(p_est_prod))
                emit_venda_edit = st.checkbox("Emitir Venda", value=bool(p_emit_venda))
                fin_edit        = st.checkbox("Financeiro", value=bool(p_fin))
                gerenciar_edit  = st.checkbox("Gerenciar Usuários", value=bool(p_gerenciar))

                if st.form_submit_button("Salvar"):
                    if not nova_senha:
                        nova_senha = senha_
                    atualizar_usuario_bd(
                        user_id=id_,
                        nova_senha=nova_senha,
                        cad_produtos=cad_prod_edit,
                        est_prod=est_prod_edit,
                        emit_venda=emit_venda_edit,
                        financeiro=fin_edit,
                        gerenciar_usuarios=gerenciar_edit
                    )
                    st.success(f"Usuário {login_} atualizado!")
                    st.rerun()

            if st.button("Excluir Usuário"):
                excluir_usuario_bd(id_)
                st.warning(f"Usuário '{login_}' excluído!")
                st.rerun()

################################################
# MAIN
################################################

def main():
    st.title("Gerenciador de Vendas 🛒")

    if "banco_inicializado" not in st.session_state:
        criar_banco_de_dados()
        st.session_state.banco_inicializado = True  # Evita repetição

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = ""
    if "permissoes" not in st.session_state:
        st.session_state.permissoes = {}

    if not st.session_state.autenticado:
        login_input = st.text_input("Login")
        senha_input = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            # Verifica Master
            if login_input == "Master" and senha_input == "1235":
                st.session_state.autenticado = True
                st.session_state.usuario_logado = "Master"
                st.session_state.permissoes = {
                    "cadastrar_produtos":  True,
                    "gerenciar_vendas":    True,
                    "emitir_venda":        True,
                    "financeiro":          True,
                    "gerenciar_usuarios":  True
                }
                st.rerun()
            else:
                user_db = buscar_usuario_bd(login_input, senha_input)
                if user_db:
                    st.session_state.autenticado = True
                    st.session_state.usuario_logado = user_db[1]
                    # user_db => (id, login, senha, perm_cad_prod, perm_est_prod, perm_emit_venda, perm_fin, perm_geren_user)
                    st.session_state.permissoes = {
                        "cadastrar_produtos": bool(user_db[3]),
                        "gerenciar_vendas":   bool(user_db[4]),
                        "emitir_venda":       bool(user_db[5]),
                        "financeiro":         bool(user_db[6]),
                        "gerenciar_usuarios": bool(user_db[7])
                    }
                    st.rerun()
                else:
                    st.error("Login inválido.")
    else:
        st.success(f"Bem-vindo, {st.session_state.usuario_logado}!")
        perms = st.session_state.permissoes
        menu_opcoes = []
        menu_icones = []

        if perms.get("gerenciar_usuarios"):
            menu_opcoes.append("Gerenciar Usuários")
            menu_icones.append("people")
        if perms.get("cadastrar_produtos"):
            menu_opcoes.append("Cadastrar Produtos")
            menu_icones.append("box-arrow-in-down")
        if perms.get("gerenciar_vendas"):
            menu_opcoes.append("Gerenciar Vendas")
            menu_icones.append("arrow-counterclockwise")
        if perms.get("emitir_venda"):
            menu_opcoes.append("Emitir Venda")
            menu_icones.append("cart-check")
        if perms.get("financeiro"):
            menu_opcoes.append("Financeiro")
            menu_icones.append("wallet2")

        menu_opcoes.append("Sair")
        menu_icones.append("door-closed")

        with st.sidebar:
            selected = option_menu(
                "Menu Permissões",
                menu_opcoes,
                icons=menu_icones,
                menu_icon="cast",
                default_index=0,
                orientation="vertical",
                key="menu_principal"
            )

        if selected == "Gerenciar Usuários":
            pagina_gerenciar_usuarios()
        elif selected == "Cadastrar Produtos":
            pagina_cadastrar_produtos()
        elif selected == "Gerenciar Vendas":
            pagina_gerenciar_vendas()
        elif selected == "Emitir Venda":
            pagina_emitir_venda()
        elif selected == "Financeiro":
            pagina_financeiro()
        elif selected == "Sair":
            st.session_state.autenticado = False
            st.session_state.usuario_logado = ""
            st.session_state.permissoes = {}
            st.rerun()
        else:
            st.write("Selecione uma das opções no menu lateral.")

if __name__ == "__main__":
    main()
