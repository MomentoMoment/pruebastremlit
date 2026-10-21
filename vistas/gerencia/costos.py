"""Gerencia — Costos y margen: qué clientes, tramos y servicios dejan más o menos margen."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import calculos_gerencia as cg
from core import datos
from core.estilo import (CONFIG_GRAFICO, ESTADOS, GRIS_CLARO, GRIS_MEDIO, GRIS_OSCURO, NEGRO,
                         boton_exportar, encabezado, estado, estilo_grafico, filtro_periodo,
                         leyenda_semaforo, pie, tarjeta_kpi, texto_estado)
from core.formato import fmt_clp, fmt_num, mes_anio

META = datos.METAS_GERENCIA["margen"]
COMPONENTES = {"costo_combustible": ("Combustible", NEGRO), "costo_comision": ("Comisión", GRIS_OSCURO),
               "costo_hoja_ruta": ("Hoja de ruta (viáticos)", GRIS_MEDIO),
               "costo_peajes": ("Peajes", GRIS_CLARO)}

encabezado("Tablero de Gerencia — Costos y margen",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)
anio, mes = filtro_periodo("g_costos", anio_def=a_def, mes_def=m_def)
v = datos.viajes()
f1, f2 = st.columns(2)
serv = f1.multiselect("Tipo de servicio", sorted(v["tipo_servicio"].unique()),
                      placeholder="Todos los servicios")
cli = f2.multiselect("Cliente", sorted(v["cliente"].unique()), placeholder="Todos los clientes")
if serv:
    v = v[v["tipo_servicio"].isin(serv)]
if cli:
    v = v[v["cliente"].isin(cli)]

a_ant, m_ant = calc.mes_anterior(anio, mes)
va, vp = calc.filtrar_mes(v, anio, mes), calc.filtrar_mes(v, a_ant, m_ant)
if va.empty:
    st.info("No hay viajes para el período y filtros seleccionados.")
    st.stop()

st.caption("Costo directo **estimado**: el combustible y la hoja de ruta se asignan a cada viaje "
           "mediante reglas de prorrateo; no se registran por viaje en el ERP.")

# --------------------------------------------------------------- tarjetas
def pct_var(a, b):
    return 100 * (a / b - 1) if b else None


k = st.columns(4)
with k[0]:
    tarjeta_kpi("Ingreso del mes", va["ingreso"].sum(), "$", unidad_delta="%",
                delta=pct_var(va["ingreso"].sum(), vp["ingreso"].sum()))
with k[1]:
    tarjeta_kpi("Costo directo estimado", va["costo_directo"].sum(), "$", sentido="menor_mejor",
                unidad_delta="%", delta=pct_var(va["costo_directo"].sum(), vp["costo_directo"].sum()))
with k[2]:
    tarjeta_kpi("Margen directo", cg.margen(va), "%", meta=META,
                delta=cg.delta(cg.margen(va), cg.margen(vp)))
with k[3]:
    tarjeta_kpi("Viajes del mes", len(va), "", dec=0, delta=len(va) - len(vp), unidad_delta="")


# --------------------------------------------------------------- agregados
def agregar(df, por):
    g = df.groupby(por).agg(viajes=("ingreso", "size"), ingreso=("ingreso", "sum"),
                            costo=("costo_directo", "sum"))
    g["margen_pesos"] = g["ingreso"] - g["costo"]
    g["margen_pct"] = 100 * g["margen_pesos"] / g["ingreso"]
    g["estado"] = g["margen_pct"].map(lambda x: estado(x, META))
    return g


colores = {k: c for k, (_, c) in ESTADOS.items()}
c1, c2 = st.columns(2)
with c1:
    g = agregar(va, "cliente").sort_values("margen_pct", ascending=False)
    f = go.Figure(go.Bar(y=g.index, x=g["margen_pct"], orientation="h",
                         marker_color=g["estado"].map(colores),
                         text=[f"{fmt_num(x, 1)} %" for x in g["margen_pct"]], textposition="outside"))
    f.add_vline(x=META, line_dash="dash", line_color=NEGRO, annotation_text=f"Meta {META:.0f} %")
    f.update_layout(title=f"Margen directo por cliente (%) — {mes_anio(anio, mes)}", showlegend=False)
    st.plotly_chart(estilo_grafico(f, 420), use_container_width=True, config=CONFIG_GRAFICO)
with c2:
    comp = va.groupby("tipo_servicio")[list(COMPONENTES)].sum()
    comp_pct = comp.div(comp.sum(axis=1), axis=0) * 100
    f = go.Figure()
    for col, (nombre, color) in COMPONENTES.items():
        f.add_bar(x=comp_pct.index, y=comp_pct[col], name=nombre, marker_color=color,
                  marker_line=dict(color=GRIS_MEDIO, width=1),
                  text=[f"{fmt_num(x, 0)} %" for x in comp_pct[col]], textposition="inside",
                  textfont=dict(color="white" if color in (NEGRO, GRIS_OSCURO) else NEGRO))
    f.update_layout(title="Composición del costo directo por tipo de servicio (%)", barmode="stack")
    f.update_yaxes(range=[0, 100], ticksuffix=" %")
    st.plotly_chart(estilo_grafico(f, 420), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- tabla por tramo
st.subheader("Detalle por tramo y servicio — ordenado de menor a mayor margen")
g = agregar(va, ["tramo", "tipo_servicio"]).sort_values("margen_pct").reset_index()
st.dataframe(pd.DataFrame({
    "Tramo": g["tramo"], "Tipo de servicio": g["tipo_servicio"], "Viajes": g["viajes"],
    "Ingreso": g["ingreso"].map(fmt_clp), "Costo directo estimado": g["costo"].map(fmt_clp),
    "Margen ($)": g["margen_pesos"].map(fmt_clp), "Margen (%)": g["margen_pct"].round(1),
    "Estado": g["estado"].map(texto_estado),
}), hide_index=True, use_container_width=True, height=380,
    column_config={"Margen (%)": st.column_config.ProgressColumn(format="%.1f %%", min_value=0,
                                                                 max_value=50)})

boton_exportar({
    "Por tramo": g.rename(columns={"margen_pesos": "margen", "margen_pct": "margen_pct"}),
    "Por cliente": agregar(va, "cliente").reset_index(),
    "Viajes": va,
}, f"costos_margen_{anio}_{mes:02d}", "g_costos")

leyenda_semaforo()
pie("Margen = (Σ ingreso − Σ costo directo estimado) / Σ ingreso. Variaciones contra el mes "
    "anterior. Metas referenciales por validar con la Gerencia. Datos ilustrativos.")
