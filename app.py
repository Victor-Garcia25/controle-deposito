import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Controle de Depósito", layout="wide")

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

# --- ESTILIZAÇÃO DO FUNDO AZUL DO SISTEMA ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b1e4f 0%, #164095 50%, #1e5fc1 100%);
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 1. BARRA LATERAL ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if dados_img:
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{dados_img}" style="max-width: 85%; max-height: 150px; border-radius: 8px;"></div>', unsafe_allow_html=True)

st.sidebar.markdown("<hr style='margin-top: 15px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# Estado para controlar qual tela está ativa por clique dos cards
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = "🏠 Menu Principal"

# Menu da barra lateral para navegação rápida ou voltar
aba_lateral = st.sidebar.selectbox("Navegação Direta:", [
    "🏠 Menu Principal",
    "📋 Painel do Estoque & Histórico", 
    "📥 Dar Entrada em Peça", 
    "📤 Dar Saída (Destinar à Frota)"
])

# Sincroniza a barra lateral com o estado das telas
if aba_lateral != st.session_state["tela_ativa"] and st.sidebar.button("Ir para seleção"):
    st.session_state["tela_ativa"] = aba_lateral
    st.rerun()

# --- 2. PARTE CENTRAL ---
if dados_img:
    st.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{dados_img}" style="max-width: 140px; border-radius: 8px;"></div>', unsafe_allow_html=True)

if conexao:
    cursor = conexao.cursor()

    # =========================================================================
    # 🏠 TELA: MENU PRINCIPAL EM BLOCOS (LAYOUT DA IMAGEM)
    # =========================================================================
    if st.session_state["tela_ativa"] == "🏠 Menu Principal":
        st.markdown("<h2 style='text-align: center; font-weight: bold; margin-bottom: 30px;'>Sistema Integrado de Gestão de Almoxarifado</h2>", unsafe_allow_html=True)
        
        # Criação da estrutura de colunas para os blocos
        col1, col2, col3, col4 = st.columns(4)
        
        # CARD 1: Painel do Estoque
        with col1:
            st.markdown("""
                <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #ff6600; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 160px;'>
                    <h2 style='margin: 0; color: #333 !important;'>📊</h2>
                    <p style='font-weight: bold; font-size: 16px; margin-top: 10px; color: #333 !important;'>Painel Geral & Histórico</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Acessar Painel", key="btn_p1", use_container_width=True):
                st.session_state["tela_ativa"] = "📋 Painel do Estoque & Histórico"
                st.rerun()

        # CARD 2: Entradas de Materiais
        with col2:
            st.markdown("""
                <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #0066cc; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 160px;'>
                    <h2 style='margin: 0; color: #333 !important;'>📥</h2>
                    <p style='font-weight: bold; font-size: 16px; margin-top: 10px; color: #333 !important;'>Dar Entrada em Peça</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Acessar Entradas", key="btn_p2", use_container_width=True):
                st.session_state["tela_ativa"] = "📥 Dar Entrada em Peça"
                st.rerun()

        # CARD 3: Saídas para Frota
        with col3:
            st.markdown("""
                <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #9933ff; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 160px;'>
                    <h2 style='margin: 0; color: #333 !important;'>📤</h2>
                    <p style='font-weight: bold; font-size: 16px; margin-top: 10px; color: #333 !important;'>Dar Saída para Frota</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Acessar Saídas", key="btn_p3", use_container_width=True):
                st.session_state["tela_ativa"] = "📤 Dar Saída (Destinar à Frota)"
                st.rerun()

        # CARD 4: Inventário e Alertas (Visualização rápida de críticos)
        with col4:
            cursor.execute("SELECT COUNT(*) FROM estoque WHERE quantidade = 1")
            qtd_criticos = cursor.fetchone()[0]
            st.markdown(f"""
                <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #00cc66; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 160px;'>
                    <h2 style='margin: 0; color: #333 !important;'>⚠️</h2>
                    <p style='font-weight: bold; font-size: 16px; margin-top: 10px; color: #333 !important;'>Alertas Críticos: {qtd_criticos}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Verificar Alertas", key="btn_p4", use_container_width=True):
                st.session_state["tela_ativa"] = "📋 Painel do Estoque & Histórico"
                st.rerun()

    # =========================================================================
    # 📋 TELA: PAINEL DO ESTOQUE & HISTÓRICO
    # =========================================================================
    elif st.session_state["tela_ativa"] == "📋 Painel do Estoque & Histórico":
        if st.button("⬅️ Voltar ao Menu Principal"):
            st.session_state["tela_ativa"] = "🏠 Menu Principal"
            st.rerun()
            
        st.subheader("📋 Saldo Atual do Depósito")
        cursor.execute("SELECT id, nome_peca, quantidade FROM estoque ORDER BY nome_peca")
        pecas_deposito = cursor.fetchall()
        
        if pecas_deposito:
            for id_peca, nome_peca, quantidade in pecas_deposito:
                col_info, col_btn = st.columns([6, 1])
                if quantidade == 1:
                    col_info.markdown(f"🔴 **{nome_peca}** — Quantidade em Estoque: `{quantidade}` unidades (CRÍTICO)")
                else:
                    col_info.markdown(f"📦 **{nome_peca}** — Quantidade em Estoque: `{quantidade}` unidades")
                
                if col_btn.button("🗑️ Excluir", key=f"del_{id_peca}"):
                    st.session_state["id_para_excluir"] = id_peca
                    st.session_state["nome_para_excluir"] = nome_peca
                    st.session_state["qtd_para_excluir"] = quantidade
            
            if "id_para_excluir" in st.session_state:
                st.markdown("---")
                st.warning(f"⚠️ Confirmar Exclusão de: **{st.session_state['nome_para_excluir']}**")
                senha_adm = st.text_input("Digite sua senha de Garagista para apagar:", type="password")
                col_conf, col_canc = st.columns([1, 5])
                
                if col_conf.button("💥 Confirmar Deletar", type="primary"):
                    garagista_identificado = None
                    for chave, dados in GARAGISTAS.items():
                        if senha_adm == dados["senha"]:
                            garagista_identificado = dados["nome"]
                            break
                    if not garagista_identificado:
                        st.error("❌ Senha incorreta!")
                    else:
                        cursor.execute("DELETE FROM estoque WHERE id = %s", (st.session_state["id_para_excluir"],))
                        cursor.execute("INSERT INTO historico (tipo_movimentacao, nome_peca, quantidade, frota, utilizacao, data_hora) VALUES (%s, %s, %s, %s, %s, %s)",
