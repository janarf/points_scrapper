import streamlit as st
from scrapper import scrape_livelo

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


# Filtro dinâmico: lista de nomes
if 'nomes_filtro' not in st.session_state:
    st.session_state['nomes_filtro'] = []

nome_input = st.text_input("Digite um nome para filtrar")
col1, col2 = st.columns([1,1])
with col1:
    if st.button("Adicionar ao filtro") and nome_input.strip():
        nome = nome_input.strip()
        if nome not in st.session_state['nomes_filtro']:
            st.session_state['nomes_filtro'].append(nome)
        st.experimental_rerun()
with col2:
    if st.button("Limpar filtro"):
        st.session_state['nomes_filtro'] = []
        st.experimental_rerun()

# UI para remover nomes individuais
if st.session_state['nomes_filtro']:
    st.write("Nomes filtrando:")
    for nome in st.session_state['nomes_filtro']:
        if st.button(f"Remover '{nome}'", key=f"remover_{nome}"):
            st.session_state['nomes_filtro'].remove(nome)
            st.experimental_rerun()

# Detecta coluna de nome de forma robusta (case-insensitive)
name_col = None
if hasattr(df, 'columns'):
    for col in df.columns:
        if col.lower() == 'nome' or 'nome' in col.lower():
            name_col = col
            break



nomes_lista = st.session_state['nomes_filtro']
if nomes_lista and name_col:
    try:
        regex = '|'.join([f"{n}" for n in nomes_lista])
        filtered_df = df[df[name_col].astype(str).str.contains(regex, case=False, na=False)]
    except Exception:
        filtered_df = df
        st.warning('Ocorreu um problema ao filtrar — exibindo todos os registros.')
elif nomes_lista and not name_col:
    filtered_df = df
    st.warning('Coluna de nome não encontrada no DataFrame. Verifique os nomes das colunas.')
else:
    filtered_df = df

st.dataframe(filtered_df)
