import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. DADOS DA TABELA TJ-MG (ANTIGA/ATÉ AGO 2024) ---
CSV_TJMG = """Data,Indice
2016-01-01,1.51
2016-02-01,0.95
2016-03-01,0.44
2016-04-01,0.64
2016-05-01,0.98
2016-06-01,0.47
2016-07-01,0.64
2016-08-01,0.31
2016-09-01,0.08
2016-10-01,0.17
2016-11-01,0.07
2016-12-01,0.13
2017-01-01,0.42
2017-02-01,0.24
2017-03-01,0.32
2017-04-01,0.08
2017-05-01,0.36
2017-06-01,-0.3
2017-07-01,0.17
2017-08-01,-0.03
2017-09-01,-0.02
2017-10-01,0.37
2017-11-01,0.18
2017-12-01,0.26
2018-01-01,0.23
2018-02-01,0.18
2018-03-01,0.07
2018-04-01,0.21
2018-05-01,0.43
2018-06-01,1.43
2018-07-01,0.25
2018-08-01,0.0
2018-09-01,0.3
2018-10-01,0.4
2018-11-01,-0.25
2018-12-01,0.14
2019-01-01,0.36
2019-02-01,0.54
2019-03-01,0.77
2019-04-01,0.6
2019-05-01,0.15
2019-06-01,0.01
2019-07-01,0.1
2019-08-01,0.12
2019-09-01,-0.05
2019-10-01,0.04
2019-11-01,0.54
2019-12-01,1.22
2020-01-01,0.19
2020-02-01,0.17
2020-03-01,0.18
2020-04-01,-0.23
2020-05-01,-0.25
2020-06-01,0.3
2020-07-01,0.44
2020-08-01,0.36
2020-09-01,0.87
2020-10-01,0.89
2020-11-01,0.95
2020-12-01,1.46
2021-01-01,0.27
2021-02-01,0.82
2021-03-01,0.86
2021-04-01,0.38
2021-05-01,0.96
2021-06-01,0.6
2021-07-01,1.02
2021-08-01,0.88
2021-09-01,1.2
2021-10-01,1.16
2021-11-01,0.84
2021-12-01,0.73
2022-01-01,0.67
2022-02-01,1.0
2022-03-01,1.71
2022-04-01,1.04
2022-05-01,0.45
2022-06-01,0.62
2022-07-01,-0.6
2022-08-01,-0.31
2022-09-01,-0.32
2022-10-01,0.47
2022-11-01,0.38
2022-12-01,0.69
2023-01-01,0.46
2023-02-01,0.77
2023-03-01,0.64
2023-04-01,0.53
2023-05-01,0.36
2023-06-01,-0.1
2023-07-01,-0.09
2023-08-01,0.2
2023-09-01,0.11
2023-10-01,0.12
2023-11-01,0.1
2023-12-01,0.55
2024-01-01,0.57
2024-02-01,0.81
2024-03-01,0.19
2024-04-01,0.37
2024-05-01,0.46
2024-06-01,0.25
2024-07-01,0.26
2024-08-01,-0.14
2024-09-01,0.48
2024-10-01,0.61
2024-11-01,0.33
2024-12-01,0.48
"""

# Configuração da Página
st.set_page_config(page_title="Calculadora Revisional Híbrida (Lei 14.905)", layout="wide")

# CSS Impressão
st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stHeader"] { display: none; }
    .stButton { display: none; }
    .block-container { padding-top: 20px; }
    footer { display: none; }
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Sistema Revisional Bancário - Híbrido")
st.markdown("**Regra:** TJMG + 1% até 30/08/2024 | IPCA + (Selic - IPCA) após 01/09/2024 (Lei 14.905/24)")
st.markdown("---")

# --- PROCESSAMENTO DOS DADOS ANTIGOS ---
@st.cache_data
def carregar_tabela_tjmg():
    try:
        df = pd.read_csv(io.StringIO(CSV_TJMG))
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Indice'] = pd.to_numeric(df['Indice'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Data']).sort_values('Data')
        df['periodo'] = df['Data'].dt.to_period('M')
        # Fator Acumulado
        df['Multiplicador'] = 1 + (df['Indice'] / 100)
        df['Fator_Acumulado'] = df['Multiplicador'].cumprod()
        return df
    except:
        return pd.DataFrame()

