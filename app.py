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

# --- 1. BARRA LATERAL ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if dados_img:
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{dados_img}" style="max-width: 85%; max-height: 150px; border-radius: 8px;"></div>', unsafe_allow_html=True)

st.sidebar.markdown("<hr style='margin-top: 15px; margin-bottom: 15px;'>", unsafe_allow_html=True)

aba = st.sidebar.radio("Selecione a Ação", [
    "Visualizar Estoque & Histórico", 
    "Dar Entrada em Peça", 
    "Dar Saída (Destinar à Frota)",
    "❌ Excluir Peça (Restrito)"
])

# --- 2. PARTE CENTRAL ---
if dados_img:
    st.markdown(f'<div style="text-align: center; margin-bottom: -10px;"><img src="data:image/png;base64,{dados_img}" style="max-width: 180px; max-height: 120px; border-radius: 8px; margin-bottom: 10px;"><h1 style="font-weight: bold; margin-top: 0px; color: #ffffff;">Controle de Depósito</h1></div>', unsafe_allow_html=True)
else:
    st.markdown('<h1 style="text-align: center; font-weight: bold; color: #ffffff;">Controle de Depósito</h1>', unsafe_allow_html=True)

st.markdown("---")

if conexao:
    # --- PAINEL DE ALERTA MÁXIMO (Estoque = 1) ---
    cursor = conexao.cursor()
    cursor.execute("SELECT nome_peca FROM estoque WHERE quantidade = 1")
    pecas_criticas = [linha[0] for linha in cursor.fetchall()]
    if pecas_criticas:
        st.error(f"### 🚨 ALERTA MÁXIMO DE COMPRA: PEÇAS ACABANDO!\nAs seguintes peças possuem apenas **1 unidade** no depósito e precisam de reposição urgente: {', '.join([f'**{p}**' for p in pecas_criticas])}")
        st.markdown("---")

    # --- ABA 1: VISUALIZAR ---
    if aba == "Visualizar Estoque & Histórico":
        st.subheader("📋 Saldo Atual do Depósito")
        df_estoque = pd.read_sql_query("SELECT nome_peca as \"Nome da Peça\", quantidade as \"Quantidade em Estoque\" FROM estoque ORDER BY nome_peca", conexao)
        if not df_estoque.empty:
            def destacar_critico(linha):
                cor = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if linha['Quantidade em Estoque'] == 1 else ''
                return [cor] * len(linha)
            st.dataframe(df_estoque.style.apply(destacar_critico, axis=1), use_container_width=True)
        else:
            st.info("Nenhuma peça cadastrada no momento.")
            
        st.markdown("---")
        st.subheader("📜 Histórico Geral de Movimentações")
        df_historico = pd.read_sql_query("SELECT tipo_movimentacao as \"Operação\", nome_peca as \"Peça\", quantidade as \"Qtd\", frota as \"Frota/Veículo\", utilizacao as \"Utilização\", data_hora as \"Data/Hora\" FROM historico ORDER BY id DESC", conexao)
        if not df_historico.empty:
            st.dataframe(df_historico, use_container_width=True)

    # --- ABA 2: ENTRADA ---
    elif aba == "Dar Entrada em Peça":
        st.subheader("📥 Registro de Entrada no Depósito")
        with st.form("form_entrada", clear_on_submit=True):
            nome = st.text_input("Nome da Peça / Código:").strip().upper()
            qtd = st.number_input("Quantidade de Entrada:", min_value=1, step=1)
            if st.form_submit_button("Confirmar Entrada") and nome:
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO estoque (nome_peca, quantidade) VALUES (%s, %s) ON CONFLICT(nome_peca) DO UPDATE SET quantidade = estoque.quantidade + EXCLUDED.quantidade", (nome, qtd))
                cursor.execute("INSERT INTO historico (tipo_movimentacao, nome_peca, quantidade, frota, utilizacao, data_hora) VALUES (%s, %s, %s, %s, %s, %s)", ("ENTRADA", nome, qtd, "-", "Abastecimento de Depósito", datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                conexao.commit()
                st.success(f"Entrada realizada!")
                st.rerun()

    # --- ABA 3: SAÍDA ---
    elif aba == "Dar Saída (Destinar à Frota)":
        st.subheader("📤 Registro de Saída para Frota")
        cursor = conexao.cursor()
        cursor.execute("SELECT nome_peca FROM estoque WHERE quantidade > 0 ORDER BY nome_peca")
        pecas = [linha[0] for linha in cursor.fetchall()]
        
        if not pecas:
            st.warning("Não há peças disponíveis.")
        else:
            with st.form("form_saida", clear_on_submit=True):
                peca_sel = st.selectbox("Selecione a Peça:", pecas)
                cursor = conexao.cursor()
                cursor.execute("SELECT quantidade FROM estoque WHERE nome_peca = %s", (peca_sel,))
                saldo_atual = int(cursor.fetchone()[0])
                st.info(f"Saldo atual desta peça no depósito: {saldo_atual} unidades.")
                
                qtd_saida = st.number_input("Quantidade de Saída:", min_value=1, max_value=saldo_atual, step=1)
                frota = st.text_input("Identificação da Frota:").strip().upper()
                utilizacao = st.text_input("Utilização da Peça:").strip()
                
                if st.form_submit_button("Confirmar Saída") and frota and utilizacao:
                    novo_saldo = saldo_atual - qtd_saida
                    cursor.execute("UPDATE estoque SET quantidade = %s WHERE nome_peca = %s", (novo_saldo, peca_sel))
                    # CORREGIDO: Removido termo misturado em inglês da linha de histórico antiga
                    cursor.execute("INSERT INTO historico (tipo_movimentacao, nome_peca, quantidade, frota, utilizacao, data_hora) VALUES (%s, %s, %s, %s, %s, %s)", ("SAÍDA", peca_sel, qtd_saida, frota, utilizacao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                    conexao.commit()
                    st.success(f"Saída realizada!")
                    st.rerun()

    # --- ❌ ABA 4: EXCLUIR PEÇA ---
    elif aba == "❌ Excluir Peça (Restrito)":
        st.subheader("🗑️ Excluir Item com Identificação de Garagista")
        st.warning("Atenção: A peça será removida do saldo do depósito, e o responsável pela remoção ficará permanentemente gravado no histórico.")
        
        cursor = conexao.cursor()
        cursor.execute("SELECT nome_peca FROM estoque ORDER BY nome_peca")
        dados_estoque_atual = [linha[0] for linha in cursor.fetchall()]
        
        if not dados_estoque_atual:
            st.info("Não há nenhuma peça cadastrada no sistema no momento.")
        else:
            with st.form("form_exclusao", clear_on_submit=True):
                peca_para_excluir = st.selectbox("Selecione a Peça que deseja deletar do estoque:", dados_estoque_atual)
                senha_digitada = st.text_input("Digite sua senha de Garagista para autorizar:", type="password")
                
                botao_deletar = st.form_submit_button("💥 Confirmar Remoção do Estoque")
                
                if botao_deletar:
                    if senha_digitada == "":
                        st.error("Por favor, insira uma senha para continuar.")
                    else:
                        garagista_identificado = None
                        for chave, dados in GARAGISTAS.items():
                            if senha_digitada == dados["senha"]:
                                garagista_identificado = dados["nome"]
                                break
                        
                        if not garagista_identificado:
                            st.error("❌ Senha incorreta! Acesso negado.")
                        else:
                            cursor = conexao.cursor()
                            # CORREGIDO: Puxando o número de dentro da lista de forma limpa para evitar o TypeError
                            cursor.execute("SELECT quantidade FROM estoque WHERE nome_peca = %s", (peca_para_excluir,))
                            qtd_antes_deletar = int(cursor.fetchone()[0])
                            
                            # Remove do saldo atual
                            cursor.execute("DELETE FROM estoque WHERE nome_peca = %s", (peca_para_excluir,))
                            
                            # Registra no histórico

                            
                            # Registra permanentemente no histórico QUEM deletou e O QUE deletou
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

