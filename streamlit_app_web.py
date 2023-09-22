import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import geopandas as gpd
import os
import socket
import matplotlib.colors as mcolors

colors = plt.cm.get_cmap('Reds', 12)(range(12))
colors = list(colors)
colors.append('#3a0000')
colors.append('#000000')

custom_cmap = mcolors.ListedColormap(colors)


if "delitos" not in st.session_state:
    st.session_state["delitos"] = pd.read_csv("Data/delitos_mensuales.csv", encoding="utf8")

    st.session_state["censo_poblacion"] = pd.read_csv("Data/Municipios.csv", encoding="utf8")
    st.session_state["censo_poblacion"].columns = ['cve_ent', 'ent', 'cve_mun', 'mun', 'pobtot']

    st.session_state["geo_mpos"] = (gpd.read_file('../Data/mapa_mexico/' if socket.gethostname() == "erick-huawei" else 'Data/mapa_mexico/')
                                    .set_index('CLAVE')
                                    .to_crs(epsg=4485)
                                    .assign(cve_ent=lambda _df: _df['CVE_EDO'].astype(int)
                                            , cve_mun=lambda _df: _df['CVE_MUNI'].astype(int)
                                            )
                                   )

    st.session_state["geo_mx"] = st.session_state["geo_mpos"].dissolve(by='CVE_EDO')


df = st.session_state["delitos"].copy()
delitos = df.columns[3:].values.tolist()

url = "https://github.com/ErickdeMauleon/dashboard-delitos"
st.title("Delitos en México")
st.write("""Datos abiertos de la Secretaría de Seguridad y Protección Ciudadana, actualizados a %s.\n
Datos del censo de población del INEGI, actualizados a 2020.\n
Delitos por cada 100 mil habitantes tomando años móviles.\n
Repositorio en [GitHub](%s)
""" % (str(df["Fecha"].max())[:7]), url)

st.sidebar.title("Delitos en México")


delito_selected = st.sidebar.selectbox("Selecciona el delito", delitos)
flag = st.sidebar.selectbox("Filtrar municipios con menos de 100 mil habitantes", ["Sí", "No"]) == "Sí"

fechas = df["Fecha"].drop_duplicates().sort_values(ascending=False).values.tolist()
periodo = st.sidebar.selectbox("Selecciona el año móvil", fechas[:-12])

pos = fechas.index(periodo)
Ult_anio = fechas[pos:pos+12]

df = (df
      [df["Fecha"].isin(Ult_anio)]
      .filter(["cve_ent", "cve_mun", "Fecha", delito_selected])
      .groupby(["cve_ent", "cve_mun"], as_index=False)
      .agg(delitos=(delito_selected, "sum"))
      .merge(st.session_state["censo_poblacion"].filter(["cve_ent", "cve_mun", "pobtot"])
             , on=["cve_ent", "cve_mun"]
             , how="left"
            )
      .assign(delitos_por_cienmil=lambda _df: _df["delitos"] / _df["pobtot"] * 100000)
     )

to_plot = (st.session_state["geo_mpos"]
           .merge(df
                  .query("pobtot > 100000" if flag else "pobtot > 0")
                  .filter(['cve_ent', 'cve_mun', 'delitos_por_cienmil', 'pobtot', 'delitos'])
                  , on=['cve_ent', 'cve_mun']
                  , how='left'
                  )
         )

boxstyle = dict(facecolor='white', alpha=0.5, edgecolor='black', boxstyle='round,pad=0.5')


st.subheader("México")

fig, ax = plt.subplots()
st.session_state["geo_mx"].boundary.plot(lw=1, color='grey', ax=ax)
st.session_state["geo_mpos"].boundary.plot(lw=1, color='lightgrey', ax=ax, alpha=0.2)
to_plot.plot(column='delitos_por_cienmil', ax=ax, legend=True, cmap=custom_cmap)
ax.set_title(f'{delito_selected} por cada 100 mil habitantes', fontsize="xx-large")
ax.set_aspect('auto')
ax.set_axis_off()
ax.set_xticks([])
ax.set_yticks([])
fig.set_size_inches(20, 10)

st.pyplot(fig, use_container_width=True)

st.subheader("Área metropolitana del Valle de México")

l, u = (1.71e6, 1.82e6)
ax.set_xbound(lower=l, upper=u)
l, u = (2.14e6, 2.22e6)
ax.set_ybound(lower=l, upper=u)
ax.text(1.79e6, 2.15e6, 'EdoMex', fontsize=20, color='black', bbox=boxstyle, alpha=0.9)
ax.text(1.755e6, 2.1575e6, 'CDMX', fontsize=20, color='black', bbox=boxstyle, alpha=0.9)

st.pyplot(fig, use_container_width=True)

st.subheader("Área metropolitana de Guadalajara")

for text in ax.texts:
    text.set_visible(False)
l, u = (1.225e6, 1.37e6)
ax.set_xbound(lower=l, upper=u)
l, u = (2.25e6, 2.38e6)
ax.set_ybound(lower=l, upper=u)
ax.text(1.23e6, 2.255e6, 'Jalisco', fontsize=20, color='black', bbox=boxstyle, alpha=0.9)

st.pyplot(fig, use_container_width=True)

st.subheader("Área metropolitana de Monterrey")

for text in ax.texts:
    text.set_visible(False)
l, u = (1.51e6, 1.64e6)
p = (0.85*u + 0.15*l)
r = (0.15*u + 0.85*l)
ax.set_xbound(lower=l, upper=u)
l, u = (2.83e6, 2.93e6)
q = (0.1*u + 0.9*l)
ax.set_ybound(lower=l, upper=u)
ax.text(p, q, 'Nuevo León', fontsize=20, color='black', bbox=boxstyle, alpha=0.9)
ax.text(r, q, 'Coahuila', fontsize=20, color='black', bbox=boxstyle, alpha=0.9)

st.pyplot(fig, use_container_width=True)