df_tjmg = carregar_tabela_tjmg()

# --- FUNÇÃO CORREÇÃO TJMG (Até data de corte) ---
def calcular_fator_tjmg_parcial(data_venc, data_corte_limite):
    """Calcula fator acumulado TJMG do Vencimento até 30/08/2024"""
    if df_tjmg.empty: return 1.0
    
    p_venc = pd.to_datetime(data_venc).to_period('M')
    p_corte = pd.to_datetime(data_corte_limite).to_period('M')
    
    # Se vencimento é posterior ao corte, não aplica TJMG
    if p_venc > p_corte:
        return 1.0
        
    # Busca Fator na data de Corte (Agosto/24 ou anterior)
    linha_corte = df_tjmg[df_tjmg['periodo'] == p_corte]
    if linha_corte.empty:
        # Pega o mais próximo se a tabela acabar antes
        fator_fim = df_tjmg['Fator_Acumulado'].iloc[-1]
    else:
        fator_fim = linha_corte['Fator_Acumulado'].iloc[0]
        
    # Busca Fator Inicial (Mês anterior ao vencimento)
    p_anterior = p_venc - 1
    linha_inicial = df_tjmg[df_tjmg['periodo'] == p_anterior]
    
    if linha_inicial.empty:
        # Lógica de fallback
        linha_venc = df_tjmg[df_tjmg['periodo'] == p_venc]
        if not linha_venc.empty:
            fator_venc = linha_venc['Fator_Acumulado'].iloc[0]
            taxa_venc = linha_venc['Multiplicador'].iloc[0]
            fator_inicio = fator_venc / taxa_venc
        else:
            fator_inicio = 1.0
    else:
        fator_inicio = linha_inicial['Fator_Acumulado'].iloc[0]
        
    return fator_fim / fator_inicio

# --- FUNÇÕES FINANCEIRAS BÁSICAS ---
def calcular_pmt_mensal(principal, taxa_mensal_pct, meses):
    taxa = taxa_mensal_pct / 100
    if taxa == 0: return principal / meses
    return principal * (taxa * (1 + taxa)**meses) / ((1 + taxa)**meses - 1)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# --- INTERFACE LATERAL ---
st.sidebar.header("1. Contrato")
valor_emprestimo = st.sidebar.number_input("Valor Empréstimo (R$)", 50000.0)
prazo_meses = st.sidebar.number_input("Prazo (meses)", 48)
data_inicio = st.sidebar.date_input("Início Contrato", date(2022, 1, 15), format="DD/MM/YYYY")
valor_parcela_real = st.sidebar.number_input("Parcela Cobrada (R$)", 1800.0)

st.sidebar.header("2. Decisão Judicial")
taxa_judicial_mensal = st.sidebar.number_input("Nova Taxa Juros (Mensal %)", 1.5, format="%.2f")
data_citacao = st.sidebar.date_input("Data Citação", date(2023, 6, 1), format="DD/MM/YYYY")
data_calculo = st.sidebar.date_input("Data Base Cálculo", date.today(), format="DD/MM/YYYY")

# Data de Corte da Nova Lei
DATA_CORTE = date(2024, 8, 30)

st.sidebar.markdown("---")

# --- ABA DE ÍNDICES NOVOS (EDITÁVEL) ---
st.subheader("Configuração dos Índices Pós-Lei (Set/24 em diante)")
st.info("Abaixo estão os índices de IPCA e Selic Mensal a partir de 09/2024. Você pode editar ou adicionar meses futuros.")

# Dados iniciais conhecidos (Set/Out/Nov 2024)
dados_novos_init = [
    {"Mes": "2024-09-01", "IPCA (%)": 0.44, "Selic Meta (%)": 0.84},
    {"Mes": "2024-10-01", "IPCA (%)": 0.56, "Selic Meta (%)": 0.93},
    {"Mes": "2024-11-01", "IPCA (%)": 0.39, "Selic Meta (%)": 0.79},
    {"Mes": "2024-12-01", "IPCA (%)": 0.00, "Selic Meta (%)": 0.00},
    {"Mes": "2025-01-01", "IPCA (%)": 0.00, "Selic Meta (%)": 0.00},
]

