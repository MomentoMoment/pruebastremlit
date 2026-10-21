"""Conductores: producción respecto de su grupo y rendimiento de combustible."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import datos
from core.estilo import (CONFIG_GRAFICO, ESTADOS, GRIS_OSCURO, NEGRO, encabezado,
                         estado, estilo_grafico, filtro_periodo, leyenda_semaforo, pie,
                         tarjeta_kpi, texto_estado)
from core.formato import fmt_clp, fmt_num

encabezado("Tablero de Operaciones — Conductores",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

# por defecto, el último mes cerrado
hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)
anio, mes = filtro_periodo("conductores", anio_def=a_def, mes_def=m_def)

cond = datos.conductores_mes()
grupos = ["Todos"] + sorted(cond["grupo"].unique())
grupo = st.selectbox("Grupo", grupos)

d = calc.produccion_conductores(cond, anio, mes)
a_ant, m_ant = calc.mes_anterior(anio, mes)
d_ant = calc.produccion_conductores(cond, a_ant, m_ant)
if grupo != "Todos":
    d, d_ant = d[d.grupo == grupo], d_ant[d_ant.grupo == grupo]

if d.empty:
    st.info("No hay datos para el período seleccionado.")
    st.stop()

META_REND = datos.METAS["rendimiento"]
META_PROD = datos.METAS["produccion"]
d["est_prod"] = d["produccion"].map(lambda v: estado(v, META_PROD))
d["est_rend"] = d["rendimiento"].map(lambda v: estado(v, META_REND))
peor = {"cumple": 0, "alerta": 1, "no_cumple": 2, "sin_meta": -1}
d["est_peor"] = [a if peor[a] >= peor[b] else b for a, b in zip(d.est_prod, d.est_rend)]

# --------------------------------------------------------------- tarjetas
def n_sobre(df):
    return int((df["produccion"] >= 100).sum()) if not df.empty else 0


def n_ambos(df):
    if df.empty:
        return 0
    return int(((df["produccion"] < META_PROD * 0.9) & (df["rendimiento"] < META_REND * 0.9)).sum())


k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Conductores con producción ≥ 100 % de su grupo", n_sobre(d), "", dec=0,
                delta=n_sobre(d) - n_sobre(d_ant), nota=f"de {len(d)} conductores")
with k2:
    rend = d["km"].sum() / d["litros"].sum()
    rend_ant = d_ant["km"].sum() / d_ant["litros"].sum() if not d_ant.empty else None
    tarjeta_kpi("Rendimiento de los conductores", rend, "km/l", dec=2, meta=META_REND,
                delta=rend - rend_ant if rend_ant else None)
with k3:
    tarjeta_kpi("Conductores en «No cumple» en ambos indicadores", n_ambos(d), "", dec=0,
                sentido="menor_mejor", delta=n_ambos(d) - n_ambos(d_ant))

# --------------------------------------------------------------- dispersión
f = go.Figure()
for k, (texto, color) in ESTADOS.items():
    s = d[d["est_peor"] == k]
    if s.empty:
        continue
    f.add_scatter(x=s["produccion"], y=s["rendimiento"], mode="markers", name=texto,
                  marker=dict(color=color, size=11, line=dict(color="white", width=1)),
                  customdata=s[["conductor", "grupo", "viajes"]],
                  hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                                "Producción: %{x:.1f} %<br>Rendimiento: %{y:.2f} km/l<br>"
                                "Viajes: %{customdata[2]}<extra></extra>")
f.add_vline(x=100, line_dash="dash", line_color=NEGRO, annotation_text="Promedio del grupo",
            annotation_position="top")
f.add_hline(y=META_REND, line_dash="dash", line_color=NEGRO,
            annotation_text=f"Meta rendimiento {fmt_num(META_REND, 2)} km/l",
            annotation_position="right")
x_min, x_max = min(60, d.produccion.min() - 5), max(140, d.produccion.max() + 5)
y_min, y_max = min(2.0, d.rendimiento.min() - 0.05), max(3.2, d.rendimiento.max() + 0.05)
for x, y, t in [(x_max, y_max, "Alta producción y buen rendimiento"),
                (x_max, y_min, "Producción alta, revisar rendimiento"),
                (x_min, y_max, "Buen rendimiento, baja producción"),
                (x_min, y_min, "Revisar ambos")]:
    f.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(color=GRIS_OSCURO, size=11),
                     xanchor="right" if x == x_max else "left",
                     yanchor="top" if y == y_max else "bottom")
f.update_layout(title="Producción vs rendimiento por conductor (color = el peor de sus dos estados)")
f.update_xaxes(title="Producción respecto del promedio de su grupo (%)", range=[x_min, x_max])
f.update_yaxes(title="Rendimiento (km/l)", range=[y_min, y_max])
st.plotly_chart(estilo_grafico(f, 470), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- rankings
colores = {k: c for k, (_, c) in ESTADOS.items()}


def ranking(col, est, titulo, ref, formato):
    s = d.sort_values(col)
    s = pd.concat([s.head(5), s.tail(10)]) if len(s) > 15 else s
    g = go.Figure(go.Bar(y=s["conductor"], x=s[col], orientation="h",
                         marker_color=s[est].map(colores),
                         text=[formato(v) for v in s[col]], textposition="outside"))
    g.add_vline(x=ref, line_dash="dash", line_color=NEGRO)
    g.update_layout(title=titulo, showlegend=False)
    return estilo_grafico(g, 480)


c1, c2 = st.columns(2)
c1.plotly_chart(ranking("produccion", "est_prod", "Producción (%) — 10 mejores y 5 más bajos",
                        100, lambda v: f"{fmt_num(v, 0)} %"),
                use_container_width=True, config=CONFIG_GRAFICO)
c2.plotly_chart(ranking("rendimiento", "est_rend", "Rendimiento (km/l) — 10 mejores y 5 más bajos",
                        META_REND, lambda v: fmt_num(v, 2)),
                use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- tabla
t = d.sort_values("produccion", ascending=False)
st.subheader("Detalle por conductor")
st.dataframe(pd.DataFrame({
    "Conductor": t["conductor"], "Grupo": t["grupo"], "Viajes": t["viajes"],
    "Ingreso": t["ingreso"].map(fmt_clp), "Producción (%)": t["produccion"].round(1),
    "Km": t["km"].map(lambda v: fmt_num(v, 0)), "Litros": t["litros"].map(lambda v: fmt_num(v, 0)),
    "Rendimiento (km/l)": t["rendimiento"].map(lambda v: fmt_num(v, 2)),
    "Estado producción": t["est_prod"].map(texto_estado),
    "Estado rendimiento": t["est_rend"].map(texto_estado),
}), hide_index=True, use_container_width=True,
    column_config={"Producción (%)": st.column_config.ProgressColumn(
        "Producción (%)", format="%.0f %%", min_value=0, max_value=150)})

leyenda_semaforo()
pie("Producción = ingreso del conductor / ingreso promedio de su grupo × 100. Variaciones contra "
    "el mes anterior. Metas referenciales por validar. Datos ilustrativos.")
