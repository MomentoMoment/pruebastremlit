"""Gerencia — Inicio: los cinco indicadores del mes, su tendencia y accesos."""
from datetime import date

import streamlit as st

from core import calculos as calc
from core import calculos_gerencia as cg
from core import datos
from core.estilo import (CONFIG_GRAFICO, encabezado, filtro_periodo, grafico_tendencia,
                         leyenda_semaforo, pie, tarjeta_kpi)
from core.formato import mes_anio

M = datos.METAS_GERENCIA

encabezado("Tablero de Gerencia — Inicio",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)       # último mes cerrado
anio, mes = filtro_periodo("g_inicio", anio_def=a_def, mes_def=m_def)
a_ant, m_ant = calc.mes_anterior(anio, mes)

v, t, o = datos.viajes(), datos.tramos_combustible(), datos.ordenes_taller()
va, vp = calc.filtrar_mes(v, anio, mes), calc.filtrar_mes(v, a_ant, m_ant)
ta, tp = (calc.filtrar_mes(t, anio, mes, col="fecha_cierre"),
          calc.filtrar_mes(t, a_ant, m_ant, col="fecha_cierre"))
oa, op = (calc.filtrar_mes(o, anio, mes, col="fecha_salida"),
          calc.filtrar_mes(o, a_ant, m_ant, col="fecha_salida"))

st.subheader(f"Indicadores de {mes_anio(anio, mes)}")
k = st.columns(5)
with k[0]:
    tarjeta_kpi("Margen directo por viaje", cg.margen(va), "%", meta=M["margen"],
                delta=cg.delta(cg.margen(va), cg.margen(vp)), nota="Costo directo estimado")
with k[1]:
    tarjeta_kpi("Rendimiento de combustible", cg.rendimiento(ta), "km/l", dec=2,
                meta=M["rendimiento"], delta=cg.delta(cg.rendimiento(ta), cg.rendimiento(tp)))
with k[2]:
    tarjeta_kpi("Costo de mantención por km", cg.costo_km(oa, ta), "$", meta=M["costo_km"],
                sentido="menor_mejor", unidad_delta="$",
                delta=cg.delta(cg.costo_km(oa, ta), cg.costo_km(op, tp)))
with k[3]:
    tarjeta_kpi("Proporción de costo preventivo", cg.pct_preventivo(oa), "%",
                meta=M["pct_preventivo"],
                delta=cg.delta(cg.pct_preventivo(oa), cg.pct_preventivo(op)))
with k[4]:
    tarjeta_kpi("Cumplimiento de mantenimiento preventivo", None, "%",
                nota="Disponible cuando se carguen las pautas de mantención")

leyenda_semaforo()

st.subheader("Ir a")
c1, c2, c3 = st.columns(3)
c1.page_link("vistas/gerencia/costos.py", label="Costos y margen", icon=":material/paid:")
c2.page_link("vistas/gerencia/combustible.py", label="Combustible", icon=":material/local_gas_station:")
c3.page_link("vistas/gerencia/mantencion.py", label="Mantención", icon=":material/build:")

st.subheader("Tendencia de los últimos 12 meses")
g1, g2 = st.columns(2)
g1.plotly_chart(grafico_tendencia(cg.serie_12m(cg.margen, anio, mes, (v, "fecha")),
                                  "Margen directo mensual (%)", M["margen"],
                                  f"Meta {M['margen']:.0f} %", " %"),
                use_container_width=True, config=CONFIG_GRAFICO)
g2.plotly_chart(grafico_tendencia(cg.serie_12m(cg.costo_km, anio, mes, (o, "fecha_salida"),
                                               (t, "fecha_cierre")),
                                  "Costo de mantención por km ($/km)", M["costo_km"],
                                  f"Meta ${M['costo_km']:.0f}/km", " $/km", dec=0),
                use_container_width=True, config=CONFIG_GRAFICO)

pie("Variaciones contra el mes anterior. Costo directo estimado: combustible y hoja de ruta "
    "asignados a cada viaje. Metas referenciales por validar con la Gerencia. Datos ilustrativos.")
