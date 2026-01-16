import streamlit as st
import soccerdata as sd
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Arsenal Analytics 🔴", page_icon="⚽", layout="wide")

st.title("🔴 Arsenal FC: Advanced Analytics")

# --- BARRA LATERAL ---
season_input = st.sidebar.text_input("Época", "2023-2024")

# --- NOVA ESTRATÉGIA DE CACHE ---
# Em vez de passar o objeto 'fb', passamos apenas a 'season'
# O Streamlit guarda o resultado final (DataFrame), que é seguro.

@st.cache_data
def get_data_from_fbref(season, stat_type):
    # Criamos o objeto FBref aqui dentro, usamos e "deitamos fora"
    fb = sd.FBref(leagues="ENG-Premier League", seasons=season)
    df = fb.read_player_season_stats(stat_type=stat_type)
    
    # Limpeza imediata para o Arsenal
    df = df.reset_index()
    df = df[df['team'].str.contains("Arsenal", na=False)]
    return df

# --- RECOLHA DOS DADOS ---
try:
    with st.spinner('A recolher estatísticas oficiais...'):
        # Chamamos a função para cada tipo de estatística
        ars_std = get_data_from_fbref(season_input, "standard")
        ars_shoot = get_data_from_fbref(season_input, "shooting")
        ars_pass = get_data_from_fbref(season_input, "passing")
        ars_def = get_data_from_fbref(season_input, "defense")
        
except Exception as e:
    st.error(f"Ocorreu um erro: {e}")
    st.stop()

# --- DASHBOARD ---
tab1, tab2 = st.tabs(["🎯 Ataque", "🛡️ Defesa"])

with tab1:
    st.subheader("Eficácia Ofensiva: Golos vs xG")
    
    # Preparar colunas (usando nomes simples após o reset_index)
    # Nota: No FBref, após reset_index, as colunas podem ser tuplos ou strings.
    # Vamos forçar nomes de colunas simples para evitar confusão:
    
    atk_df = pd.DataFrame({
        'Jogador': ars_std['player'],
        'Golos': ars_std['performance', 'Gls'],
        'xG': ars_shoot['expected', 'xG'],
        'Minutos': ars_std['playing_time', 'Min']
    })
    
    atk_df = atk_df[atk_df['Minutos'] > 400]
    
    fig_xg = px.scatter(atk_df, x='xG', y='Golos', text='Jogador', size='Minutos',
                        color=(atk_df['Golos'] - atk_df['xG']),
                        color_continuous_scale='RdBu_r',
                        title="Diferencial de xG (Quem está a finalizar melhor?)")
    st.plotly_chart(fig_xg, use_container_width=True)

with tab2:
    st.subheader("Métricas Defensivas")
    def_df = pd.DataFrame({
        'Jogador': ars_def['player'],
        'Desarmes': ars_def['tackles', 'TklW'],
        'Interceções': ars_def['interceptions', 'Int']
    })
    st.bar_chart(def_df.set_index('Jogador').head(10))