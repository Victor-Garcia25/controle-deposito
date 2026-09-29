import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import base64
import os
import io

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
            port=st.secrets["DB_PORT"],
            connect_timeout=5
        )
        return conexao
    except Exception:
        return None

conexao = conectar_banco()

# Inicialização das tabelas de forma silenciosa
if conexao:
    try:
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
        cursor.close()
    except Exception:
        pass

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
    div.stButton > button {
        background-color: #ffffff !important;
        color: #0b1e4f !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.2) !important;
        transition: background-color 0.2s, color 0.2s;
    }
    div.stButton > button:hover {
        background-color: #ff6600 !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Oculta a barra lateral cinza para evitar cliques fantasmas
st.markdown("<style>[data-testid=\"stSidebar\"] {display: none;}</style>", unsafe_allow_html=True)

# Inicializa o controle de navegação de telas
if "tela_ativa" not in st.session_state:
    st.session_state["tela_ativa"] = "🏠 Menu Principal"

# --- LOGOMARCA LOGO ACIMA DOS BOTÕES ---
if dados_img:
    st.markdown(f'<div style="text-align: center; margin-top: 10px; margin-bottom: 20px;"><img src="data:image/png;base64,{dados_img}" style="max-width: 140px; border-radius: 8px;"></div>', unsafe_allow_html=True)


# =========================================================================
# 🏠 TELA 1: MENU PRINCIPAL (BLOCOS AZUIS E BRANCOS)
# =========================================================================
if st.session_state["tela_ativa"] == "🏠 Menu Principal":
    st.markdown("<h2 style='text-align: center; font-weight: bold; margin-bottom: 40px;'>Sistema Integrado de Gestão de Almoxarifado</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #ff6600; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 150px; margin-bottom: 12px;'>
                <h1 style='margin: 0; padding: 0; font-size: 35px;'>📊</h1>
                <p style='font-weight: bold; font-size: 15px; margin-top: 10px; color: #333333 !important;'>Painel Geral & Histórico</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📊 Acessar Painel", key="btn_p1_main", use_container_width=True):
            st.session_state["tela_ativa"] = "📋 Painel do Estoque & Histórico"
            st.rerun()

    with col2:
        st.markdown("""
            <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #0066cc; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 150px; margin-bottom: 12px;'>
                <h1 style='margin: 0; padding: 0; font-size: 35px;'>📥</h1>
                <p style='font-weight: bold; font-size: 15px; margin-top: 10px; color: #333333 !important;'>Dar Entrada em Peça</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📥 Acessar Entradas", key="btn_p2_main", use_container_width=True):
            st.session_state["tela_ativa"] = "📥 Dar Entrada em Peça"
            st.rerun()

    with col3:
        st.markdown("""
            <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #9933ff; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 150px; margin-bottom: 12px;'>
                <h1 style='margin: 0; padding: 0; font-size: 35px;'>📤</h1>
                <p style='font-weight: bold; font-size: 15px; margin-top: 10px; color: #333333 !important;'>Dar Saída para Frota</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📤 Acessar Saídas", key="btn_p3_main", use_container_width=True):
            st.session_state["tela_ativa"] = "📤 Dar Saída (Destinar à Frota)"
            st.rerun()

    with col4:
        qtd_criticos = 0
        if conexao:
            try:
                cursor_c = conexao.cursor()
                cursor_c.execute("SELECT COUNT(*) FROM estoque WHERE quantidade = 1")
                res_criticos = cursor_c.fetchone()
                qtd_criticos = res_criticos[0] if res_criticos else 0
                cursor_c.close()
            except Exception:
                qtd_criticos = 0
                
        st.markdown(f"""
            <div style='background-color: white; border-radius: 12px; padding: 25px; text-align: center; border-top: 6px solid #00cc66; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); min-height: 150px; margin-bottom: 12px;'>
                <h1 style='margin: 0; padding: 0; font-size: 35px;'>⚠️</h1>
                <p style='font-weight: bold; font-size: 15px; margin-top: 10px; color: #333333 !important;'>Alertas Críticos: {qtd_criticos}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("⚠️ Verificar Alertas", key="btn_p4_main", use_container_width=True):
            st.session_state["tela_ativa"] = "📋 Painel do Estoque & Histórico"
            st.rerun()


# =========================================================================
# 📋 TELA 2: PAINEL DO ESTOQUE & HISTÓRICO
# =========================================================================
elif st.session_state["tela_ativa"] == "📋 Painel do Estoque & Histórico":
    if st.button("⬅️ Voltar para o Menu Principal", key="back_btn_1"):
        st.session_state["tela_ativa"] = "🏠 Menu Principal"
        st.rerun()
        
    st.markdown("---")
    st.subheader("📋 Saldo Atual do Depósito")
    
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT id, nome_peca, quantidade FROM estoque ORDER BY nome_peca")
            pecas_deposito = cursor.fetchall()
            
            df_estoque = pd.read_sql_query("SELECT nome_peca as \"Nome da Peça\", quantidade as \"Quantidade em Estoque\" FROM estoque ORDER BY nome_peca", conexao)
            df_historico = pd.read_sql_query("SELECT tipo_movimentacao as \"Operação\", nome_peca as \"Peça\", quantidade as \"Qtd\", frota as \"Frota/Veículo\", utilizacao as \"Utilização\", data_hora as \"Data/Hora\" FROM historico ORDER BY id DESC", conexao)
            
            if pecas_deposito:
                for id_peca, nome_peca, quantidade in pecas_deposito:
                    col_info, col_btn = st.columns([6, 1])
                    if quantidade == 1:
                        col_info.markdown(f"🔴 **{nome_peca}** — Estoque: `{quantidade}` unidades (CRÍTICO)")
                    else:
                        col_info.markdown(f"📦 **{nome_peca}** — Estoque: `{quantidade}` unidades")
                    
                    st.markdown("""<style>div[data-testid="stColumn"] button { min-height: auto !important; padding: 5px 10px !important; }</style>""", unsafe_allow_html=True)
                    if col_btn.button("🗑️ Apagar", key=f"del_item_{id_peca}", use_container_width=True):
                        st.session_state["id_para_excluir"] = id_peca
                        st.session_state["nome_para_excluir"] = nome_peca
                        st.session_state["qtd_para_excluir"] = quantidade
                
                if "id_para_excluir" in st.session_state:
                    st.markdown("---")
                    st.warning(f"### ⚠️ Confirmar Exclusão de: **{st.session_state['nome_para_excluir']}**")
                    senha_adm = st.text_input("Digite sua senha de Garagista para apagar:", type="password", key="pwd_del_puro")
                    col_conf, col_canc = st.columns(2)
                    
                    if col_conf.button("💥 Confirmar Deletar", type="primary", key="conf_del_puro"):
                        garagista_identificado = None