df_novos_indices_input = st.data_editor(
    pd.DataFrame(dados_novos_init), 
    num_rows="dynamic",
    column_config={
        "Mes": st.column_config.DateColumn("Mês Ref.", format="MM/YYYY"),
        "IPCA (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Selic Meta (%)": st.column_config.NumberColumn(format="%.2f%%")
    },
    use_container_width=True
)

# Processar tabela nova
df_novos_indices_input['Mes'] = pd.to_datetime(df_novos_indices_input['Mes'])
df_novos_indices_input['periodo'] = df_novos_indices_input['Mes'].dt.to_period('M')

# --- LÓGICA DE CÁLCULO MISTA ---
def calcular_fator_ipca_pos(data_inicio_novo, data_fim_calculo):
    """Calcula fator acumulado IPCA da tabela nova"""
    if data_inicio_novo > data_fim_calculo: return 1.0
    
    p_ini = pd.to_datetime(data_inicio_novo).to_period('M')
    p_fim = pd.to_datetime(data_fim_calculo).to_period('M')
    
    df_filtrado = df_novos_indices_input[
        (df_novos_indices_input['periodo'] >= p_ini) & 
        (df_novos_indices_input['periodo'] <= p_fim)
    ]
    
    fator = 1.0
    for idx, row in df_filtrado.iterrows():
        fator *= (1 + row['IPCA (%)'] / 100)
    return fator

def calcular_juros_lei_nova(valor_corrigido_ipca, data_inicio_novo, data_fim_calculo):
    """
    Calcula juros (Selic - IPCA) acumulados mês a mês.
    Aplica-se sobre o valor atualizado mês a mês (mas aqui simplificaremos
    somando as taxas mensais ao saldo já corrigido, prática comum).
    Lei: Juro = Selic - IPCA. Se der negativo, juro é zero.
    """
    if data_inicio_novo > data_fim_calculo: return 0.0
    
    p_ini = pd.to_datetime(data_inicio_novo).to_period('M')
    p_fim = pd.to_datetime(data_fim_calculo).to_period('M')
    
    df_filtrado = df_novos_indices_input[
        (df_novos_indices_input['periodo'] >= p_ini) & 
        (df_novos_indices_input['periodo'] <= p_fim)
    ]
    
    juros_acumulados = 0.0
    
    # OBS: O cálculo exato seria aplicar a taxa composta dia a dia ou mês a mês.
    # Em juízo, simplifica-se somando as taxas mensais efetivas de juros reais.
    for idx, row in df_filtrado.iterrows():
        selic = row['Selic Meta (%)']
        ipca = row['IPCA (%)']
        juro_real = max(0, selic - ipca)
        juros_acumulados += juro_real
        
    # Retorna valor monetário aproximado (Taxa Acumulada * Valor Atualizado)
    return valor_corrigido_ipca * (juros_acumulados / 100)


