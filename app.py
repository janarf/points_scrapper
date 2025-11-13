import streamlit as st
from scraper import scrape_livelo

st.set_page_config(page_title="Parceiros Livelo", layout="wide")
st.title("Tabela de Parceiros Livelo")

# Button to refresh data
if st.button("Atualizar Dados"):
    with st.spinner("Buscando dados..."):
        df = scrape_livelo()
        st.session_state['df'] = df
        st.success("Dados atualizados!")

# Show table
df = st.session_state.get('df')
if df is None:
    df = scrape_livelo()
    st.session_state['df'] = df

st.dataframe(df)
