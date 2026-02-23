import streamlit as st
import pandas as pd
import numpy as np
import io
import streamlit.components.v1 as components
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
st.set_page_config(page_title="Calculadora Revisional Híbrida", layout="wide")

# CSS Impressão e Estilos Gerais
st.markdown("""
<style>
@media print {
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .stButton, .btn-imprimir, .stDownloadButton { display: none !important; }
    .block-container { padding-top: 0px !important; margin-top: 0px !important; }
    table { font-size: 10px !important; page-break-inside: auto; }
    tr { page-break-inside: avoid; page-break-after: auto; }
}
.info-cabecalho {
    background-color: #f8f9fa; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 5px; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Relatório de Cálculo Revisional")
st.markdown("**Regra:** TJMG + 1% a.m. até 29/08/2024 | IPCA + (Selic - IPCA) após 30/08/2024 (Lei 14.905/24)")
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
        df['Multiplicador'] = 1 + (df['Indice'] / 100)
        df['Fator_Acumulado'] = df['Multiplicador'].cumprod()
        return df
    except:
        return pd.DataFrame()

df_tjmg = carregar_tabela_tjmg()

def calcular_fator_tjmg_parcial(data_venc, data_corte_limite):
    if df_tjmg.empty: return 1.0
    p_venc = pd.to_datetime(data_venc).to_period('M')
    p_corte = pd.to_datetime(data_corte_limite).to_period('M')
    if p_venc > p_corte: return 1.0
        
    linha_corte = df_tjmg[df_tjmg['periodo'] == p_corte]
    if linha_corte.empty:
        fator_fim = df_tjmg['Fator_Acumulado'].iloc[-1]
    else:
        fator_fim = linha_corte['Fator_Acumulado'].iloc[0]
        
    p_anterior = p_venc - 1
    linha_inicial = df_tjmg[df_tjmg['periodo'] == p_anterior]
    
    if linha_inicial.empty:
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
def calcular_pmt_mensal(principal, taxa_mensal_pct, meses, antecipada=False):
    taxa = taxa_mensal_pct / 100
    if taxa == 0: return principal / meses
    
    # Cálculo da Price Padrão (Postecipada)
    pmt = principal * (taxa * (1 + taxa)**meses) / ((1 + taxa)**meses - 1)
    
    # Ajuste para Price com Entrada (Antecipada)
    if antecipada:
        pmt = pmt / (1 + taxa)
        
    return pmt

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# --- INTERFACE LATERAL ---
st.sidebar.header("📋 Dados do Processo (Opcional)")
nome_cliente = st.sidebar.text_input("Nome do Cliente", value="")

st.sidebar.header("1. Contrato")
valor_emprestimo = st.sidebar.number_input("Valor Empréstimo (R$)", min_value=0.0, value=3921.41, step=100.0)
prazo_meses = st.sidebar.number_input("Prazo (meses)", min_value=1, value=45, step=1)
taxa_contrato_mensal = st.sidebar.number_input("Taxa Contrato (Mensal %)", min_value=0.0, value=5.99, step=0.1, format="%.2f")

# Checkbox para identificar se a parcela 1 foi paga no ato
pagamento_antecipado = st.sidebar.checkbox("1ª Parcela paga no ato (Entrada / Antecipada)", value=True)

data_inicio = st.sidebar.date_input("Início Contrato (Venc. 1ª Parcela)", date(2020, 7, 16), format="DD/MM/YYYY")
valor_parcela_real = st.sidebar.number_input("Parcela Cobrada (R$)", min_value=0.0, value=243.94, step=10.0, format="%.2f")

st.sidebar.header("2. Decisão Judicial")
taxa_judicial_mensal = st.sidebar.number_input("Nova Taxa Juros (Mensal %)", min_value=0.0, value=4.59, step=0.1, format="%.2f")
data_citacao = st.sidebar.date_input("Data Citação", date(2021, 5, 10), format="DD/MM/YYYY")
data_calculo = st.sidebar.date_input("Data Base Cálculo", date.today(), format="DD/MM/YYYY")

st.sidebar.header("3. Estratégia Processual")
excluir_str = st.sidebar.text_input("Parcelas a Excluir (Ex: 44, 45)", value="44, 45")

parcelas_excluidas = []
if excluir_str:
    try:
        parcelas_excluidas = [int(x.strip()) for x in excluir_str.split(",") if x.strip().isdigit()]
    except:
        st.sidebar.error("Erro ao ler parcelas excluídas. Use apenas números separados por vírgula.")

DATA_CORTE = date(2024, 8, 29)

st.sidebar.markdown("---")

# --- ABA DE ÍNDICES NOVOS (IPCA + SELIC) ---
with st.sidebar.expander("Índices Pós-Lei (Set/24 em diante)"):
    st.info("Valores Oficiais carregados até Jan/2026.")
    dados_novos_init = [
        {"Mes": date(2024, 9, 1),  "IPCA (%)": 0.44, "Selic Meta (%)": 0.84},
        {"Mes": date(2024, 10, 1), "IPCA (%)": 0.56, "Selic Meta (%)": 0.93},
        {"Mes": date(2024, 11, 1), "IPCA (%)": 0.39, "Selic Meta (%)": 0.79},
        {"Mes": date(2024, 12, 1), "IPCA (%)": 0.52, "Selic Meta (%)": 0.93},
        {"Mes": date(2025, 1, 1),  "IPCA (%)": 0.16, "Selic Meta (%)": 1.01},
        {"Mes": date(2025, 2, 1),  "IPCA (%)": 1.31, "Selic Meta (%)": 0.99},
        {"Mes": date(2025, 3, 1),  "IPCA (%)": 0.56, "Selic Meta (%)": 0.96},
        {"Mes": date(2025, 4, 1),  "IPCA (%)": 0.43, "Selic Meta (%)": 1.06},
        {"Mes": date(2025, 5, 1),  "IPCA (%)": 0.26, "Selic Meta (%)": 1.14},
        {"Mes": date(2025, 6, 1),  "IPCA (%)": 0.24, "Selic Meta (%)": 1.10},
        {"Mes": date(2025, 7, 1),  "IPCA (%)": 0.26, "Selic Meta (%)": 1.28},
        {"Mes": date(2025, 8, 1),  "IPCA (%)": -0.11,"Selic Meta (%)": 1.16},
        {"Mes": date(2025, 9, 1),  "IPCA (%)": 0.48, "Selic Meta (%)": 1.22},
        {"Mes": date(2025, 10, 1), "IPCA (%)": 0.09, "Selic Meta (%)": 1.28},
        {"Mes": date(2025, 11, 1), "IPCA (%)": 0.18, "Selic Meta (%)": 1.05},
        {"Mes": date(2025, 12, 1), "IPCA (%)": 0.33, "Selic Meta (%)": 1.22},
        {"Mes": date(2026, 1, 1),  "IPCA (%)": 0.33, "Selic Meta (%)": 1.16},
    ]
    df_init = pd.DataFrame(dados_novos_init)
    df_init["Mes"] = pd.to_datetime(df_init["Mes"])
    
    df_novos_indices_input = st.data_editor(
        df_init, 
        num_rows="dynamic",
        column_config={
            "Mes": st.column_config.DateColumn("Mês Ref.", format="MM/YYYY", step=1),
            "IPCA (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Selic Meta (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        use_container_width=True
    )

df_novos_indices_input['periodo'] = df_novos_indices_input['Mes'].dt.to_period('M')

def calcular_fator_ipca_pos(data_inicio_novo, data_fim_calculo):
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
    if data_inicio_novo > data_fim_calculo: return 0.0, 0.0, 0
    p_ini = pd.to_datetime(data_inicio_novo).to_period('M')
    p_fim = pd.to_datetime(data_fim_calculo).to_period('M')
    df_filtrado = df_novos_indices_input[
        (df_novos_indices_input['periodo'] >= p_ini) & 
        (df_novos_indices_input['periodo'] <= p_fim)
    ]
    juros_acumulados = 0.0
    meses_contados = 0
    for idx, row in df_filtrado.iterrows():
        selic = row['Selic Meta (%)']
        ipca = row['IPCA (%)']
        juro_real = max(0, selic - ipca)
        juros_acumulados += juro_real
        meses_contados += 1
    return valor_corrigido_ipca * (juros_acumulados / 100), juros_acumulados, meses_contados


# --- PROCESSAMENTO PRINCIPAL ---
if st.sidebar.button("Calcular Execução", type="primary"):
    
    st.markdown("### 📄 Parâmetros da Liquidação")
    
    if nome_cliente:
        st.write(f"**Cliente:** {nome_cliente}")
        
    st.markdown(f"""
    <div class="info-cabecalho">
        <strong>Valor Financiado:</strong> R$ {valor_emprestimo:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 
        <strong>Prazo do Contrato:</strong> {prazo_meses} meses &nbsp;&nbsp;|&nbsp;&nbsp; 
        <strong>Data da Citação:</strong> {data_citacao.strftime('%d/%m/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; 
        <strong>Atualizado até:</strong> {data_calculo.strftime('%d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)
        
    parcela_revisada = calcular_pmt_mensal(valor_emprestimo, taxa_judicial_mensal, prazo_meses, antecipada=pagamento_antecipado)
    diferenca_base = valor_parcela_real - parcela_revisada
    
    colA, colB, colC = st.columns(3)
    colA.metric(f"Parcela do Contrato ({taxa_contrato_mensal:.2f}% a.m.)", f"R$ {valor_parcela_real:,.2f}")
    colB.metric(f"Parcela Judicial ({taxa_judicial_mensal:.2f}% a.m.)", f"R$ {parcela_revisada:,.2f}")
    colC.metric("Indébito Mensal (Diferença)", f"R$ {diferenca_base:,.2f}")
    
    st.divider()
    
    dados = []
    totais = {"Principal": 0, "CM": 0, "Juros_1_pct": 0, "Juros_Selic": 0}

    for i in range(1, prazo_meses + 1):
        
        vencimento = data_inicio + relativedelta(months=(i-1))
        
        if vencimento > data_calculo: break

        # Dias totais da CM
        dias_cm = (data_calculo - vencimento).days
        info_tempo_cm = f"{dias_cm}d" if dias_cm > 0 else "0d"

        # --- EXCLUSÃO SUTIL DE PARCELAS (ZERADAS) ---
        if i in parcelas_excluidas:
            dados.append({
                "Nº": i,
                "Vencimento": vencimento.strftime("%d/%m/%Y"),
                "Original": 0.00,
                "Tempo CM (Dias)": "-",
                "Fator TJMG": "-",
                "Fator IPCA": "-",
                "Principal Atualizado": 0.00,
                "Taxa 1% (Dias)": "-",
                "Juros 1% a.m.": 0.00,
                "Taxa Selic (Meses)": "-",
                "Juros Lei 14.905": 0.00,
                "Total Devido": 0.00
            })
            continue 
            
        dias_tjmg = 0
        dias_ipca = 0
        
        dias_antigos = 0
        taxa_antiga_pct = 0.0
        juros_antigo_val = 0.0
        
        meses_novos = 0
        taxa_nova_pct = 0.0
        juros_novos_val = 0.0
        
        # --- ETAPA 1: ATÉ 30/08/2024 ---
        if vencimento <= DATA_CORTE:
            fator_tjmg = calcular_fator_tjmg_parcial(vencimento, DATA_CORTE)
            valor_em_agosto = diferenca_base * fator_tjmg
            
            if data_calculo <= DATA_CORTE:
                dias_tjmg = (data_calculo - vencimento).days
                dias_ipca = 0
            else:
                dias_tjmg = (DATA_CORTE - vencimento).days
                dias_ipca = (data_calculo - DATA_CORTE).days 
            
            inicio_juros_antigo = max(vencimento, data_citacao)
            
            if inicio_juros_antigo < DATA_CORTE:
                dias_antigos = (DATA_CORTE - inicio_juros_antigo).days
                taxa_antiga_pct = (dias_antigos / 30) * 1.0 
                juros_antigo_val = valor_em_agosto * (taxa_antiga_pct / 100)
                
            saldo_principal_agosto = valor_em_agosto
            
            # --- ETAPA 2: DE 01/09/2024 ATÉ HOJE ---
            if data_calculo > DATA_CORTE:
                fator_ipca = calcular_fator_ipca_pos(date(2024, 9, 1), data_calculo)
                valor_final_principal = saldo_principal_agosto * fator_ipca
                
                juros_novos_val, taxa_nova_pct, meses_novos = calcular_juros_lei_nova(valor_final_principal, date(2024, 9, 1), data_calculo)
            else:
                valor_final_principal = saldo_principal_agosto
                fator_ipca = 1.0
                
        else:
            # --- PARCELA PÓS-LEI ---
            fator_tjmg = 1.0
            dias_tjmg = 0
            dias_ipca = (data_calculo - vencimento).days
            
            fator_ipca = calcular_fator_ipca_pos(vencimento, data_calculo)
            valor_final_principal = diferenca_base * fator_ipca
            
            inicio_juros = max(vencimento, data_citacao)
            if inicio_juros < data_calculo:
                juros_novos_val, taxa_nova_pct, meses_novos = calcular_juros_lei_nova(valor_final_principal, inicio_juros, data_calculo)

        total_linha = valor_final_principal + juros_antigo_val + juros_novos_val
        
        str_fator_tjmg = f"{fator_tjmg:.4f} ({dias_tjmg}d)" if dias_tjmg > 0 else "-"
        str_fator_ipca = f"{fator_ipca:.4f} ({dias_ipca}d)" if dias_ipca > 0 else "-"
        
        info_mora_1 = f"{taxa_antiga_pct:.2f}% ({dias_antigos}d)" if dias_antigos > 0 else "-"
        info_mora_selic = f"{taxa_nova_pct:.2f}% ({meses_novos}m)" if meses_novos > 0 else "-"

        dados.append({
            "Nº": i,
            "Vencimento": vencimento.strftime("%d/%m/%Y"),
            "Original": diferenca_base,
            "Tempo CM (Dias)": info_tempo_cm,
            "Fator TJMG": str_fator_tjmg,
            "Fator IPCA": str_fator_ipca,
            "Principal Atualizado": valor_final_principal,
            "Taxa 1% (Dias)": info_mora_1,
            "Juros 1% a.m.": juros_antigo_val,
            "Taxa Selic (Meses)": info_mora_selic,
            "Juros Lei 14.905": juros_novos_val,
            "Total Devido": total_linha
        })
        
        totais["Principal"] += diferenca_base
        totais["CM"] += (valor_final_principal - diferenca_base)
        totais["Juros_1_pct"] += juros_antigo_val
        totais["Juros_Selic"] += juros_novos_val

    # --- RESULTADOS ---
    df_res = pd.DataFrame(dados)
    
    if not df_res.empty:
        st.markdown("### Memória de Cálculo Parcelada")
        
        st.table(df_res.style.format({
            "Original": "R$ {:.2f}",
            "Principal Atualizado": "R$ {:.2f}",
            "Juros 1% a.m.": "R$ {:.2f}",
            "Juros Lei 14.905": "R$ {:.2f}",
            "Total Devido": "R$ {:.2f}"
        }, na_rep="-")) 
        
        st.divider()
        st.markdown("### 🏛️ Resumo da Condenação a Executar")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Principal Original", f"R$ {totais['Principal']:,.2f}")
        col2.metric("Correção (TJMG+IPCA)", f"R$ {totais['CM']:,.2f}")
        col3.metric("Juros Mora (1% a.m.)", f"R$ {totais['Juros_1_pct']:,.2f}")
        col4.metric("Juros Lei 14.905", f"R$ {totais['Juros_Selic']:,.2f}")
        
        total_geral = totais['Principal'] + totais['CM'] + totais['Juros_1_pct'] + totais['Juros_Selic']
        col5.metric("TOTAL FINAL", f"R$ {total_geral:,.2f}", delta="Crédito do Autor")
        
        st.divider()
        
        # --- BOTÕES DE EXPORTAÇÃO E IMPRESSÃO ---
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            csv = convert_df(df_res)
            st.download_button("💾 Baixar Tabela (Excel/CSV)", csv, "calculo_judicial.csv", "text/csv", use_container_width=True)
            
        with col_btn2:
            html_botao = """
            <script>
            function imprimir() { window.parent.print(); }
            </script>
            <style>
            .btn-imprimir {
                background-color: #2e7d32; color: white; border: none; padding: 0.5rem 1rem;
                font-size: 16px; border-radius: 8px; cursor: pointer; font-weight: bold;
                text-align: center; width: 100%; font-family: 'Source Sans Pro', sans-serif; margin-top: 15px;
            }
            .btn-imprimir:hover { background-color: #1b5e20; }
            </style>
            <button onclick="imprimir()" class="btn-imprimir">🖨️ Imprimir Relatório (PDF)</button>
            """
            components.html(html_botao, height=70)
            
    else:
        st.warning("Nenhuma parcela vencida no período selecionado.")
