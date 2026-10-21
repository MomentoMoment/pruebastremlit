"""Gerencia — Combustible: rendimiento por camión y consumo real vs esperado."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import calculos_gerencia as cg
from core import datos
from core.estilo import (CONFIG_GRAFICO, ESTADOS, GRIS_MEDIO, GRIS_OSCURO, NEGRO,
                         boton_exportar, encabezado, estado, estilo_grafico, filtro_periodo,
                         leyenda_semaforo, pie, tarjeta_kpi, texto_estado)
from core.formato import MESES_CORTO, fmt_num, mes_anio

M = datos.METAS_GERENCIA

encabezado("Tablero de Gerencia — Combustible",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)
anio, mes = filtro_periodo("g_comb", anio_def=a_def, mes_def=m_def)
t = datos.tramos_combustible()
sel = st.multiselect("Camión", sorted(t["patente"].unique()), placeholder="Todos los camiones")
if sel:
    t = t[t["patente"].isin(sel)]

a_ant, m_ant = calc.mes_anterior(anio, mes)
ta = calc.filtrar_mes(t, anio, mes, col="fecha_cierre")
tp = calc.filtrar_mes(t, a_ant, m_ant, col="fecha_cierre")
if ta.empty:
    st.info("No hay tramos de combustible para el período seleccionado.")
    st.stop()

# --------------------------------------------------------------- tarjetas
validos = ta[ta["valido"]]
k = st.columns(4)
with k[0]:
    tarjeta_kpi("Rendimiento de la flota", cg.rendimiento(ta), "km/l", dec=2, meta=M["rendimiento"],
                delta=cg.delta(cg.rendimiento(ta), cg.rendimiento(tp)))
with k[1]:
    lit_a, lit_p = validos["litros"].sum(), tp[tp["valido"]]["litros"].sum()
    tarjeta_kpi("Litros cargados (tramos válidos)", lit_a, "l", dec=0, sentido="menor_mejor",
                delta=100 * (lit_a / lit_p - 1) if lit_p else None, unidad_delta="%")
with k[2]:
    tarjeta_kpi("Consumo real vs esperado", cg.consumo_vs_esperado(ta), "%",
                meta=M["consumo_vs_esperado"], sentido="menor_mejor",
                delta=cg.delta(cg.consumo_vs_esperado(ta), cg.consumo_vs_esperado(tp)),
                nota="Sobre 100 % = consumió más de lo esperado")
with k[3]:
    n_desc = int((~ta["valido"]).sum())
    tarjeta_kpi("Tramos descartados", n_desc, "", dec=0, sentido="menor_mejor",
                delta=n_desc - int((~tp["valido"]).sum()), unidad_delta="",
                nota=f"de {len(ta)} tramos · rendimiento fuera de 1–5 km/l")

colores = {k: c for k, (_, c) in ESTADOS.items()}
c1, c2 = st.columns(2)

# --------------------------------------------------------------- rendimiento por camión
with c1:
    g = validos.groupby("patente")[["km", "litros"]].sum()
    g["rend"] = g["km"] / g["litros"]
    g["estado"] = g["rend"].map(lambda x: estado(x, M["rendimiento"]))
    g = g.sort_values("rend", ascending=False)
    g = pd.concat([g.head(5), g.tail(10)]) if len(g) > 15 else g
    f = go.Figure(go.Bar(y=g.index, x=g["rend"], orientation="h",
                         marker_color=g["estado"].map(colores),
                         text=[fmt_num(x, 2) for x in g["rend"]], textposition="outside"))
    f.add_vline(x=M["rendimiento"], line_dash="dash", line_color=NEGRO,
                annotation_text=f"Meta {fmt_num(M['rendimiento'], 2)}")
    f.update_layout(title=f"Rendimiento por camión (km/l) — 5 mejores y 10 más bajos", showlegend=False)
    f.update_xaxes(range=[min(2.0, g["rend"].min() - 0.1), max(3.2, g["rend"].max() + 0.15)])
    st.plotly_chart(estilo_grafico(f, 460), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- real vs esperado 12 meses
with c2:
    fin = pd.Period(year=anio, month=mes, freq="M")
    filas = []
    for p in pd.period_range(fin - 11, fin, freq="M"):
        x = calc.filtrar_mes(t, p.year, p.month, col="fecha_cierre")
        x = x[x["valido"]]
        filas.append({"mes": f"{MESES_CORTO[p.month - 1]}-{p.year}",
                      "real": x["litros"].sum(), "esperado": x["litros_esperados"].sum()})
    s = pd.DataFrame(filas)
    f = go.Figure()
    f.add_bar(x=s["mes"], y=s["real"], name="Real", marker_color=NEGRO)
    f.add_scatter(x=s["mes"], y=s["esperado"], name="Esperado (referencia)", mode="lines+markers",
                  line=dict(color=GRIS_MEDIO, width=3))
    f.update_layout(title="Litros reales vs esperados — últimos 12 meses")
    f.update_yaxes(title="Litros")
    st.plotly_chart(estilo_grafico(f, 460), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- tramos a revisar
st.subheader("Tramos a revisar — mayor desviación primero")
d = ta.copy()
d["desv_l"] = d["litros"] - d["litros_esperados"]
d["desv_pct"] = 100 * d["litros"] / d["litros_esperados"]
d["rend"] = d["km"] / d["litros"]
d["estado"] = [texto_estado(estado(x, M["consumo_vs_esperado"], "menor_mejor")) if ok
               else "● Descartado (rendimiento fuera de rango)" for x, ok in zip(d["desv_pct"], d["valido"])]
d = pd.concat([d[d["valido"]].sort_values("desv_l", ascending=False), d[~d["valido"]]])
st.dataframe(pd.DataFrame({
    "Camión": d["patente"], "Fecha cierre": pd.to_datetime(d["fecha_cierre"]).dt.strftime("%d-%m-%Y"),
    "Km": d["km"], "Litros reales": d["litros"].round(0), "Litros esperados": d["litros_esperados"].round(0),
    "Desviación (l)": d["desv_l"].round(0), "Real / esperado (%)": d["desv_pct"].round(1),
    "Rendimiento (km/l)": d["rend"].round(2), "Estado": d["estado"],
}), hide_index=True, use_container_width=True, height=380)

boton_exportar({"Tramos": d.drop(columns=["estado"])}, f"combustible_{anio}_{mes:02d}", "g_comb")

leyenda_semaforo()
pie("Rendimiento calculado entre cargas completas en la base. Esperado = km / rendimiento de "
    "referencia del camión. Variaciones contra el mes anterior. Metas referenciales por validar. "
    "Datos ilustrativos.")
