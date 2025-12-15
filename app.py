import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# --- DADOS DA TABELA TJ-MG (EMBUTIDOS) ---
# Extraídos do arquivo fornecido pelo usuário.
# Contém índices mensais (%) de Jan/2016 a Dez/2025.
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
2025-01-01,0.0
2025-02-01,1.48
2025-03-01,0.51
2025-04-01,0.48
2025-05-01,0.35
2025-06-01,0.23
2025-07-01,0.21
2025-08-01,-0.21
2025-09-01,0.52
2025-10-01,0.03
2025-11-01,0.03
"""

# Configuração da Página
st.set_page_config(page_title="Calculadora Revisional TJ-MG", layout="wide")

st.title("⚖️ Sistema de Cálculo Revisional - TJMG")
st.markdown("**Índices Oficiais Carregados (2016-2025)**")
st.markdown("---")

# --- PROCESSAMENTO DOS DADOS EMBUTIDOS ---
@st.cache_data
def carregar_tabela_interna():
    """Lê a string CSV, trata datas e calcula fatores acumulados."""
    try:
        df = pd.read_csv(io.StringIO(CSV_TJMG))
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df['Indice'] = pd.to_numeric(df['Indice'], errors='coerce').fillna(0)
        
        # Eliminar linhas sem data válida
        df = df.dropna(subset=['Data']).sort_values('Data')
        
        # Criar coluna Periodo (Mês/Ano) para busca
        df['periodo'] = df['Data'].dt.to_period('M')
        
        # CALCULAR FATOR ACUMULADO
        # Fórmula: Fator_Atual = Fator_Anterior * (1 + Indice/100)
        # Começamos com fator 1.0 antes do primeiro registro
        df['Multiplicador'] = 1 + (df['Indice'] / 100)
        df['Fator_Acumulado'] = df['Multiplicador'].cumprod()
        
        # Normalizar para facilitar leitura (Opcional, mas bom para debug)
        # Vamos inserir um ponto base "fictício" antes do início para cálculos seguros
        data_minima = df['Data'].min()
        mes_anterior = data_minima - relativedelta(months=1)
        
        # Mas para a lógica de busca, basta usarmos o fator do mês.
        return df
    except Exception as e:
        st.error(f"Erro interno nos dados: {e}")
        return pd.DataFrame()

df_indices = carregar_tabela_interna()

def buscar_fator_correcao(df, data_vencimento, data_calculo):
    """
    Retorna o coeficiente para multiplicar o valor original.
    Lógica: Valor_Atualizado = Valor_Orig * (Fator_DataCalculo / Fator_MesAnteriorAoVencimento)
    Isso aplica a inflação de TODO o período, incluindo o mês do vencimento.
    """
    if df.empty: return 1.0
    
    p_venc = pd.to_datetime(data_vencimento).to_period('M')
    p_calc = pd.to_datetime(data_calculo).to_period('M')
    
    # Se data cálculo < vencimento, não corrige
    if p_calc < p_venc:
        return 1.0

    # Buscar Fator Final (Data do Cálculo)
    linha_final = df[df['periodo'] == p_calc]
    if linha_final.empty:
        # Tenta pegar o último disponível se a data for futura
        fator_fim = df['Fator_Acumulado'].iloc[-1]
    else:
        fator_fim = linha_final['Fator_Acumulado'].iloc[0]
        
    # Buscar Fator Inicial (Mês ANTERIOR ao vencimento)
    # Ex: Venceu em Jan/23. Queremos que o índice de Jan/23 incida.
    # Então dividimos pelo fator acumulado até Dez/22.
    p_anterior = p_venc - 1
    linha_inicial = df[df['periodo'] == p_anterior]
    
    if linha_inicial.empty:
        # Se o mês anterior não existe na tabela (tabela começa depois),
        # Verificamos se é o primeiro mês da tabela.
        # Se for muito antigo, usa o primeiro fator disponível e avisa (ou assume 1 se for o início absoluto)
        # Para simplificar: se não achar o anterior, assume fator base 1.0 (divisão pelo fator inicial do acumulado ajustado)
        primeiro_periodo = df['periodo'].iloc[0]
        if p_anterior < primeiro_periodo:
             # Vencimento antes da tabela: usa o fator mais antigo como divisor? 
             # Não, isso ignoraria inflação antiga. Mas assumindo que a tabela cobre o contrato:
             # Vamos pegar o fator do próprio mês e retirar o índice dele? 
             # Melhor: Dividir pelo fator base inicial da série (que seria 1 / (1+i_primeiro)).
             # Simplificação: Usar fator do próprio mês de vencimento dividindo por (1+i_mes).
             linha_venc = df[df['periodo'] == p_venc]
             if not linha_venc.empty:
                 fator_venc = linha_venc['Fator_Acumulado'].iloc[0]
                 taxa_venc = linha_venc['Multiplicador'].iloc[0]
                 fator_inicio = fator_venc / taxa_venc
             else:
                 fator_inicio = 1.0 # Fallback
    else:
        fator_inicio = linha_inicial['Fator_Acumulado'].iloc[0]
        
    return fator_fim / fator_inicio

# --- INTERFACE ---

st.sidebar.header("1. Dados do Contrato")
valor_emprestimo = st.sidebar.number_input("Valor do Empréstimo (R$)", min_value=1000.0, value=50000.0, step=100.0)
prazo_meses = st.sidebar.number_input("Prazo (meses)", min_value=1, value=48, step=1)
data_inicio = st.sidebar.date_input("Data Início do Contrato", value=date(2022, 1, 15))
valor_parcela_real = st.sidebar.number_input("Valor da Parcela Cobrada (R$)", min_value=0.0, value=1800.0, format="%.2f")

st.sidebar.header("2. Parâmetros da Decisão")
taxa_judicial_anual = st.sidebar.number_input("Nova Taxa de Juros (Anual %)", value=12.0)
data_citacao = st.sidebar.date_input("Data da Citação", value=date(2023, 6, 1))
data_calculo = st.sidebar.date_input("Data Base do Cálculo", value=date.today())

# Funções auxiliares financeiras
def calcular_pmt(principal, taxa_anual, meses):
    taxa_mensal = (1 + taxa_anual/100)**(1/12) - 1
    if taxa_mensal == 0: return principal / meses
    pmt = principal * (taxa_mensal * (1 + taxa_mensal)**meses) / ((1 + taxa_mensal)**meses - 1)
    return pmt

def calcular_juros_mora(valor_atualizado, data_vencimento, data_citacao, data_hoje):
    inicio_juros = max(data_vencimento, data_citacao)
    if inicio_juros >= data_hoje: return 0.0
    dias = (data_hoje - inicio_juros).days
    return valor_atualizado * (dias / 30) * 0.01 # 1% a.m pro rata die (cível padrão)

if st.button("Calcular Revisional"):
    
    # Cálculos Iniciais
    parcela_revisada = calcular_pmt(valor_emprestimo, taxa_judicial_anual, prazo_meses)
    diferenca_mensal_base = valor_parcela_real - parcela_revisada
    
    st.subheader("Resumo das Parcelas")
    c1, c2, c3 = st.columns(3)
    c1.metric("Parcela Paga", f"R$ {valor_parcela_real:,.2f}")
    c2.metric("Parcela Recalculada", f"R$ {parcela_revisada:,.2f}")
    c3.metric("Diferença Inicial (S/ Correção)", f"R$ {diferenca_mensal_base:,.2f}")

    # Processamento Mês a Mês
    dados = []
    total_indebito_hist = 0
    total_corrigido = 0
    total_juros = 0
    
    # Aviso se datas estiverem fora da tabela
    if data_inicio < df_indices['Data'].min().date():
        st.warning("⚠️ O contrato começa antes de 2016. A correção monetária das primeiras parcelas pode estar incompleta (Tabela inicia em Jan/2016).")

    for i in range(1, prazo_meses + 1):
        vencimento = data_inicio + relativedelta(months=i)
        
        # Se parcela vence no futuro (após data cálculo), não entra no cálculo de ressarcimento
        if vencimento > data_calculo:
            break
            
        # 1. Correção Monetária
        fator = buscar_fator_correcao(df_indices, vencimento, data_calculo)
        valor_atualizado = diferenca_mensal_base * fator
        
        # 2. Juros de Mora (sobre o valor ATUALIZADO)
        valor_juros = calcular_juros_mora(valor_atualizado, vencimento, data_citacao, data_calculo)
        
        total_linha = valor_atualizado + valor_juros
        
        dados.append({
            "Nº": i,
            "Vencimento": vencimento.strftime("%d/%m/%Y"),
            "Diferença Base": diferenca_mensal_base,
            "Coef. CM": fator,
            "Valor Atualizado": valor_atualizado,
            "Juros Mora": valor_juros,
            "Total": total_linha
        })
        
        total_indebito_hist += diferenca_mensal_base
        total_corrigido += (valor_atualizado - diferenca_mensal_base)
        total_juros += valor_juros

    # Exibição
    df_res = pd.DataFrame(dados)
    
    if not df_res.empty:
        st.markdown("### 📋 Memória de Cálculo Detalhada")
        st.dataframe(df_res.style.format({
            "Diferença Base": "R$ {:.2f}",
            "Coef. CM": "{:.6f}",
            "Valor Atualizado": "R$ {:.2f}",
            "Juros Mora": "R$ {:.2f}",
            "Total": "R$ {:.2f}"
        }), use_container_width=True)
        
        st.divider()
        st.markdown("### 🏛️ Resultado Final da Execução")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        col_f1.metric("Principal Histórico", f"R$ {total_indebito_hist:,.2f}", help="Soma simples das diferenças sem correção")
        col_f2.metric("Correção Monetária", f"R$ {total_corrigido:,.2f}", help="Apenas o valor agregado pela inflação (TJMG)")
        col_f3.metric("Juros de Mora (1% a.m.)", f"R$ {total_juros:,.2f}", help="Desde a citação ou vencimento")
        
        total_final = total_indebito_hist + total_corrigido + total_juros
        col_f4.metric("TOTAL A EXECUTAR", f"R$ {total_final:,.2f}", delta="Crédito Cliente")
    else:
        st.info("Nenhuma parcela vencida encontrada para o cálculo.")
