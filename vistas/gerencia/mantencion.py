"""Gerencia — Mantención: costo por km, preventivo vs correctivo y tiempo en taller."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import calculos_gerencia as cg
from core import datos
from core.estilo import (CONFIG_GRAFICO, GRIS_OSCURO, NEGRO, VERDE, boton_exportar, encabezado,
                         estado, estilo_grafico, filtro_periodo, leyenda_semaforo, pie,
                         tarjeta_kpi, texto_estado)
from core.formato import MESES_CORTO, fmt_clp, fmt_num

M = datos.METAS_GERENCIA
COLOR_TIPO = {"PREVENTIVA": VERDE, "CORRECTIVA": NEGRO}

encabezado("Tablero de Gerencia — Mantención",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)
anio, mes = filtro_periodo("g_mant", anio_def=a_def, mes_def=m_def)
o, t = datos.ordenes_taller(), datos.tramos_combustible()
tipo_eq = st.selectbox("Tipo de equipo", ["Todos", "Tracto", "Rampla"])
if tipo_eq != "Todos":
    o = o[o["tipo_equipo"] == tipo_eq]

a_ant, m_ant = calc.mes_anterior(anio, mes)
oa, op = (calc.filtrar_mes(o, anio, mes, col="fecha_salida"),
          calc.filtrar_mes(o, a_ant, m_ant, col="fecha_salida"))
ta, tp = (calc.filtrar_mes(t, anio, mes, col="fecha_cierre"),
          calc.filtrar_mes(t, a_ant, m_ant, col="fecha_cierre"))
if oa.empty:
    st.info("No hay órdenes de trabajo cerradas en el período seleccionado.")
    st.stop()

st.markdown(f"<span style='color:{VERDE};font-size:18px'>■</span> Preventiva &nbsp;&nbsp; "
            f"<span style='color:{NEGRO};font-size:18px'>■</span> Correctiva &nbsp;&nbsp; "
            f"<span style='color:{GRIS_OSCURO}'>- - -</span> Meta", unsafe_allow_html=True)

# --------------------------------------------------------------- tarjetas
k = st.columns(4)
with k[0]:
    if tipo_eq == "Rampla":
        tarjeta_kpi("Costo de mantención por km", None, "$",
                    nota="No aplica a ramplas: los km se miden en el tracto")
    else:
        tarjeta_kpi("Costo de mantención por km (tractos)", cg.costo_km(oa, ta), "$",
                    meta=M["costo_km"], sentido="menor_mejor", unidad_delta="$",
                    delta=cg.delta(cg.costo_km(oa, ta), cg.costo_km(op, tp)))
with k[1]:
    tarjeta_kpi("Proporción de costo preventivo", cg.pct_preventivo(oa), "%", meta=M["pct_preventivo"],
                delta=cg.delta(cg.pct_preventivo(oa), cg.pct_preventivo(op)))
with k[2]:
    dp, dc = cg.dias_promedio(oa, "PREVENTIVA"), cg.dias_promedio(oa, "CORRECTIVA")
    tarjeta_kpi("Tiempo en taller — preventiva", dp, "días", meta=M["dias_preventiva"],
                sentido="menor_mejor", delta=cg.delta(dp, cg.dias_promedio(op, "PREVENTIVA")))
    st.write("")
    tarjeta_kpi("Tiempo en taller — correctiva", dc, "días", meta=M["dias_correctiva"],
                sentido="menor_mejor", delta=cg.delta(dc, cg.dias_promedio(op, "CORRECTIVA")))
with k[3]:
    tarjeta_kpi("Cumplimiento de mantenimiento preventivo", None, "%",
                nota="Disponible cuando se carguen las pautas de mantención")

# --------------------------------------------------------------- gráficos
c1, c2 = st.columns(2)
with c1:
    fin = pd.Period(year=anio, month=mes, freq="M")
    filas = []
    for p in pd.period_range(fin - 11, fin, freq="M"):
        x = calc.filtrar_mes(o, p.year, p.month, col="fecha_salida")
        for tipo in ("PREVENTIVA", "CORRECTIVA"):
            filas.append({"mes": f"{MESES_CORTO[p.month - 1]}-{p.year}", "tipo": tipo,
                          "costo": x.loc[x["tipo_mantencion"] == tipo, "costo"].sum()})
    s = pd.DataFrame(filas)
    f = go.Figure()
    for tipo in ("PREVENTIVA", "CORRECTIVA"):
        y = s[s["tipo"] == tipo]
        f.add_bar(x=y["mes"], y=y["costo"], name=tipo.capitalize(), marker_color=COLOR_TIPO[tipo])
    f.update_layout(title="Costo de mantención mensual por tipo ($) — últimos 12 meses", barmode="stack")
    st.plotly_chart(estilo_grafico(f, 400), use_container_width=True, config=CONFIG_GRAFICO)
with c2:
    g = oa.groupby(["tipo_equipo", "tipo_mantencion"])["dias_taller"].mean().reset_index()
    f = go.Figure()
    for tipo in ("PREVENTIVA", "CORRECTIVA"):
        y = g[g["tipo_mantencion"] == tipo]
        f.add_bar(x=y["tipo_equipo"], y=y["dias_taller"], name=tipo.capitalize(),
                  marker_color=COLOR_TIPO[tipo], text=[fmt_num(v, 1) for v in y["dias_taller"]],
                  textposition="outside")
    f.add_hline(y=M["dias_preventiva"], line_dash="dash", line_color=VERDE, line_width=1,
                annotation_text=f"Meta preventiva {fmt_num(M['dias_preventiva'], 0)} días",
                annotation_position="top left")
    f.add_hline(y=M["dias_correctiva"], line_dash="dash", line_color=GRIS_OSCURO, line_width=1,
                annotation_text=f"Meta correctiva {fmt_num(M['dias_correctiva'], 0)} días",
                annotation_position="top right")
    f.update_layout(title="Tiempo promedio en taller (días) por tipo de equipo", barmode="group")
    st.plotly_chart(estilo_grafico(f, 400), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- tabla por equipo
st.subheader("Equipos con mayor costo de mantención")
km = ta[ta["valido"]].groupby("patente")["km"].sum()
e = oa.pivot_table(index=["patente", "tipo_equipo"], columns="tipo_mantencion", values="costo",
                   aggfunc="sum", fill_value=0).reset_index()
for col in ("PREVENTIVA", "CORRECTIVA"):
    if col not in e:
        e[col] = 0
e["total"] = e["PREVENTIVA"] + e["CORRECTIVA"]
e["n_ot"] = e["patente"].map(oa.groupby("patente").size())
e["dias"] = e["patente"].map(oa.groupby("patente")["dias_taller"].sum())
e["km"] = e["patente"].map(km)
e["costo_km"] = e["total"] / e["km"]
e["estado"] = [texto_estado(estado(x, M["costo_km"], "menor_mejor")) if pd.notna(x) else "— (rampla)"
               for x in e["costo_km"]]
e = e.sort_values("total", ascending=False)
st.dataframe(pd.DataFrame({
    "Equipo": e["patente"], "Tipo": e["tipo_equipo"], "Km del mes": e["km"].map(lambda x: fmt_num(x, 0) if pd.notna(x) else "—"),
    "Costo preventivo": e["PREVENTIVA"].map(fmt_clp), "Costo correctivo": e["CORRECTIVA"].map(fmt_clp),
    "Costo total": e["total"].map(fmt_clp),
    "Costo por km": e["costo_km"].map(lambda x: f"${fmt_num(x, 0)}" if pd.notna(x) else "—"),
    "N.º OT": e["n_ot"], "Días en taller": e["dias"].round(1), "Estado": e["estado"],
}), hide_index=True, use_container_width=True, height=380)

boton_exportar({"Por equipo": e, "Órdenes de trabajo": oa}, f"mantencion_{anio}_{mes:02d}", "g_mant")

leyenda_semaforo()
pie("Costo de materiales consumidos en OT, sin combustible. Costo por km solo para tractos (los km "
    "se miden en el tracto). Variaciones contra el mes anterior. Metas referenciales por validar. "
    "Datos ilustrativos.")
