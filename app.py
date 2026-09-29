import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Controle de Estoque", layout="wide")

# 🔑 NOMES E SENHAS DOS GARAGISTAS
GARAGISTAS = {
    "GARAGISTA_01": {"nome": "VICTOR", "senha": "2528"},
    "GARAGISTA_02": {"nome": "REGINALDO", "senha": "7472"}
}

# --- CONEXÃO COM O BANCO DE DADOS NA NUVEM (NEON) ---
def conectar_banco():
    try:
        conexao = psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"]
        )
        return conexao
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados na nuvem: {e}")
        return None

conexao = conectar_banco()

if conexao:
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY,
            nome_peca TEXT UNIQUE,
            quantidade INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            tipo_movimentacao TEXT,
            nome_peca TEXT,
            quantidade INTEGER,
            frota TEXT,
            utilizacao TEXT,
            data_hora TEXT
        )
    ''')
    conexao.commit()

# --- FUNÇÃO PARA CONVERTER IMAGEM PARA BASE64 ---
def obter_imagem_base64(caminho_imagem):
    try:
        with open(caminho_imagem, "rb") as arquivo_img:
            return base64.b64encode(arquivo_img.read()).decode()
    except Exception:
        return None

nome_logo = None
for formato in ["logo.png", "logo.jpg", "logo.jpeg", "LOGO.PNG", "LOGO.JPG", "LOGO.JPEG"]:
    if os.path.exists(formato):
        nome_logo = formato
        break

dados_img = obter_imagem_base64(nome_logo) if nome_logo else None

# --- 1. BARRA LATERAL ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if dados_img:
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{dados_img}" style="max-width: 85%; max-height: 150px; border-radius: 8px;"></div>', unsafe_allow_html=True)

st.sidebar.markdown("<hr style='margin-top: 15px; margin-bottom: 15px;'>", unsafe_allow_html=True)

aba = st.sidebar.radio("Selecione a Ação", [
    "📋 Painel do Estoque & Histórico", 
    "📥 Dar Entrada em Peça", 
    "📤 Dar Saída (Destinar à Frota)"
])

# --- 2. PARTE CENTRAL ---
if dados_img:
    st.markdown(f'<div style="text-align: center; margin-bottom: -10px;"><img src="data:image/png;base64,{dados_img}" style="max-width: 180px; max-height: 120px; border-radius: 8px; margin-bottom: 10px;"><h1 style="font-weight: bold; margin-top: 0px; color: #ffffff;">Controle de Estoque</h1></div>', unsafe_allow_html=True)
else:
    st.markdown('<h1 style="text-align: center; font-weight: bold; color: #ffffff;">Controle de Estoque</h1>', unsafe_allow_html=True)

st.markdown("---")

if conexao:
    cursor = conexao.cursor()
    
    # --- PAINEL DE ALERTA MÁXIMO (Estoque = 1) ---
    cursor.execute("SELECT nome_peca FROM estoque WHERE quantidade = 1")
    pecas_criticas = [linha[0] for linha in cursor.fetchall()]
    if pecas_criticas:
        st.error(f"### 🚨 ALERTA MÁXIMO DE COMPRA: PEÇAS ACABANDO!\nAs seguintes peças possuem apenas **1 unidade** no depósito e precisam de reposição urgente: {', '.join([f'**{p}**' for p in pecas_criticas])}")
        st.markdown("---")

    # --- ABA 1: VISUALIZAR COM BOTÃO DE EXCLUIR ---
    if aba == "📋 Painel do Estoque & Histórico":
        st.subheader("📋 Saldo Atual do Depósito")
        
        cursor.execute("SELECT id, nome_peca, quantidade FROM estoque ORDER BY nome_peca")
        pecas_deposito = cursor.fetchall()
        
        if pecas_deposito:
            # Renderiza as peças em linhas organizadas com um botão ao lado
            for id_peca, nome_peca, quantidade in pecas_deposito:
                col_info, col_btn = st.columns([6, 1])
                
                # Alerta visual em vermelho caso tenha apenas 1 peça
                if quantidade == 1:
                    col_info.markdown(f"🔴 **{nome_peca}** — Quantidade em Estoque: `{quantidade}` unidades (CRÍTICO)")
                else:
                    col_info.markdown(f"📦 **{nome_peca}** — Quantidade em Estoque: `{quantidade}` unidades")
                
                # Cria um botão de lixeira individual para cada item
                if col_btn.button("🗑️ Excluir", key=f"del_{id_peca}"):
                    st.session_state["id_para_excluir"] = id_peca
                    st.session_state["nome_para_excluir"] = nome_peca
                    st.session_state["qtd_para_excluir"] = quantidade
            
            # Se clicou em excluir, abre o validador de senha fixo embaixo da tabela
            if "id_para_excluir" in st.session_state:
                st.markdown("---")
                st.warning(f"### ⚠️ Confirmar Exclusão de: **{st.session_state['nome_para_excluir']}**")
                
                senha_adm = st.text_input("Digite sua senha de Garagista para apagar permanentemente:", type="password", key="senha_exclusao_direta")
                col_conf, col_canc = st.columns([1, 5])
                
                if col_conf.button("💥 Confirmar Deletar", type="primary"):
                    garagista_identificado = None
                    for chave, dados in GARAGISTAS.items():
                        if senha_adm == dados["senha"]:
                            garagista_identificado = dados["nome"]
                            break
                    
                    if not garagista_identificado:
                        st.error("❌ Senha incorreta! Acesso negado.")
                    else:
                        id_del = st.session_state["id_para_excluir"]
                        nome_del = st.session_state["nome_para_excluir"]
                        qtd_del = st.session_state["qtd_para_excluir"]
                        
                        # Executa a remoção direta por ID numérico
                        cursor.execute("DELETE FROM estoque WHERE id = %s", (id_del,))
                        
                        # Salva na auditoria do histórico
                        data_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        cursor.execute(
                            "INSERT INTO historico (tipo_movimentacao, nome_peca, quantidade, frota, utilizacao, data_hora) VALUES (%s, %s, %s, %s, %s, %s)",
                            ("EXCLUSÃO", nome_del, qtd_del, "-", f"Item apagado por: {garagista_identificado}", data_actual)
                        )
                        conexao.commit()
                        st.success("Item removido com sucesso!")
                        
                        # Limpa os estados da memória
                        del st.session_state["id_para_excluir"]
                        st.rerun()
                        
                if col_canc.button("Cancelar"):
                    del st.session_state["id_para_excluir"]
                    st.rerun()
        else:
            st.info("Nenhuma peça cadastrada no depósito no momento.")
            
        st.markdown("---")
        st.subheader("📜 Histórico Geral de Movimentações")
        df_historico = pd.read_sql_query("SELECT tipo_movimentacao as \"Operação\", nome_peca as \"Peça\", quantidade as \"Qtd\", frota as \"Frota/Veículo\", utilizacao as \"Utilização\", data_hora as \"Data/Hora\" FROM historico ORDER BY id DESC", conexao)
        if not df_historico.empty:
            st.dataframe(df_historico, use_container_width=True)

    # --- ABA 2: ENTRADA ---
    elif aba == "📥 Dar Entrada em Peça":
        st.subheader("📥 Registro de Entrada no Depósito")
        with st.form("form_entrada", clear_on_submit=True):
            nome = st.text_input("Nome da Peça / Código:").strip().upper()
            qtd = st.number_input("Quantidade de Entrada:", min_value=1, step=1)
            if st.form_submit_button("Confirmar Entrada") and nome:
                cursor.execute("INSERT INTO estoque (nome_peca, quantidade) VALUES (%s, %s) ON CONFLICT(nome_peca) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (nome, qtd))
                cursor.execute("INSERT INTO historico (tipo_movimentacao, nome_peca, quantidade, frota, utilizacao, data_hora) VALUES (%s, %s, %s, %s, %s, %s)", ("ENTRADA", nome, qtd, "-", "Abastecimento de Depósito", datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                conexao.commit()
                st.success(f"Entrada realizada!")
                st.rerun()

    # --- ABA 3: SAÍDA ---
    elif aba == "📤 Dar Saída (Destinar à Frota)":
        st.subheader("📤 Registro de Saída para Frota")
        cursor.execute("SELECT id, nome_peca FROM estoque WHERE quantidade > 0 ORDER BY nome_peca")
        dados_saida = cursor.fetchall()
        
        if not dados_saida:
            st.warning("Não há peças disponíveis.")
        else:
            opcoes_saida = {f"{linha[1]}": linha[0] for linha in dados_saida}
            
            with st.form("form_saida", clear_on_submit=True):
                peca_exibida = st.selectbox("Selecione a Peça:", list(opcoes_saida.keys()))
                id_peca_sel = opcoes_saida[peca_exibida]
                
                cursor.execute("SELECT quantidade, nome_peca FROM estoque WHERE id = %s", (id_peca_sel,))
                resultado_saldo = cursor.fetchone()
                saldo_atual = resultado_saldo[0] if resultado_saldo else 0
                nome_peca_real = resultado_saldo[1] if resultado_saldo else ""
                
                st.info(f"Saldo atual desta peça no depósito: {saldo_atual} unidades.")
                
                qtd_saida = st.number_input("Quantidade de Saída:", min_value=1, max_value=max(1, saldo_atual), step=1)