if st.button("Calcular Revisional (Híbrido)"):
    
    parcela_revisada = calcular_pmt_mensal(valor_emprestimo, taxa_judicial_mensal, prazo_meses)
    diferenca_base = valor_parcela_real - parcela_revisada
    
    st.divider()
    st.subheader(f"1. Diferença Base: R$ {diferenca_base:,.2f} / mês")
    
    dados = []
    totais = {"Principal": 0, "CM": 0, "Juros": 0}
    
    alerta_data = False

    for i in range(1, prazo_meses + 1):
        vencimento = data_inicio + relativedelta(months=i)
        
        if vencimento > data_calculo: break
        
        # --- ETAPA 1: ATÉ 30/08/2024 ---
        if vencimento <= DATA_CORTE:
            # Correção TJMG do Vencimento até Corte
            fator_tjmg = calcular_fator_tjmg_parcial(vencimento, DATA_CORTE)
            valor_em_agosto = diferenca_base * fator_tjmg
            
            # Juros 1% a.m. (Simples) do Vencimento/Citação até Corte
            inicio_juros_antigo = max(vencimento, data_citacao)
            
            if inicio_juros_antigo < DATA_CORTE:
                # Contagem de meses (pro rata dias / 30)
                dias_antigos = (DATA_CORTE - inicio_juros_antigo).days
                juros_antigo_val = valor_em_agosto * (dias_antigos / 30) * 0.01
            else:
                juros_antigo_val = 0.0
                
            # Saldo em 30/08 (Sem capitalizar juros, carregamos separados)
            saldo_principal_agosto = valor_em_agosto
            saldo_juros_agosto = juros_antigo_val
            
            # --- ETAPA 2: DE 01/09/2024 ATÉ HOJE ---
            if data_calculo > DATA_CORTE:
                # Correção IPCA sobre o Principal de Agosto
                fator_ipca = calcular_fator_ipca_pos(date(2024, 9, 1), data_calculo)
                valor_final_principal = saldo_principal_agosto * fator_ipca
                
                # Juros Nova Lei sobre o Principal Atualizado IPCA
                # Data inicio juros novos: 01/09/2024
                juros_novos_val = calcular_juros_lei_nova(valor_final_principal, date(2024, 9, 1), data_calculo)
                
                # Total Juros = Juros Antigos (nominais) + Juros Novos
                total_juros_linha = saldo_juros_agosto + juros_novos_val
            else:
                # Cálculo parou antes da lei nova
                valor_final_principal = saldo_principal_agosto
                total_juros_linha = saldo_juros_agosto
                fator_ipca = 1.0
                
            memoria = f"TJMG até 08/24 ({fator_tjmg:.4f}) + IPCA pós"

        else:
            # --- PARCELA VENCEU JÁ NA VIGÊNCIA DA LEI NOVA (PÓS SET/24) ---
            # Não tem TJMG nem 1%. Só IPCA e Selic-IPCA
            fator_tjmg = 1.0
            
            # Correção IPCA do Vencimento até Hoje
            fator_ipca = calcular_fator_ipca_pos(vencimento, data_calculo)
            valor_final_principal = diferenca_base * fator_ipca
            
            # Juros Nova Lei (Citação ou Vencimento)
            inicio_juros = max(vencimento, data_citacao)
            if inicio_juros < data_calculo:
                juros_novos_val = calcular_juros_lei_nova(valor_final_principal, inicio_juros, data_calculo)
            else:
                juros_novos_val = 0.0
                
            total_juros_linha = juros_novos_val
            memoria = "Lei Nova (IPCA + Juro Real)"

        total_linha = valor_final_principal + total_juros_linha
        
        dados.append({
            "Vencimento": vencimento.strftime("%d/%m/%Y"),
            "Original": diferenca_base,
            "Regra": memoria,
            "Principal Atualizado": valor_final_principal,
            "Total Juros": total_juros_linha,
            "Total Devido": total_linha
        })
        
        totais["Principal"] += diferenca_base
        totais["CM"] += (valor_final_principal - diferenca_base)
        totais["Juros"] += total_juros_linha

    # --- RESULTADOS ---
    df_res = pd.DataFrame(dados)
    
    if not df_res.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Principal Original", f"R$ {totais['Principal']:,.2f}")
        col2.metric("Correção (TJMG+IPCA)", f"R$ {totais['CM']:,.2f}")
        col3.metric("Juros (1% + Lei Nova)", f"R$ {totais['Juros']:,.2f}")
        
        total_geral = totais['Principal'] + totais['CM'] + totais['Juros']
        col4.metric("TOTAL FINAL", f"R$ {total_geral:,.2f}", delta="Execução")
        
        st.dataframe(df_res.style.format({
            "Original": "R$ {:.2f}",
            "Principal Atualizado": "R$ {:.2f}",
            "Total Juros": "R$ {:.2f}",
            "Total Devido": "R$ {:.2f}"
        }), use_container_width=True)
        
        # Download
        csv = convert_df(df_res)
        st.download_button("💾 Baixar Relatório (CSV)", csv, "calculo_lei_nova.csv", "text/csv")
    else:
        st.warning("Nenhuma parcela vencida no período selecionado.")
