import streamlit as st
import pandas as pd
from scrapper import scrape_livelo
from data_transformations import transform_data

st.set_page_config(
    page_title="Parceiros Livelo", 
    layout="wide", 
    page_icon=":chart_with_upwards_trend:",
)
st.title(":material/query_stats: Tabela de Parceiros Livelo")


# Public CSV URL
sheet_url = "https://docs.google.com/spreadsheets/d/1KA1LGTdEszZDGxzVDiLrizg_qYf4vsMY3f2cT0Y1Pt4/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=3600)  # cache for 1h to avoid reloading too often
def load_data(url):
    return pd.read_csv(url)

# Carrega e transforma os dados
df = transform_data(load_data(sheet_url))

# Converte os tipos de dados
try:
    df["pontos"] = pd.to_numeric(df["pontos"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["scraping_day"] = pd.to_datetime(df["scraping_day"], errors="coerce")
except Exception as e:
    st.error(f"Erro ao converter os dados: {e}")


# Se não veio do CSV, tenta pegar do session_state
if df is None:
    df = st.session_state.get('df')
    if df is None:
        df = scrape_livelo()
        st.session_state['df'] = df

# Filtros na barra lateral
with st.sidebar:
    # Filtro multiselect para nomes
    if 'nome' in df.columns:
        all_names = sorted(df['nome'].dropna().unique())
        # default_names = ['ACER', 'ADCOS', 'Aliexpress','Amazon', 'AMOBELEZA', 'Asics', 'Avon', 'Azul Viagens', 'Basico.com', 'Beleza na web','Booking.com','Buser', 'Café Orfeu', 'CEA', 'Centauro', 'ClickBus']
        default_names = all_names
        names_selected = st.multiselect(
            "Filtrar por nome (dropdown ou digite)",
            options=all_names,
            default=default_names,
            key='nome_multiselect'
        )
    else:
        names_selected = []

    # Filtro de intervalo de datas (busca por várias possibilidades)
    date_col = None
    date_candidates = ['scraping_day']
    for col in df.columns:
        if any(candidate in col.lower() for candidate in date_candidates):
            date_col = col
            break
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if not df[date_col].isna().all():
            min_date = df[date_col].min().date()
            max_date = df[date_col].max().date()
            date_range = st.date_input(
                "Intervalo de datas (ano/mês/dia)",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date,
                key='date_input'
            )
            if len(date_range) == 2:
                start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            else:
                start_date, end_date = min_date, max_date
        else:
            st.warning("Coluna de data encontrada, mas não há datas válidas.")
            start_date, end_date = None, None
    else:
        st.warning("Nenhuma coluna de data encontrada. Certifique-se que o arquivo tem uma coluna de datas.")
        start_date, end_date = None, None

    # Filtro por indicador (subiu, desceu, manteve)
    indicator_options = ["","📈 Subiu", "📉 Desceu", "➖ Manteve"]
    selected_indicators = st.selectbox(
        "Filtrar por indicador",
        options=indicator_options
    )



# Aplica filtros
df_filtered = df.copy()
if names_selected:
    df_filtered = df_filtered[df_filtered['nome'].isin(names_selected)]
if date_col and start_date and end_date:
    df_filtered = df_filtered[df_filtered[date_col].between(start_date, end_date)]
if "indicador" in df_filtered.columns and selected_indicators!= "":
    df_filtered = df_filtered[df_filtered["indicador"].isin([selected_indicators])]

# Exibe tabela filtrada
st.dataframe(df_filtered)

# Exibe gráfico de dados históricos com pontos_por_real no eixo y e scraping_day no eixo x
import altair as alt

if "scraping_day" in df.columns and "pontos_por_real" in df.columns:
    df = df.dropna(subset=["scraping_day", "pontos_por_real", "nome"])
    
    # Adiciona interatividade ao gráfico para selecionar nomes na legenda
    selection = alt.selection_point(fields=['nome'], bind='legend')

    chart = alt.Chart(df).mark_line().encode(
        x="scraping_day:T",
        y="pontos_por_real:Q",
        color="nome:N",
        tooltip=["nome", "pontos_por_real", "scraping_day"]
    ).add_selection(
        selection
    ).transform_filter(
        selection
    ).properties(
        width="container",
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp by <a href="https://www.linkedin.com/in/janaina-r-fernandes/">@janaina-r-fernandes</a></h6>',
            unsafe_allow_html=True,
        )
    