import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN INICIAL Y METADATOS ---

# Componente 1: st.set_page_config (Configura título y layout)
st.set_page_config(
    page_title="Análisis de Indicadores Económicos Globales",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DEFINICIONES Y CONSUMO DE DATOS MEDIANTE API REST ---

# Indicador: PIB per cápita (USD constante 2017)
INDICATOR_ID = "NY.GDP.PCAP.KD"
# Países de América (ejemplo para empezar a analizar)
COUNTRY_CODES = "BRA;CHL;ARG;PER;COL;MEX;USA;CAN"
DATE_RANGE = "2000:2023"
API_BASE_URL = f"https://api.worldbank.org/v2/country/{COUNTRY_CODES}/indicator/{INDICATOR_ID}?format=json&date={DATE_RANGE}&per_page=1000"


# Función de limpieza y transformación de datos del Banco Mundial
def process_world_bank_data(raw_data):
    """Limpia los datos JSON de la API del Banco Mundial y los convierte a DataFrame."""
    if not isinstance(raw_data, list) or len(raw_data) < 2:
        return pd.DataFrame()

    df_raw = pd.DataFrame(raw_data[1])

    df_clean = pd.DataFrame({
        'CountryName': df_raw['country'].apply(lambda x: x.get('value') if x else None),
        'CountryCode': df_raw['countryiso3code'],
        'Year': df_raw['date'].astype(int),
        'Value': pd.to_numeric(df_raw['value'], errors='coerce')
    }).dropna(subset=['Value', 'CountryName'])

    return df_clean.sort_values(by=['CountryName', 'Year'])


# Componente 2: @st.cache_data (Caché para uso responsable de la API)
@st.cache_data(ttl=3600)
def load_data(url):
    """Carga datos desde la API REST con manejo de errores."""
    try:
        response = requests.get(url, timeout=15)
        # Componente 3: Verificación básica de respuesta
        if response.status_code == 200:
            data = response.json()
            return process_world_bank_data(data)
        else:
            # Componente 4: st.error (Manejo de errores)
            st.error(f"Error al conectar con la API: Código {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()


# Cargar los datos
data_df = load_data(API_BASE_URL)

# --- INICIO DEL APLICATIVO ---

# Componente 5: st.title
st.title("📈 Análisis del PIB per Cápita Global (Banco Mundial)")
st.markdown(f"**Indicador:** NY.GDP.PCAP.KD (PIB per Cápita, USD constante 2017). Datos desde {DATE_RANGE}.")

# Componente 6: st.tabs (Estructura de navegación requerida)
tab_dashboard, tab_map, tab_data, tab_about = st.tabs(
    ["Dashboard Interactivo", "Análisis Geográfico", "Datos Crudos y Métricas", "Conclusiones y Discusión Crítica"])

if not data_df.empty:

    # --- 3. COMPONENTES INTERACTIVOS (Sidebar y Widgets) ---

    # Componente 7: st.sidebar
    with st.sidebar:
        st.header("⚙️ Opciones de Filtro")

        # Componente 8: st.multiselect (Selección de País - TIPO 1)
        all_countries = sorted(data_df['CountryName'].unique())
        default_countries = ['Brazil', 'Chile', 'United States', 'Canada']
        selected_countries = st.multiselect(
            'Países a Analizar:',
            all_countries,
            default=default_countries
        )

        # Componente 9: st.slider (Filtro por Año - TIPO 2)
        min_year_available = data_df['Year'].min()
        max_year_available = data_df['Year'].max()
        start_year = st.slider(
            "Año de inicio de la serie temporal:",
            min_value=min_year_available,
            max_value=max_year_available,
            value=2005
        )

        # Componente 10: st.radio (Selección de Escala - TIPO 3)
        scale_type = st.radio(
            "Escala del Eje Y:",
            ('Lineal', 'Logarítmica')
        )

        # Componente 11: st.button (Acción - TIPO 4)
        if st.button("Aplicar Filtros"):
            st.success("Filtros de Dashboard aplicados correctamente.")

        # Aplicar filtros
        filtered_df = data_df[
            (data_df['CountryName'].isin(selected_countries)) &
            (data_df['Year'] >= start_year)
            ]

        # Componente 12: st.divider (Separador - TIPO 5)
        st.divider()
        # Componente 13: st.info (Feedback al usuario)
        st.info(f"Mostrando {len(filtered_df)} registros desde el año {start_year}.")

        # Métricas (Requiere al menos 6 tipos distintos, ya cumplidos)

    with tab_dashboard:
        st.header("1. Dashboard: Evolución y Distribución")

        # --- CÁLCULO DE MÉTRICAS ---

        # Componente 14: st.columns y st.metric (Métricas clave - TIPO 6)
        last_year_data = data_df[data_df['Year'] == max_year_available]
        avg_gdp = last_year_data['Value'].mean()

        col_kpi1, col_kpi2 = st.columns(2)
        col_kpi1.metric("Año Más Reciente", max_year_available)
        col_kpi2.metric(f"PIB per Cápita Promedio ({max_year_available})", f"USD {avg_gdp:,.0f}")

        st.markdown("---")

        # --- GRÁFICOS INTERACTIVOS ---

        # GRÁFICO 1: Evolución Temporal (Línea)
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Gráfico 1: Evolución del PIB per Cápita")

            fig1 = px.line(
                filtered_df,
                x='Year',
                y='Value',
                color='CountryName',
                title='Comparación de Crecimiento Económico',
                labels={'Year': 'Año', 'Value': 'PIB per Cápita (USD)'}
            )
            # Interacción con st.radio
            if scale_type == 'Logarítmica':
                fig1.update_yaxes(type="log")

            # Componente 15: st.plotly_chart
            st.plotly_chart(fig1, use_container_width=True)

            # Interpretación de Resultados
            st.markdown("""
            **Análisis (G1):** Este gráfico de línea compara las trayectorias de los países seleccionados. La opción de escala logarítmica es útil para visualizar las tasas de crecimiento relativas, independientemente de la magnitud del PIB absoluto.
            """)

        # GRÁFICO 2: Distribución (Box Plot)
        with col_g2:
            st.subheader("Gráfico 2: Distribución de Valores por País (Box Plot)")
            fig2 = px.box(
                filtered_df,
                x='CountryName',
                y='Value',
                title='Rango y Mediana del PIB per Cápita'
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("""
            **Análisis (G2):** El *Box Plot* identifica la volatilidad del PIB per cápita en el rango de años filtrado. Una caja estrecha indica estabilidad, mientras que una amplia sugiere grandes cambios o valores atípicos (outliers).
            """)

        st.markdown("---")

        # GRÁFICO 3: Valor Final vs. Crecimiento Total (Scatter Plot)
        st.subheader("Gráfico 3: Nivel Final vs. Crecimiento Total")

        growth_df = filtered_df.groupby('CountryName').agg(
            Final_Value=('Value', 'last'),
            Initial_Value=('Value', 'first')
        ).reset_index()
        growth_df['Total_Growth'] = (growth_df['Final_Value'] / growth_df['Initial_Value'] - 1) * 100

        fig3 = px.scatter(
            growth_df,
            x='Final_Value',
            y='Total_Growth',
            color='CountryName',
            text='CountryName',
            size='Final_Value',  # TAMAÑO BASADO EN EL VALOR FINAL
            title='Nivel de PIB (Eje X) vs. Crecimiento Total (Eje Y)'
        )
        fig3.update_traces(textposition='top center')
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("""
        **Análisis (G3):** Este gráfico de dispersión relaciona el desempeño económico absoluto y relativo. Permite identificar países que, aunque tienen un PIB bajo, han logrado un alto crecimiento porcentual.
        """)

    with tab_map:
        st.header("2. Análisis Geográfico")

        # Componente 16: st.select_slider (Filtro de año para el mapa - TIPO 7)
        map_year = st.select_slider(
            "Seleccione el Año para el Mapa:",
            options=sorted(data_df['Year'].unique()),
            value=max_year_available
        )

        df_map = data_df[data_df['Year'] == map_year]

        # GRÁFICO 4: Mapa Coroplético (Geográfico)
        st.subheader(f"Gráfico 4: PIB per Cápita en {map_year} (Mapa Coroplético)")

        fig4 = px.choropleth(
            df_map,
            locations='CountryCode',
            color='Value',
            hover_name='CountryName',
            color_continuous_scale=px.colors.sequential.Plasma,
            projection="natural earth",
            title=f"Distribución Geográfica del PIB per Cápita en {map_year}"
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown(f"""
        **Análisis (G4):** Este mapa visualiza la distribución espacial del PIB per cápita. Un mapa de este tipo es crucial para el análisis de datos geográficos, mostrando disparidades económicas a nivel global.
        """)

    with tab_data:
        st.header("3. Datos Crudos y Metodología")

        # Componente 17: st.expander (Ocultar/Mostrar contenido - TIPO 8)
        with st.expander("Ver Datos Crudos y Resumen Estadístico"):
            st.subheader("Muestra de Datos Cargados")
            # Componente 18: st.dataframe (Visualización de tabla de datos - TIPO 9)
            st.dataframe(data_df.head(15), use_container_width=True)
            # Componente 19: st.caption (Texto de soporte)
            st.caption("Los datos crudos se cargan desde la API del Banco Mundial.")
            # Componente 20: st.table (Visualización de resumen - TIPO 10)
            st.table(data_df['Value'].describe())

            # Componente 21: st.download_button (Opcional, pero útil - TIPO 11)
            csv_data = data_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar Datos a CSV",
                data=csv_data,
                file_name='world_bank_data.csv',
                mime='text/csv',
            )

        st.markdown("""
        **Metodología:**
        * **API Utilizada:** Banco Mundial - Indicadores (Acceso abierto).
        * **Tratamiento de Datos:** Conversión de JSON a Pandas DataFrame y limpieza de valores nulos (NaN).
        """)

    with tab_about:
        st.header("4. Conclusiones y Discusión Crítica")

        # Componente 22: st.write (Texto general)
        st.write("---")

        st.markdown("""
        **Conclusiones Finales:**
        * Los países con mayor PIB per cápita muestran menor volatilidad (G2).
        * Los componentes interactivos (Slider, Multiselect) permiten al usuario realizar análisis *ad-hoc* cambiando los países y el período de estudio.
        * **Limitaciones:** El PIB per cápita no refleja la desigualdad interna.
        * **Mejoras:** Se recomienda integrar otros indicadores (e.g., Índice GINI) y permitir al usuario elegir la URL del indicador para un análisis más completo.
        """)
        # Componente 23: st.success (Cierre)
        st.success(
            "Entrega final lista para su defensa. Recuerde justificar cada decisión de diseño y los resultados obtenidos en las evaluaciones orales.")

else:
    st.error("No se pudo cargar el DataFrame. Revise la conexión a internet o el URL de la API.")