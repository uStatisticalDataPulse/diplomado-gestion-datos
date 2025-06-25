import streamlit as st
import pandas as pd
import plotly.express as px
import io

def show_transform_tab():
    st.header("🔧 Transformación y Modelo Estrella (Versión Ajustada)")

    if 'df_raw' not in st.session_state:
        st.warning("Primero debes cargar los datos en la pestaña 'Carga de Datos'.")
        return

    df = st.session_state['df_raw'].copy()
    st.subheader("Paso 1: Limpieza inicial")
    st.write(f"🔹 Total registros originales: {len(df)}")

    columnas_relevantes = [
        'a_o', 'departamento', 'municipio', 'c_digo_departamento',
        'poblaci_n_5_16', 'tasa_matriculaci_n_5_16',
        'cobertura_neta', 'cobertura_bruta'
    ]

    columnas_faltantes = [col for col in columnas_relevantes if col not in df.columns]
    if columnas_faltantes:
        st.error(f"❌ Las siguientes columnas no están en los datos: {columnas_faltantes}")
        return

    df = df[columnas_relevantes]
    df.columns = [c.lower() for c in df.columns]

    for col in df.columns:
        if col not in ['departamento', 'municipio']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df_clean = df.dropna()
    st.write(f"🔹 Registros después de eliminar nulos: {len(df_clean)}")

    st.subheader("Paso 2: Crear dimensiones")

    def crear_dimension(df, cols, nombre, sort_col=None):
        dim = df[cols].drop_duplicates()
        if sort_col:
            dim = dim.sort_values(by=sort_col)
        dim = dim.reset_index(drop=True).copy()
        dim_id = f"id_{nombre}"
        dim[dim_id] = dim.index + 1
        return dim[[dim_id] + cols]

    # Dimensión tiempo
    dim_tiempo = crear_dimension(df_clean, ['a_o'], 'tiempo')

    # Dimensión geográfica (usando código de departamento)
    dim_geo = df_clean[['c_digo_departamento', 'departamento', 'municipio']].copy()
    dim_geo = dim_geo.sort_values(by=['c_digo_departamento', 'municipio'])
    dim_geo = dim_geo.drop_duplicates(subset=['c_digo_departamento'], keep='first').reset_index(drop=True)
    dim_geo['id_geo'] = dim_geo.index + 1
    dim_geo = dim_geo[['id_geo', 'c_digo_departamento', 'departamento', 'municipio']]

    st.write("🔸 Dimensión tiempo:", len(dim_tiempo))
    st.write("🔸 Dimensión geo (por código DANE):", len(dim_geo))

    st.subheader("Paso 3: Tabla de Hechos")

    df_fact = df_clean.merge(dim_tiempo, on='a_o') \
                      .merge(dim_geo, on=['departamento', 'municipio'], how='inner')

    df_fact = df_fact[[
        'id_tiempo', 'id_geo',
        'poblaci_n_5_16', 'tasa_matriculaci_n_5_16',
        'cobertura_neta', 'cobertura_bruta'
    ]]

    st.write(f"✅ Tabla de hechos construida con {len(df_fact)} registros.")
    st.session_state['df_fact'] = df_fact
    st.session_state['dim_geo'] = dim_geo
    st.session_state['dim_tiempo'] = dim_tiempo

    st.subheader("🔍 Métricas y respuestas")

    escolaridad_prom = df_fact.groupby('id_geo')[['tasa_matriculaci_n_5_16']].mean().reset_index()
    escolaridad_prom = escolaridad_prom.merge(dim_geo, on='id_geo')
    top_mpios = escolaridad_prom.sort_values(by='tasa_matriculaci_n_5_16', ascending=False).head(10)

    st.markdown("**¿Qué municipios tienen mayor porcentaje de escolaridad (5-16 años)?**")
    st.dataframe(top_mpios[['departamento', 'municipio', 'tasa_matriculaci_n_5_16']])

    fig = px.bar(
        top_mpios.sort_values(by='tasa_matriculaci_n_5_16', ascending=False),
        x='municipio',
        y='tasa_matriculaci_n_5_16',
        title='Top 10 Municipios con Mayor Tasa de Escolaridad (5-16 años)',
        labels={'tasa_matriculaci_n_5_16': 'Tasa de Escolaridad (%)'},
    )
    st.plotly_chart(fig, use_container_width=True)

    cobertura_depto = df_fact.merge(dim_geo, on='id_geo') \
        .groupby('departamento')['cobertura_neta'].mean().sort_values(ascending=False).head(10)

    st.markdown("**¿Qué departamentos tienen mayor cobertura neta promedio?**")
    st.dataframe(cobertura_depto.reset_index())

    st.subheader("📄 Vista completa de la Tabla de Hechos")
    st.dataframe(df_fact.head(50))
    st.markdown(f"🔹 Total de registros en la tabla de hechos: `{len(df_fact):,}`")

    # Descargar en Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_fact.to_excel(writer, index=False, sheet_name='TablaHechos')
    output.seek(0)

    st.download_button(
        label="📥 Descargar tabla de hechos en Excel",
        data=output,
        file_name='tabla_hechos_educacion.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.subheader("📊 Resumen por Departamento y Año")
    df_fact_ext = df_fact.merge(dim_geo, on='id_geo').merge(dim_tiempo, on='id_tiempo')
    resumen = df_fact_ext.groupby(['departamento', 'a_o'])[
        ['tasa_matriculaci_n_5_16', 'cobertura_neta', 'cobertura_bruta']
    ].mean().reset_index()
    st.dataframe(resumen.head(20))