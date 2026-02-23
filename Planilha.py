if st.sidebar.button("Calcular Execução", type="primary"):
    
    if nome_cliente:
        st.subheader(f"Cliente: {nome_cliente}")
        
    parcela_revisada = calcular_pmt_mensal(valor_emprestimo, taxa_judicial_mensal, prazo_meses)
    diferenca_base = valor_parcela_real - parcela_revisada
    
    colA, colB, colC = st.columns(3)
    colA.metric("Parcela do Contrato", f"R$ {valor_parcela_real:,.2f}")
    colB.metric("Parcela Judicial (Devida)", f"R$ {parcela_revisada:,.2f}")
    colC.metric("Indébito Mensal (Diferença)", f"R$ {diferenca_base:,.2f}")
    
    st.divider()
    
    dados = []
    totais = {"Principal": 0, "CM": 0, "Juros": 0}

    for i in range(1, prazo_meses + 1):
        
        vencimento = data_inicio + relativedelta(months=(i-1))
        
        if vencimento > data_calculo: break

        # --- EXCLUSÃO SUTIL DE PARCELAS (ZERADAS) ---
        if i in parcelas_excluidas:
            dados.append({
                "Nº": i,
                "Vencimento": vencimento.strftime("%d/%m/%Y"),
                "Original": 0.00,
                "Fator TJMG": np.nan,  # Fica vazio na tabela
                "Fator IPCA": np.nan,  # Fica vazio na tabela
                "Principal Atualizado": 0.00,
                "Juros Acumulados": 0.00,
                "Total Devido": 0.00
            })
            continue 
            
        # --- ETAPA 1: ATÉ 30/08/2024 ---
        if vencimento <= DATA_CORTE:
            fator_tjmg = calcular_fator_tjmg_parcial(vencimento, DATA_CORTE)
            valor_em_agosto = diferenca_base * fator_tjmg
            
            inicio_juros_antigo = max(vencimento, data_citacao)
            
            if inicio_juros_antigo < DATA_CORTE:
                dias_antigos = (DATA_CORTE - inicio_juros_antigo).days
                juros_antigo_val = valor_em_agosto * (dias_antigos / 30) * 0.01
            else:
                juros_antigo_val = 0.0
                
            saldo_principal_agosto = valor_em_agosto
            saldo_juros_agosto = juros_antigo_val
            
            # --- ETAPA 2: DE 01/09/2024 ATÉ HOJE ---
            if data_calculo > DATA_CORTE:
                fator_ipca = calcular_fator_ipca_pos(date(2024, 9, 1), data_calculo)
                valor_final_principal = saldo_principal_agosto * fator_ipca
                
                juros_novos_val = calcular_juros_lei_nova(valor_final_principal, date(2024, 9, 1), data_calculo)
                total_juros_linha = saldo_juros_agosto + juros_novos_val
            else:
                valor_final_principal = saldo_principal_agosto
                total_juros_linha = saldo_juros_agosto
                fator_ipca = 1.0
                
        else:
            # --- PARCELA PÓS-LEI ---
            fator_tjmg = 1.0
            
            fator_ipca = calcular_fator_ipca_pos(vencimento, data_calculo)
            valor_final_principal = diferenca_base * fator_ipca
            
            inicio_juros = max(vencimento, data_citacao)
            if inicio_juros < data_calculo:
                juros_novos_val = calcular_juros_lei_nova(valor_final_principal, inicio_juros, data_calculo)
            else:
                juros_novos_val = 0.0
                
            total_juros_linha = juros_novos_val

        total_linha = valor_final_principal + total_juros_linha
        
        # Adiciona a linha detalhada na tabela
        dados.append({
            "Nº": i,
            "Vencimento": vencimento.strftime("%d/%m/%Y"),
            "Original": diferenca_base,
            "Fator TJMG": fator_tjmg,
            "Fator IPCA": fator_ipca,
            "Principal Atualizado": valor_final_principal,
            "Juros Acumulados": total_juros_linha,
            "Total Devido": total_linha
        })
        
        totais["Principal"] += diferenca_base
        totais["CM"] += (valor_final_principal - diferenca_base)
        totais["Juros"] += total_juros_linha

    # --- RESULTADOS ---
    df_res = pd.DataFrame(dados)
    
    if not df_res.empty:
        st.markdown("### Memória de Cálculo Parcelada")
        
        # Utilizamos st.table e limitamos a 4 casas decimais os fatores
        st.table(df_res.style.format({
            "Original": "R$ {:.2f}",
            "Fator TJMG": "{:.4f}",
            "Fator IPCA": "{:.4f}",
            "Principal Atualizado": "R$ {:.2f}",
            "Juros Acumulados": "R$ {:.2f}",
            "Total Devido": "R$ {:.2f}"
        }, na_rep="-")) # na_rep="-" coloca um traço nas parcelas excluídas
        
        st.divider()
        st.markdown("### 🏛️ Resumo da Condenação a Executar")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Principal Original", f"R$ {totais['Principal']:,.2f}")
        col2.metric("Correção (TJMG+IPCA)", f"R$ {totais['CM']:,.2f}")
        col3.metric("Juros (1% + Lei Nova)", f"R$ {totais['Juros']:,.2f}")
        
        total_geral = totais['Principal'] + totais['CM'] + totais['Juros']
        col4.metric("TOTAL FINAL", f"R$ {total_geral:,.2f}", delta="Crédito do Autor")
        
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
