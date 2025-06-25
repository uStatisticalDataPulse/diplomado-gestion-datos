import streamlit as st

from cargar_datos import show_data_tab
from transformacion import show_transform_tab
from visualizaciones import show_visualization_tab


# Definir páginas o pestañas
tab = st.sidebar.radio("Navegación", ["Carga de Datos", "Transformación y Métricas","Visualizaciones", "Mapa"])

# Lógica según la pestaña seleccionada
if tab == "Carga de Datos":
    show_data_tab()
elif tab == "Transformación y Métricas":
    show_transform_tab()
elif tab == "Visualizaciones":
    show_visualization_tab()
elif tab == "Mapa":
    st.write("🗺️ Mapa aquí...")