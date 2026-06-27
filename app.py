import streamlit as st
import pandas as pd
import numpy as np
import pulp
import math
import os

import streamlit as st
import pandas as pd
import numpy as np
import pulp
import math
import os
import platform

# --- O TRUQUE PARA DRIBLAR A PASTA TEMP (APENAS NO WINDOWS) ---
if platform.system() == "Windows":
    os.environ['TMP'] = 'C:\\Seminario_PO'
    os.environ['TEMP'] = 'C:\\Seminario_PO'
    os.environ['TMPDIR'] = 'C:\\Seminario_PO'
# -------------------------------------------------------------

st.set_page_config(page_title="Otimizador de Roteiros - PO", layout="wide")
# ... (o resto do código continua igualzinho daqui para baixo)

st.set_page_config(page_title="Otimizador de Roteiros - PO", layout="wide")

# =====================================================================
# CONTROLE DE ESTADO DA INTERFACE (SLIDES)
# =====================================================================
if 'etapa_atual' not in st.session_state:
    st.session_state.etapa_atual = 1

def proxima_etapa():
    st.session_state.etapa_atual += 1

def etapa_anterior():
    st.session_state.etapa_atual -= 1

def ir_para_formulacao():
    st.session_state.etapa_atual = 5

def reiniciar():
    st.session_state.etapa_atual = 1

# =====================================================================
# ESTILO VISUAL FIXO (ESCURO FOSCO MINIMALISTA)
# =====================================================================
tema = {
    "bg": "#121212", "sidebar": "#1A1A1A", "sec_bg": "#2A2A2A", 
    "text": "#E0E0E0", "primary": "#CBA358", "btn_text": "#121212"
}

