"""Ventas: venta del mes por cliente vs el mismo período del mes anterior."""
import calendar

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import datos
from core.estilo import (CONFIG_GRAFICO, GRIS_MEDIO, GRIS_OSCURO, NEGRO, ROJO, ROJO_CLARO,
                         VERDE, encabezado, estilo_grafico, filtro_periodo, leyenda_semaforo,
                         pie, tarjeta_kpi, texto_estado)
from core.formato import fmt_clp, fmt_pct, mes_anio

encabezado("Tablero de Operaciones — Ventas",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

anio, mes = filtro_periodo("ventas")
ventas = datos.ventas_diarias()
clientes = sorted(ventas["cliente"].unique())
sel = st.multiselect("Cliente", clientes, default=clientes)
ventas = ventas[ventas["cliente"].isin(sel)]

act, ant, dia = calc.venta_mes(ventas, anio, mes)
if act.empty:
    st.info("No hay ventas para el período y clientes seleccionados.")
    st.stop()
a_ant, m_ant = calc.mes_anterior(anio, mes)
comp = f"vs mismo período del mes anterior (días 1–{dia})"
st.caption(f"Comparación: {mes_anio(anio, mes)} días 1–{dia} contra {mes_anio(a_ant, m_ant)} "
           f"días 1–{dia}.")

# --------------------------------------------------------------- tarjetas
v_act, v_ant = act["ingreso"].sum(), ant["ingreso"].sum()
n_act, n_ant = act["viajes"].sum(), ant["viajes"].sum()
k1, k2, k3 = st.columns(3)
with k1:
    tarjeta_kpi("Venta acumulada del mes", v_act, "$",
                meta=datos.METAS["venta_mensual"] * dia / calendar.monthrange(anio, mes)[1],
                delta=100 * (v_act / v_ant - 1) if v_ant else None, unidad_delta="%",
                comparacion=comp, nota="Meta referencial proporcional a los días transcurridos")
with k2:
    tarjeta_kpi("Viajes del mes", n_act, "", dec=0, delta=n_act - n_ant, unidad_delta="",
                comparacion=comp)
with k3:
    p_act = v_act / n_act if n_act else None
    p_ant = v_ant / n_ant if n_ant else None
    tarjeta_kpi("Ingreso promedio por viaje", p_act, "$",
                delta=100 * (p_act / p_ant - 1) if p_act and p_ant else None, unidad_delta="%",
                comparacion=comp)

# --------------------------------------------------------------- acumulado diario
def acumulado(df):
    s = df.groupby(pd.to_datetime(df["fecha"]).dt.day)["ingreso"].sum().cumsum()
    return s


s_act = acumulado(act)
s_ant_full = acumulado(calc.filtrar_mes(ventas, a_ant, m_ant))
dias_mes = calendar.monthrange(anio, mes)[1]
meta = datos.METAS["venta_mensual"]

fig = go.Figure()
fig.add_scatter(x=s_ant_full.index, y=s_ant_full.values, name=f"{mes_anio(a_ant, m_ant)} (mes anterior)",
                mode="lines", line=dict(color=GRIS_MEDIO, width=2))
fig.add_scatter(x=s_act.index, y=s_act.values, name=f"{mes_anio(anio, mes)} (actual)",
                mode="lines+markers", line=dict(color=NEGRO, width=3), marker=dict(size=5))
fig.add_scatter(x=[1, dias_mes], y=[meta / dias_mes, meta], name="Meta mensual (referencial)",
                mode="lines", line=dict(color=GRIS_OSCURO, width=1.5, dash="dash"))
fig.update_layout(title="Venta acumulada día a día ($)", hovermode="x unified")
fig.update_xaxes(title="Día del mes", dtick=2)
st.plotly_chart(estilo_grafico(fig, 380), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- por cliente
pc = (act.groupby("cliente")[["ingreso", "viajes"]].sum()
      .join(ant.groupby("cliente")["ingreso"].sum().rename("ingreso_ant"), how="outer")
      .fillna(0).sort_values("ingreso"))
pc["var_pct"] = 100 * (pc["ingreso"] / pc["ingreso_ant"].where(pc["ingreso_ant"] > 0) - 1)


def clave_var(v):
    if pd.isna(v):
        return "sin_meta"
    if v >= 0:
        return "cumple"
    return "alerta" if v > -10 else "no_cumple"


pc["estado"] = pc["var_pct"].map(clave_var)
colores = {"cumple": VERDE, "alerta": ROJO_CLARO, "no_cumple": ROJO, "sin_meta": GRIS_MEDIO}

c1, c2 = st.columns(2)
with c1:
    f = go.Figure()
    f.add_bar(y=pc.index, x=pc["ingreso_ant"], name="Mismo período mes anterior",
              orientation="h", marker_color=GRIS_MEDIO)
    f.add_bar(y=pc.index, x=pc["ingreso"], name="Mes actual", orientation="h", marker_color=NEGRO)
    f.update_layout(title="Venta por cliente ($)", barmode="group")
    st.plotly_chart(estilo_grafico(f, 420), use_container_width=True, config=CONFIG_GRAFICO)
with c2:
    f = go.Figure()
    f.add_bar(y=pc.index, x=pc["var_pct"], orientation="h",
              marker_color=pc["estado"].map(colores),
              text=[("▲ " if v >= 0 else "▼ ") + fmt_pct(abs(v)) if pd.notna(v) else "—"
                    for v in pc["var_pct"]],
              textposition="outside", showlegend=False)
    f.add_vline(x=0, line_color=NEGRO, line_width=1)
    f.update_layout(title="Variación por cliente (%) — verde sube, rojo claro baja hasta 10 %, rojo baja más")
    st.plotly_chart(estilo_grafico(f, 420), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- tabla
total = pc["ingreso"].sum()
tabla = pd.DataFrame({
    "Cliente": pc.index,
    "Viajes": pc["viajes"].astype(int).values,
    "Venta mes actual": pc["ingreso"].map(fmt_clp).values,
    "Venta mismo período mes anterior": pc["ingreso_ant"].map(fmt_clp).values,
    "Variación ($)": (pc["ingreso"] - pc["ingreso_ant"]).map(fmt_clp).values,
    "Variación (%)": pc["var_pct"].map(lambda v: fmt_pct(v) if pd.notna(v) else "—").values,
    "Estado": pc["estado"].map(texto_estado).values,
    "Participación": (100 * pc["ingreso"] / total).values,
}).sort_values("Participación", ascending=False)
st.subheader("Detalle por cliente")
st.dataframe(tabla, hide_index=True, use_container_width=True,
             column_config={"Participación": st.column_config.ProgressColumn(
                 "Participación en la venta", format="%.1f %%", min_value=0, max_value=100)})

leyenda_semaforo()
pie("Comparación con el mismo período del mes anterior. Metas referenciales por validar. "
    "Datos ilustrativos.")
