"""
Aplicação Corporativa de BI - Performance de Mercado de Ações & Séries Temporais (B3).
Desenvolvido por: Andressa Alves de Souza
Orientação: Prof. Sávio Ricardo Garcia
"""

import streamlit as st

# 1. Configuração da Página (Layout amplo e título oficial)
st.set_page_config(
    page_title="Performance B3 | Mercado de Capitais",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Barra Lateral (Sidebar de Navegação e Filtros Executivos)
with st.sidebar:
    st.title("Painel de Controlo")
    st.markdown("---")
    st.info("Configuração dos parâmetros de mercado e horizonte temporal (2021-2023).")
    
    # Informações institucionais e autoria na barra lateral
    st.markdown("---")
    st.markdown("### Governança & Créditos")
    st.markdown("**Desenvolvedora:**  \nAndressa Alves de Souza")
    st.markdown("**Orientador:**  \nProf. Sávio Ricardo Garcia")

# 3. Cabeçalho Executivo Principal
st.title("📈 Performance de Mercado de Ações & Séries Temporais (B3)")
st.caption(
    "Data App Corporativo de Business Intelligence | Triénio 2021-2023 | "
    "Desenvolvido por: **Andressa Alves de Souza** | Orientador: **Prof. Sávio Ricardo Garcia**"
)
st.markdown("---")

# 4. Estado Inicial da Aplicação
st.success("Ambiente inicializado e pronto para a integração do pipeline de ETL.")