estilo_css = f"""
<style>
    .stApp, .main {{ background-color: {tema['bg']} !important; }}
    [data-testid="stSidebar"] {{ background-color: {tema['sidebar']} !important; }}
    h1, h2, h3, p, label, span, div[data-testid="stMarkdownContainer"] {{ color: {tema['text']} !important; }}
    button[kind="primary"] {{ background-color: {tema['primary']} !important; border: none !important; }}
    button[kind="primary"] * {{ color: {tema['btn_text']} !important; }}
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {{
        background-color: {tema['sec_bg']} !important; color: {tema['text']} !important; padding: 10px 15px !important; border-radius: 8px !important;
    }}
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
        background-color: {tema['sec_bg']} !important; border-radius: 50% !important; transition: 0.3s;
    }}
    [data-testid="collapsedControl"] svg, [data-testid="stSidebarCollapseButton"] svg {{
        color: {tema['primary']} !important; fill: {tema['primary']} !important; width: 25px !important; height: 25px !important;
    }}
    [data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapseButton"]:hover {{ transform: scale(1.1); }}
    span[data-baseweb="tag"] {{ background-color: {tema['primary']} !important; color: {tema['btn_text']} !important; border-radius: 4px !important; }}
    span[data-baseweb="tag"] span, span[data-baseweb="tag"] svg {{ color: {tema['btn_text']} !important; fill: {tema['btn_text']} !important; }}
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# =====================================================================
# CARREGAMENTO DO BANCO DE DADOS (100 CIDADES GLOBAIS)
# =====================================================================
arquivo_bd = 'banco_coordenadas.csv'

if not os.path.exists(arquivo_bd):
    # Lista organizada para evitar desalinhamento de colunas
    dados_100 = [
        # América do Norte
        ("Nova York", 40.7128, -74.0060, "America do Norte"), ("Los Angeles", 34.0522, -118.2437, "America do Norte"),
        ("Chicago", 41.8781, -87.6298, "America do Norte"), ("Las Vegas", 36.1699, -115.1398, "America do Norte"),
        ("Miami", 25.7617, -80.1918, "America do Norte"), ("São Francisco", 37.7749, -122.4194, "America do Norte"),
        ("Toronto", 43.6510, -79.3470, "America do Norte"), ("Vancouver", 49.2827, -123.1207, "America do Norte"),
        ("Montreal", 45.5017, -73.5673, "America do Norte"), ("Cidade do México", 19.4326, -99.1332, "America do Norte"),
        ("Cancún", 21.1619, -86.8515, "America do Norte"), ("Havana", 23.1136, -82.3666, "America do Norte"),
        ("Orlando", 28.5383, -81.3792, "America do Norte"), ("Washington", 38.9072, -77.0369, "America do Norte"),
        ("Boston", 42.3601, -71.0589, "America do Norte"),
        
        # América do Sul
        ("Rio de Janeiro", -22.9068, -43.1729, "America do Sul"), ("São Paulo", -23.5505, -46.6333, "America do Sul"),
        ("Buenos Aires", -34.6037, -58.3816, "America do Sul"), ("Santiago", -33.4489, -70.6693, "America do Sul"),
        ("Lima", -12.0464, -77.0428, "America do Sul"), ("Cusco", -13.5226, -71.9673, "America do Sul"),
        ("Bogotá", 4.7110, -74.0721, "America do Sul"), ("Cartagena", 10.3910, -75.4794, "America do Sul"),
        ("Quito", -0.1807, -78.4678, "America do Sul"), ("Montevidéu", -34.9011, -56.1645, "America do Sul"),
        
        # Europa
        ("Paris", 48.8566, 2.3522, "Europa"), ("Londres", 51.5074, -0.1278, "Europa"), 
        ("Roma", 41.9028, 12.4964, "Europa"), ("Barcelona", 41.3851, 2.1734, "Europa"),
        ("Madri", 40.4168, -3.7038, "Europa"), ("Berlim", 52.5200, 13.4050, "Europa"),
        ("Munique", 48.1351, 11.5820, "Europa"), ("Viena", 48.2082, 16.3738, "Europa"),
        ("Praga", 50.0755, 14.4378, "Europa"), ("Budapeste", 47.4979, 19.0402, "Europa"),
        ("Atenas", 37.9838, 23.7275, "Europa"), ("Amsterdã", 52.3676, 4.9041, "Europa"),
        ("Lisboa", 38.7223, -9.1393, "Europa"), ("Veneza", 45.4408, 12.3155, "Europa"),
        ("Florença", 43.7696, 11.2558, "Europa"), ("Milão", 45.4642, 9.1900, "Europa"),
        ("Dublin", 53.3498, -6.2603, "Europa"), ("Edimburgo", 55.9533, -3.1883, "Europa"),
        ("Bruxelas", 50.8503, 4.3517, "Europa"), ("Zurique", 47.3769, 8.5417, "Europa"),
        ("Genebra", 46.2044, 6.1432, "Europa"), ("Copenhague", 55.6761, 12.5683, "Europa"),
        ("Estocolmo", 59.3293, 18.0686, "Europa"), ("Oslo", 59.9139, 10.7522, "Europa"),
        ("Helsinque", 60.1695, 24.9354, "Europa"), ("Varsóvia", 52.2297, 21.0122, "Europa"),
        ("Cracóvia", 50.0647, 19.9450, "Europa"), ("Frankfurt", 50.1109, 8.6821, "Europa"),
        ("Salzburgo", 47.8095, 13.0550, "Europa"), ("Sevilha", 37.3891, -5.9845, "Europa"),
        ("Reykjavik", 64.1466, -21.9426, "Europa"), ("Moscou", 55.7558, 37.6173, "Europa"),
        
        # Ásia
        ("Tóquio", 35.6762, 139.6503, "Asia"), ("Quioto", 35.0116, 135.7681, "Asia"),
        ("Osaka", 34.6937, 135.5023, "Asia"), ("Seul", 37.5665, 126.9780, "Asia"),
        ("Taipé", 25.0330, 121.5654, "Asia"), ("Xangai", 31.2304, 121.4737, "Asia"),
        ("Chongqing", 29.5583, 106.5516, "Asia"), ("Pequim", 39.9042, 116.4074, "Asia"),
        ("Xi'an", 34.3416, 108.9398, "Asia"), ("Chengdu", 30.6586, 104.0648, "Asia"),
        ("Guangzhou", 23.1291, 113.2644, "Asia"), ("Shenzhen", 22.5431, 114.0579, "Asia"),
        ("Hong Kong", 22.3193, 114.1694, "Asia"), ("Macau", 22.1987, 113.5439, "Asia"),
        ("Bangkok", 13.7563, 100.5018, "Asia"), ("Singapura", 1.3521, 103.8198, "Asia"),
        ("Kuala Lumpur", 3.1390, 101.6869, "Asia"), ("Hanói", 21.0285, 105.8542, "Asia"),
        ("Ho Chi Minh", 10.8231, 106.6297, "Asia"), ("Bali", -8.4095, 115.1889, "Asia"),
        ("Mumbai", 19.0760, 72.8777, "Asia"), ("Nova Deli", 28.6139, 77.2090, "Asia"),
        ("Agra", 27.1767, 78.0081, "Asia"), ("Jaipur", 26.9124, 75.7873, "Asia"),
        ("Dubai", 25.2048, 55.2708, "Asia"), ("Abu Dhabi", 24.4539, 54.3773, "Asia"),
        ("Istambul", 41.0082, 28.9784, "Asia"), ("Jerusalém", 31.7683, 35.2137, "Asia"),
        ("Meca", 21.3891, 39.8579, "Asia"), ("Amã", 31.9454, 35.9284, "Asia"),
        
        # África
        ("Cairo", 30.0444, 31.2357, "Africa"), ("Marraquexe", 31.6295, -7.9811, "Africa"),
        ("Casablanca", 33.5731, -7.5898, "Africa"), ("Joanesburgo", -26.2041, 28.0473, "Africa"),
        ("Cidade do Cabo", -33.9249, 18.4241, "Africa"), ("Nairobi", -1.2921, 36.8219, "Africa"),
        ("Dacar", 14.7167, -17.4677, "Africa"),
        
        # Oceania
        ("Sydney", -33.8688, 151.2093, "Oceania"), ("Melbourne", -37.8136, 144.9631, "Oceania"),
        ("Brisbane", -27.4705, 153.0260, "Oceania"), ("Auckland", -36.8485, 174.7633, "Oceania"),
        ("Queenstown", -45.0312, 168.6626, "Oceania"), ("Fiji", -17.7134, 178.0650, "Oceania")
    ]
    
    dados_iniciais = {
        "Cidade": [d[0] for d in dados_100],
        "Latitude": [d[1] for d in dados_100],
        "Longitude": [d[2] for d in dados_100],
        "Continente": [d[3] for d in dados_100]
    }
    pd.DataFrame(dados_iniciais).to_csv(arquivo_bd, index=False, encoding='latin-1')

df_bd = pd.read_csv(arquivo_bd, encoding='latin-1')
lista_todas_cidades = sorted(df_bd['Cidade'].tolist())

def calcular_distancia(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    return 2 * math.asin(math.sqrt(math.sin((lat2-lat1)/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2-lon1)/2)**2)) * 6371

# =====================================================================
# SLIDE 1: APRESENTAÇÃO DO PROBLEMA
# =====================================================================
if st.session_state.etapa_atual == 1:
    st.title("Caixeiro Viajante Multimodal")
    st.markdown("Trabalho desenvolvido para o Seminário da Disciplina de Pesquisa Operacional.")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🎯 O Problema")
        st.write("Criar um itinerário contínuo que cruza múltiplas cidades ou países é um desafio logístico complexo. O tempo e o dinheiro economizados em trânsito significam mais liberdade no destino final — seja para explorar marcos urbanos históricos ou simplesmente ter tranquilidade para apreciar a noite e as luzes de metrópoles vibrantes como Chongqing e Xangai no nosso roteiro de abril de 2026.")
    with col2:
        st.markdown("### 💡 A Solução")
        st.write("Utilizando a Pesquisa Operacional, modelamos este cenário matemático como um **Problema do Caixeiro Viajante**. O algoritmo avalia milhares de combinações possíveis, analisando o *trade-off* exato entre trens de alta velocidade e aviões, eliminando sub-rotas e garantindo a rota global de maior eficiência.")
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.button("Iniciar Configuração do Modelo ➔", on_click=proxima_etapa, type="primary")

# =====================================================================
# SLIDE 2: DEFINIÇÃO DO OBJETIVO
# =====================================================================
elif st.session_state.etapa_atual == 2:
    st.title("Passo 1: Função Objetivo")
    st.write("O que o algoritmo deve priorizar na busca pela rota ótima?")
    st.markdown("---")
    st.session_state.objetivo_escolhido = st.radio(
        "Selecione a métrica de otimização:",
        ("Minimizar Custo Financeiro", "Minimizar Tempo de Trânsito")
    )
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 4])
    col1.button("⬅ Voltar", on_click=etapa_anterior)
    col2.button("Avançar ➔", on_click=proxima_etapa, type="primary")

# =====================================================================
# SLIDE 3: SELEÇÃO DE DESTINOS
# =====================================================================
elif st.session_state.etapa_atual == 3:
    st.title("Passo 2: Rede de Nós (Cidades)")
    st.write("Quais localidades farão parte deste ciclo logístico?")
    st.markdown("---")
    if 'cidades_selecionadas' not in st.session_state:
        st.session_state.cidades_selecionadas = ["Paris", "Londres", "Nova York", "Tóquio", "Xangai", "Chongqing", "Rio de Janeiro", "Dubai", "Sydney", "Cidade do Cabo"]
    
    st.session_state.cidades_selecionadas = st.multiselect(
        "Selecione de 10 a 15 destinos globais:", 
        options=lista_todas_cidades, 
        default=st.session_state.cidades_selecionadas,
        max_selections=15, # TRAVA ACADÊMICA DE SEGURANÇA
        help="A restrição máxima de 15 localidades existe para evitar o tempo de processamento exponencial da complexidade NP-Difícil."
    )
    
    n_cidades = len(st.session_state.cidades_selecionadas)
    if n_cidades < 10:
        st.warning(f"Você selecionou {n_cidades} nós. O problema exige um mínimo de 10 localidades.")
    else:
        st.success(f"Excelente! {n_cidades} nós identificados.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, _ = st.columns([1, 1, 4])
    col1.button("⬅ Voltar", on_click=etapa_anterior)
    if n_cidades >= 10:
        col2.button("Executar Cálculo Matemático 🚀", on_click=proxima_etapa, type="primary")

# =====================================================================
# SLIDE 4: EXECUÇÃO E RESULTADOS FINAIS
# =====================================================================
elif st.session_state.etapa_atual == 4:
    st.title("Análise da Solução")
    st.markdown("---")
    cidades = st.session_state.cidades_selecionadas
    n_cidades = len(cidades)
    objetivo_escolhido = st.session_state.objetivo_escolhido
    
    with st.spinner('Construindo restrições e otimizando matrizes via algoritmo CBC...'):
        df_selecionado = df_bd[df_bd['Cidade'].isin(cidades)].set_index('Cidade')
        ca, ct = np.zeros((n_cidades, n_cidades)), np.zeros((n_cidades, n_cidades))
        ta, tt = np.zeros((n_cidades, n_cidades)), np.zeros((n_cidades, n_cidades))
        
        for i in range(n_cidades):
            for j in range(n_cidades):
                if i != j:
                    origem, destino = cidades[i], cidades[j]
                    dist = calcular_distancia(df_selecionado.loc[origem, 'Latitude'], df_selecionado.loc[origem, 'Longitude'],
                                              df_selecionado.loc[destino, 'Latitude'], df_selecionado.loc[destino, 'Longitude'])
                    cont_origem = df_selecionado.loc[origem, 'Continente']
                    cont_destino = df_selecionado.loc[destino, 'Continente']
                    
                    ca[i][j], ta[i][j] = (999999, 999999) if dist < 200 else (200 + (dist * 0.8), (dist / 800) + 3)
                    ct[i][j], tt[i][j] = (999999, 999999) if cont_origem != cont_destino else (50 + (dist * 0.4), (dist / 250) + 1)
                        
        custos, tempos = [ca.tolist(), ct.tolist()], [ta.tolist(), tt.tolist()]
        prob = pulp.LpProblem("Caixeiro_Viajante_Multimodal", pulp.LpMinimize)
        modais, n_modais = ["✈️ Avião", "🚆 Trem"], 2
        
        x = pulp.LpVariable.dicts("x", ((i, j, k) for i in range(n_cidades) for j in range(n_cidades) for k in range(n_modais) if i != j), cat='Binary')
        u = pulp.LpVariable.dicts("u", (i for i in range(n_cidades)), lowBound=0, cat='Continuous')
        
        if objetivo_escolhido == "Minimizar Custo Financeiro":
            prob += pulp.lpSum(custos[k][i][j] * x[i, j, k] for i in range(n_cidades) for j in range(n_cidades) for k in range(n_modais) if i != j)
        else:
            prob += pulp.lpSum(tempos[k][i][j] * x[i, j, k] for i in range(n_cidades) for j in range(n_cidades) for k in range(n_modais) if i != j)
                               
        for i in range(n_cidades): prob += pulp.lpSum(x[i, j, k] for j in range(n_cidades) for k in range(n_modais) if i != j) == 1
        for j in range(n_cidades): prob += pulp.lpSum(x[i, j, k] for i in range(n_cidades) for k in range(n_modais) if i != j) == 1
        for i in range(1, n_cidades):
            for j in range(1, n_cidades):
                if i != j: prob += u[i] - u[j] + n_cidades * pulp.lpSum(x[i, j, k] for k in range(n_modais)) <= n_cidades - 1
                    
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
    if pulp.LpStatus[prob.status] == 'Optimal':
        st.success(f"✅ Roteiro Ótimo Global encontrado para o objetivo: {objetivo_escolhido}")
        rota, cidade_atual, custo_total, tempo_total = [], 0, 0, 0
        for passo in range(n_cidades):
            proxima_cidade_encontrada = False
            for j in range(n_cidades):
                if cidade_atual != j:
                    for k in range(n_modais):
                        if pulp.value(x[cidade_atual, j, k]) is not None and pulp.value(x[cidade_atual, j, k]) > 0.5: 
                            rota.append({
                                "Ordem": passo + 1, "Partida": cidades[cidade_atual], "Destino": cidades[j],
                                "Modal Escolhido": modais[k], "Custo R$)": round(custos[k][cidade_atual][j], 2), "Tempo (h)": round(tempos[k][cidade_atual][j], 1)
                            })
                            custo_total += custos[k][cidade_atual][j]
                            tempo_total += tempos[k][cidade_atual][j]
                            cidade_atual = j
                            proxima_cidade_encontrada = True
                            break
                if proxima_cidade_encontrada: break
        
        st.markdown("### 📊 Indicadores Principais")
        col1, col2, col3 = st.columns(3)
        col1.metric("Custo Total Estimado", f"R$ {round(custo_total, 2)}")
        col2.metric("Tempo Total em Trânsito", f"{round(tempo_total, 1)} horas")
        col3.metric("Nós Visitados", f"{n_cidades} Cidades")
        
        st.markdown("### 🗺️ Itinerário Detalhado")
        st.dataframe(pd.DataFrame(rota), use_container_width=True)
    else:
        st.error("Não foi possível encontrar uma solução matemática ótima.")

    st.markdown("<br><hr>", unsafe_allow_html=True)
    col_b1, col_b2, _ = st.columns([1.5, 2, 4])
    col_b1.button("↻ Nova Simulação", on_click=reiniciar)
    col_b2.button("📐 Ver Formulação Matemática", on_click=ir_para_formulacao, type="primary")

# =====================================================================
# SLIDE 5: MODELAGEM MATEMÁTICA E EQUAÇÕES (NOVA PÁGINA)
# =====================================================================
elif st.session_state.etapa_atual == 5:
    st.title("📐 Formulação Matemática Formal")
    st.write("Abaixo está a estrutura algébrica rigorosa resolvida pelo motor do aplicativo (Modelo MTZ Multimodal).")
    st.markdown("---")
    
    st.markdown("### 1. Variáveis de Decisão")
    st.latex(r"x_{ijk} = \begin{cases} 1, & \text{se o caixeiro viaja da cidade } i \text{ para a cidade } j \text{ via modal } k \\ 0, & \text{caso contrário} \end{cases}")
    st.latex(r"u_i = \text{Variável contínua auxiliar que representa a ordem de visita da cidade } i \text{ (induz cronologia).}")
    
    st.markdown("### 2. Função Objetivo")
    st.write("Dependendo da escolha do usuário no Passo 1, o solver minimiza a matriz de parâmetros de Custo ($C_{ijk}$) ou Tempo ($T_{ijk}$):")
    st.latex(r"\min Z = \sum_{i=1}^{n} \sum_{j=1}^{n} \sum_{k=1}^{m} P_{ijk} \cdot x_{ijk} \quad (\text{onde } P \in \{C, T\})")
    
    st.markdown("### 3. Restrições Lineares")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("**Saída Única:** Garante que o viajante saia exatamente uma vez de cada localidade $i$:")
        st.latex(r"\sum_{j=1, j \neq i}^{n} \sum_{k=1}^{m} x_{ijk} = 1 \quad \forall i = 1, \dots, n")
        
    with col_r2:
        st.markdown("**Chegada Única:** Garante que o viajante chegue exatamente uma vez a cada localidade $j$:")
        st.latex(r"\sum_{i=1, i \neq j}^{n} \sum_{k=1}^{m} x_{ijk} = 1 \quad \forall j = 1, \dots, n")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Quebra de Sub-rotas (Miller-Tucker-Zemlin - MTZ):** Impede a formação de circuitos paralelos fechados, forçando um ciclo único e completo:")
    st.latex(r"u_i - u_j + n \cdot \sum_{k=1}^{m} x_{ijk} \le n - 1 \quad \forall i, j \in \{2, \dots, n\}, \, i \neq j")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.button("↻ Voltar ao Início", on_click=reiniciar, type="primary")     
