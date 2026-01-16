import streamlit as st
import soccerdata as sd
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Sporting CP Analytics",
    page_icon="🦁",
    layout="wide"
)

st.title("🦁 Sporting CP: Estatísticas Avançadas (xG, xAG, Criação)")
st.markdown("Dados detalhados via **FBref**.")

# --- BARRA LATERAL ---
st.sidebar.header("Filtros")
season_input = st.sidebar.text_input("Época", "2024-2025")

# --- CACHE E DATA LOADER ---
@st.cache_data
def load_fbref(season):
    return sd.FBref(leagues="POR-Primeira Liga", seasons=season)

@st.cache_data
def get_all_stats(_fb):
    # Vamos buscar vários tipos de estatísticas
    with st.spinner('A recolher dados táticos...'):
        std = _fb.read_player_season_stats(stat_type="standard")
        shoot = _fb.read_player_season_stats(stat_type="shooting")
        passing = _fb.read_player_season_stats(stat_type="passing")
        defense = _fb.read_player_season_stats(stat_type="defense")
    return std, shoot, passing, defense

# --- PROCESSAMENTO ---
try:
    fb = load_fbref(season_input)
    std_df, shoot_df, pass_df, def_df = get_all_stats(fb)
    
    # Filtrar apenas Sporting CP e resetar index para facilitar manuseamento
    def clean_df(df):
        df = df.reset_index()
        return df[df['team'] == "Sporting CP"].copy()

    scp_std = clean_df(std_df)
    scp_shoot = clean_df(shoot_df)
    scp_pass = clean_df(pass_df)
    scp_def = clean_df(def_df)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}. Confirma a época.")
    st.stop()

# --- DASHBOARD ---

# Separadores
tab1, tab2, tab3 = st.tabs(["🎯 Finalização & xG", "pia Criação & Posse", "🛡️ Defesa"])

# TAB 1: FINALIZAÇÃO (xG)
with tab1:
    st.subheader("Performance Ofensiva: Golos vs Expected Goals (xG)")
    st.markdown("Quem está a marcar mais do que seria esperado (**Overperforming**)?")
    
    # Preparar dados de xG
    # Colunas Shooting: ('expected', 'xG'), ('performance', 'Gls') 
    # Nota: Usamos standard para Gls pois shooting por vezes tem apenas G-PK
    
    # Merge simples para ter dados num sitio (Golos do Standard, xG do Shooting)
    metrics = scp_std[[('player',''), ('performance','Gls'), ('playing_time','Min')]].copy()
    metrics.columns = ['Jogador', 'Golos', 'Minutos']
    
    xg_data = scp_shoot[[('player',''), ('expected','xG')]].copy()
    xg_data.columns = ['Jogador', 'xG']
    
    merged_atk = pd.merge(metrics, xg_data, on='Jogador')
    merged_atk['Diferença'] = merged_atk['Golos'] - merged_atk['xG']
    
    # Filtrar jogadores com poucos minutos para limpar o gráfico
    merged_atk = merged_atk[merged_atk['Minutos'] > 300]

    # Gráfico de Dispersão
    fig_xg = px.scatter(merged_atk, x='xG', y='Golos', 
                        text='Jogador', size='Minutos', color='Diferença',
                        color_continuous_scale='RdBu', # Azul = Bom, Vermelho = Mau
                        title="Eficácia: Golos vs xG (Jogadores > 300 min)")
    
    # Linha de referência (x=y)
    fig_xg.add_shape(type="line", x0=0, y0=0, x1=merged_atk['Golos'].max(), y1=merged_atk['Golos'].max(),
                     line=dict(color="Gray", dash="dash"))
    
    st.plotly_chart(fig_xg, use_container_width=True)
    
    st.dataframe(merged_atk.sort_values(by='xG', ascending=False).style.format({"xG": "{:.2f}", "Diferença": "{:.2f}"}))

# TAB 2: CRIAÇÃO (xAG + Progressão)
with tab2:
    st.subheader("Maestros do Meio Campo")
    
    # Dados de Passe
    # ('expected', 'xAG') -> Expected Assisted Goals
    # ('passing', 'PrgP') -> Passes Progressivos
    
    pass_metrics = scp_pass[[('player',''), ('expected','xAG'), ('passing','PrgP')]].copy()
    pass_metrics.columns = ['Jogador', 'xAG', 'Passes Progressivos']
    pass_metrics = pass_metrics.sort_values(by='xAG', ascending=False).head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_create = px.bar(pass_metrics, x='xAG', y='Jogador', orientation='h',
                            title="Ameaça de Assistência (xAG)", color='xAG', color_continuous_scale='Teal')
        st.plotly_chart(fig_create, use_container_width=True)
        
    with col2:
        fig_prog = px.bar(pass_metrics.sort_values(by='Passes Progressivos', ascending=False), 
                          x='Passes Progressivos', y='Jogador', orientation='h',
                          title="Passes Progressivos", color='Passes Progressivos', color_continuous_scale='Viridis')
        st.plotly_chart(fig_prog, use_container_width=True)

# TAB 3: DEFESA
with tab3:
    st.subheader("Ações Defensivas")
    
    # Tackles e Interceptações
    def_metrics = scp_def[[('player',''), ('tackles','TklW'), ('interceptions','Int')]].copy()
    def_metrics.columns = ['Jogador', 'Desarmes Ganhos', 'Interceções']
    
    # Scatter Defensivo
    fig_def = px.scatter(def_metrics, x='Interceções', y='Desarmes Ganhos', text='Jogador',
                         title="Atividade Defensiva: Desarmes vs Interceções", size_max=60)
    st.plotly_chart(fig_def, use_container_width=True)