import streamlit as st
import soccerdata as sd
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Arsenal Analytics 🔴",
    page_icon="⚽",
    layout="wide"
)

st.title("🔴 Arsenal FC: Advanced Analytics Dashboard")
st.markdown("Dados detalhados da Premier League via **FBref**.")

# --- BARRA LATERAL ---
st.sidebar.header("Filtros")
season_input = st.sidebar.text_input("Época (ex: 2023-2024)", "2023-2024")

# --- CACHE E DATA LOADER ---
@st.cache_data
def load_fbref(season):
    # Agora usamos a Premier League, que o FBref suporta a 100%
    return sd.FBref(leagues="ENG-Premier League", seasons=season)

@st.cache_data
def get_all_stats(_fb):
    with st.spinner('A analisar táticas dos Gunners...'):
        std = _fb.read_player_season_stats(stat_type="standard")
        shoot = _fb.read_player_season_stats(stat_type="shooting")
        passing = _fb.read_player_season_stats(stat_type="passing")
        defense = _fb.read_player_season_stats(stat_type="defense")
    return std, shoot, passing, defense

# --- PROCESSAMENTO ---
try:
    fb = load_fbref(season_input)
    std_df, shoot_df, pass_df, def_df = get_all_stats(fb)
    
    # Filtrar apenas Arsenal
    def clean_df(df):
        df = df.reset_index()
        # O FBref às vezes usa 'Arsenal' ou 'Arsenal FC'
        return df[df['team'].str.contains("Arsenal")].copy()

    ars_std = clean_df(std_df)
    ars_shoot = clean_df(shoot_df)
    ars_pass = clean_df(pass_df)
    ars_def = clean_df(def_df)

except Exception as e:
    st.error(f"Erro: {e}. Confirma se o formato da época é '2023-2024'.")
    st.stop()

# --- DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["🎯 Finalização & xG", "🪄 Criação (Odegaard/Saka)", "🛡️ Defesa (The Wall)"])

# TAB 1: FINALIZAÇÃO
with tab1:
    st.subheader("Performance Ofensiva: Golos vs Expected Goals (xG)")
    
    metrics = ars_std[[('player',''), ('performance','Gls'), ('playing_time','Min')]].copy()
    metrics.columns = ['Jogador', 'Golos', 'Minutos']
    
    xg_data = ars_shoot[[('player',''), ('expected','xG')]].copy()
    xg_data.columns = ['Jogador', 'xG']
    
    merged_atk = pd.merge(metrics, xg_data, on='Jogador')
    merged_atk['Diferença'] = merged_atk['Golos'] - merged_atk['xG']
    merged_atk = merged_atk[merged_atk['Minutos'] > 400]

    fig_xg = px.scatter(merged_atk, x='xG', y='Golos', 
                        text='Jogador', size='Minutos', color='Diferença',
                        color_continuous_scale='RdBu_r', 
                        title="Eficácia de Finalização (Jogadores > 400 min)")
    
    # Linha x=y para ver quem está acima/abaixo da média
    fig_xg.add_shape(type="line", x0=0, y0=0, x1=merged_atk['Golos'].max(), y1=merged_atk['Golos'].max(),
                     line=dict(color="Gray", dash="dash"))
    
    st.plotly_chart(fig_xg, use_container_width=True)

# TAB 2: CRIAÇÃO
with tab2:
    st.subheader("Maestros: Passes Progressivos e xAG")
    
    pass_metrics = ars_pass[[('player',''), ('expected','xAG'), ('passing','PrgP')]].copy()
    pass_metrics.columns = ['Jogador', 'xAG', 'Passes Progressivos']
    
    # Gráfico comparativo de criação
    fig_create = px.scatter(pass_metrics, x='Passes Progressivos', y='xAG', text='Jogador',
                            title="Quem faz o Arsenal avançar no terreno?",
                            color_discrete_sequence=['red'])
    st.plotly_chart(fig_create, use_container_width=True)

# TAB 3: DEFESA
with tab3:
    st.subheader("Ações Defensivas: Desarmes e Interceções")
    
    def_metrics = ars_def[[('player',''), ('tackles','TklW'), ('interceptions','Int')]].copy()
    def_metrics.columns = ['Jogador', 'Desarmes Ganhos', 'Interceções']
    
    fig_def = px.bar(def_metrics.sort_values('Desarmes Ganhos', ascending=False).head(10), 
                     x='Jogador', y=['Desarmes Ganhos', 'Interceções'],
                     title="Top 10 Muralhas Defensivas", barmode='group')
    st.plotly_chart(fig_def, use_container_width=True)