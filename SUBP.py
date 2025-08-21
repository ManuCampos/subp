# app.py

import streamlit as st
import os
import pandas as pd
import sys
import matplotlib.pyplot as plt

# Caminho do CSV considerando o executável
base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
csv_path = os.path.join(base_path, "resultados.csv")

# Carregando o CSV com tratamento de erros
try:
    df = pd.read_csv(csv_path, sep=";")
except FileNotFoundError:
    st.error("Arquivo 'resultados.csv' não encontrado.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("O arquivo 'resultados.csv' está vazio.")
    st.stop()
except pd.errors.ParserError:
    st.error("Erro ao analisar o arquivo 'resultados.csv'. Verifique o formato.")
    st.stop()

st.set_page_config(
    page_title="Seu Painel",
    layout="centered"
)

# Título do painel
st.title("Painel de BI - Exploração dos Dados")

# Excluir a coluna 'Unnamed: 0'
df = df.drop(columns=['Unnamed: 0'], errors='ignore')

# Garantindo que COMPETENCIA e CODIGO sejam strings
df['COMPETENCIA'] = df['COMPETENCIA'].astype(str)
df['CODIGO'] = df['CODIGO'].astype(str)

# Inicialização dos estados da sessão, se não existir
if 'competencia' not in st.session_state:
    st.session_state['competencia'] = ""

# Escolha da user journey
user_journey = st.selectbox("Escolha a Análise", options=["Exploração dos Dados", "Variações Grupo Elemento de Despesa", "Peso do Grupo Elemento de Despesa"])

if user_journey == "Exploração dos Dados":
    st.header("Exploração dos Dados")

    # Filtros de dados
    municipio_options = [""] + list(df['MUNICIPIO'].unique())
    municipio = st.selectbox("Selecione o Município (ou deixe em branco)", options=municipio_options)

    unidade_options = [""] + list(df[(df['MUNICIPIO'] == municipio)]['UNIDADE'].unique())
    unidade = st.selectbox("Selecione a Unidade (ou deixe em branco)", options=unidade_options)

    # Seleção do código e descrição
    codigos_disponiveis = df[(df['MUNICIPIO'] == municipio) & (df['UNIDADE'] == unidade)][['CODIGO', 'DESCRICAO']].drop_duplicates()
    codigo_options = [""] + [f"{row['CODIGO']} - {row['DESCRICAO']}" for index, row in codigos_disponiveis.iterrows()]

    codigo_selecionado = st.selectbox("Selecione o Código e Descrição (ou deixe em branco)", options=codigo_options)

    # Seleção da competência
    competencia_options = [""] + list(df['COMPETENCIA'].unique())
    competencia = st.selectbox("Selecione a Competência", options=competencia_options)
    st.session_state['competencia'] = competencia

    if st.button("Mostrar Dados"):
        df_resultado = df.copy()

        if municipio:
            df_resultado = df_resultado[df_resultado['MUNICIPIO'] == municipio]
        if unidade:
            df_resultado = df_resultado[df_resultado['UNIDADE'] == unidade]
        if codigo_selecionado:
            df_resultado = df_resultado[df_resultado['CODIGO'] == codigo_selecionado.split(" - ")[0]]
        if competencia:
            df_resultado = df_resultado[df_resultado['COMPETENCIA'] == competencia]

        if not df_resultado.empty:
            st.write(f"Resultados Filtrados: {len(df_resultado)} registros encontrados.")
            st.dataframe(df_resultado)

            # Preparando os dados para o gráfico
            df_grouped = df_resultado.groupby('COMPETENCIA')['VALOR_LIQUIDADO_MES'].sum().reset_index()

            # Plotando o gráfico
            plt.figure(figsize=(10, 5))
            plt.plot(df_grouped['COMPETENCIA'], df_grouped['VALOR_LIQUIDADO_MES'], marker='o')
            plt.title('Soma dos Valores Liquidados por Competência')
            plt.xlabel('Competência')
            plt.ylabel('Valor Liquidado')
            plt.xticks(rotation=45)
            plt.grid()
            st.pyplot(plt)

        else:
            st.write("Nenhum resultado encontrado para os filtros aplicados.")

elif user_journey == "Variações Grupo Elemento de Despesa":
    st.header("Variações Grupo Elemento de Despesa")
    
    # Seleção da competência
    competencia_options = [""] + list(df['COMPETENCIA'].unique())
    competencia = st.selectbox("Selecione a Competência", options=competencia_options)

    janela_temporal = st.selectbox("Selecione a Janela Temporal", options=["MENSAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"])

    min_variacao_percentual = st.number_input("Defina o valor mínimo de Variação Percentual (%)", value=0.0)
    min_variacao_absoluta = st.number_input("Defina o valor mínimo de Variação Absoluta", value=1_000_000.0)

    codigos_disponiveis = df['CODIGO'].unique()
    selected_codigos = st.multiselect(
        "Selecione os Códigos", 
        options=codigos_disponiveis,
        default=codigos_disponiveis.tolist()
    )

    outlier_score = st.slider("Filtrar por VARIAÇÃO % OUTLIER SCORE", 1, 9, 1)
    comparacao_outlier = st.selectbox("Filtrar por", options=["Maior ou Igual ao Score", "Igual ao Score"])

    variacao_percentual_col = f'VARIACAO_PERCENTUAL_{janela_temporal}'
    variacao_absoluta_col = f'VARIACAO_ABSOLUTA_{janela_temporal}'
    outlier_col = f'VARIACAO_PERCENTUAL_{janela_temporal}_OUTLIER_SCORE'

    if variacao_percentual_col not in df.columns or variacao_absoluta_col not in df.columns or outlier_col not in df.columns:
        st.error("Uma ou mais colunas de variação não estão disponíveis no DataFrame.")
    else:
        filtro_percentual = (df['COMPETENCIA'] == competencia) & (df[variacao_percentual_col] >= min_variacao_percentual) & (df['CODIGO'].isin(selected_codigos))

        if comparacao_outlier == "Igual ao Score":
            filtro_percentual &= (df[outlier_col] == outlier_score)
        else:
            filtro_percentual &= (df[outlier_col] >= outlier_score)

        filtro_absoluto = (df['COMPETENCIA'] == competencia) & (df[variacao_absoluta_col] >= min_variacao_absoluta)

        df_variacoes = df[filtro_percentual & filtro_absoluto].sort_values(by=variacao_percentual_col, ascending=False)

        if not df_variacoes.empty:
            st.write(f"Resultados de Variações: {len(df_variacoes)} registros encontrados.")
            st.dataframe(df_variacoes[['MUNICIPIO', 'UNIDADE', 'CODIGO', 'DESCRICAO', variacao_percentual_col, variacao_absoluta_col, outlier_col]])
        else:
            st.write("Nenhum resultado encontrado para os filtros aplicados.")

elif user_journey == "Peso do Grupo Elemento de Despesa":
    st.header("Peso do Grupo Elemento de Despesa")

    competencia_options = [""] + list(df['COMPETENCIA'].unique())
    competencia = st.selectbox("Selecione a Competência", options=competencia_options)
    
    janela_temporal = st.selectbox("Selecione a Janela Temporal", options=["MENSAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"])
        
    outlier_score = st.slider("Filtrar por PERCENTUAL DESPESA CODIGO OUTLIER SCORE", 1, 9, 1)
    comparacao_outlier = st.selectbox("Filtrar por", options=["Maior ou Igual ao Score", "Igual ao Score"])

    min_peso_percentual = st.number_input("Defina o peso percentual mínimo (%)", value=0.0)
    min_peso_absoluto = st.number_input("Defina o peso absoluto mínimo", value=1_000_000.0)

    peso_percentual_col = f'PERCENTUAL_DESPESA_CODIGO_{janela_temporal}'
    
    if janela_temporal != 'MENSAL':
        peso_absoluto_col = 'VALOR_LIQUIDADO_MES'
    elif janela_temporal != 'TRIMESTRAL':
      peso_absoluto_col = 'VALOR_MEDIO_LIQUIDADO_TRIMESTRE'
    elif janela_temporal != 'SEMESTRAL':
      peso_absoluto_col = 'VALOR_MEDIO_LIQUIDADO_SEMESTRE'
    elif janela_temporal != 'ANUAL':
      peso_absoluto_col = 'VALOR_MEDIO_LIQUIDADO_ANO'     
      
    outlier_col = f'PERCENTUAL_DESPESA_CODIGO_{janela_temporal}_OUTLIER_SCORE'

    codigos_disponiveis = df['CODIGO'].unique()
    selected_codigos = st.multiselect("Selecione os Códigos", options=codigos_disponiveis, default=codigos_disponiveis.tolist())

    if peso_percentual_col not in df.columns or peso_absoluto_col not in df.columns or outlier_col not in df.columns:
        st.error("Uma ou mais colunas de peso não estão disponíveis no DataFrame.")
    else:
        filtro_percentual = (df['COMPETENCIA'] == competencia) & (df[peso_percentual_col] >= min_peso_percentual) & (df['CODIGO'].isin(selected_codigos))

        if comparacao_outlier == "Igual ao Score":
            filtro_percentual &= (df[outlier_col] == outlier_score)
        else:
            filtro_percentual &= (df[outlier_col] >= outlier_score)

        filtro_absoluto = (df['COMPETENCIA'] == competencia) & (df[peso_absoluto_col] >= min_peso_absoluto)

        df_peso = df[filtro_percentual & filtro_absoluto].sort_values(by=peso_percentual_col, ascending=False)

        if not df_peso.empty:
            st.write(f"Resultados de Peso: {len(df_peso)} registros encontrados.")
            st.dataframe(df_peso[['MUNICIPIO', 'UNIDADE', 'CODIGO', 'DESCRICAO', peso_percentual_col, peso_absoluto_col, outlier_col]])
        else:
            st.write("Nenhum resultado encontrado para os filtros aplicados.")
