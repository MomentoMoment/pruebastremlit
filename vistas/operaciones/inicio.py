"""Inicio: resumen del día y del mes, y accesos a las demás páginas."""
import calendar

import streamlit as st

from core import calculos as calc
from core import datos
from core.estilo import (NEGRO, ROJO, VERDE, GRIS_MEDIO, conteo, encabezado,
                         filtro_periodo, leyenda_semaforo, pie, tarjeta_kpi)
from core.formato import mes_anio

encabezado("Tablero de Operaciones — Inicio",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

anio, mes = filtro_periodo("inicio")

# --------------------------------------------------------------- flota hoy
st.subheader("Flota hoy")
ea = datos.estado_actual()
n = ea["estado"].value_counts()
c1, c2, c3, c4 = st.columns(4)
with c1:
    conteo("En viaje", int(n.get("en_viaje", 0)), NEGRO)
with c2:
    conteo("En base, disponibles", int(n.get("en_base", 0)), VERDE)
with c3:
    conteo("En taller", int(n.get("en_taller", 0)), ROJO)
with c4:
    conteo("Sin señal GPS", int(n.get("sin_senal", 0)), GRIS_MEDIO)
if st.button("Ver mapa de la flota →"):
    st.switch_page("vistas/operaciones/flota.py")

# --------------------------------------------------------------- indicadores del mes
st.subheader(f"Indicadores de {mes_anio(anio, mes)}")
ventas = datos.ventas_diarias()
act, ant, dia = calc.venta_mes(ventas, anio, mes)
v_act, v_ant = act["ingreso"].sum(), ant["ingreso"].sum()

a_ant, m_ant = calc.mes_anterior(anio, mes)
estado = datos.estado_diario()
f_act = calc.flota_mes(estado, anio, mes)
f_ant = calc.flota_mes(estado, a_ant, m_ant)

cond = datos.conductores_mes()
p_act = calc.produccion_conductores(cond, anio, mes)
p_ant = calc.produccion_conductores(cond, a_ant, m_ant)

comp = f"vs mismo período del mes anterior (días 1–{dia})"
k1, k2, k3, k4 = st.columns(4)
with k1:
    meta_prop = datos.METAS["venta_mensual"] * dia / calendar.monthrange(anio, mes)[1]  # proporcional a los días
    tarjeta_kpi("Venta del mes (a la fecha)", v_act, "$", meta=meta_prop,
                delta=(100 * (v_act / v_ant - 1)) if v_ant else None, unidad_delta="%",
                comparacion=comp)
with k2:
    if f_act["disponibilidad"] is None:
        tarjeta_kpi("% Disponibilidad de flota", None, "%", nota="Sin datos para el período")
    else:
        tarjeta_kpi("% Disponibilidad de flota", f_act["disponibilidad"], "%",
                    meta=datos.METAS["disponibilidad"],
                    delta=f_act["disponibilidad"] - (f_ant["disponibilidad"] or 0))
with k3:
    if f_act["dias_trabajados"] is None:
        tarjeta_kpi("% Días trabajados", None, "%", nota="Sin datos para el período")
    else:
        tarjeta_kpi("% Días trabajados", f_act["dias_trabajados"], "%",
                    meta=datos.METAS["dias_trabajados"],
                    delta=f_act["dias_trabajados"] - (f_ant["dias_trabajados"] or 0))
with k4:
    if p_act.empty:
        tarjeta_kpi("Ingreso promedio por conductor", None, "$", nota="Sin datos para el período")
    else:
        prom, prom_ant = p_act["ingreso"].mean(), p_ant["ingreso"].mean() if not p_ant.empty else None
        tarjeta_kpi("Ingreso promedio por conductor", prom, "$",
                    delta=(100 * (prom / prom_ant - 1)) if prom_ant else None, unidad_delta="%")

leyenda_semaforo()

# --------------------------------------------------------------- accesos
st.subheader("Ir a")
a1, a2, a3 = st.columns(3)
a1.page_link("vistas/operaciones/ventas.py", label="Ventas por cliente", icon=":material/payments:")
a2.page_link("vistas/operaciones/conductores.py", label="Desempeño de conductores", icon=":material/badge:")
a3.page_link("vistas/operaciones/control_flota.py", label="Control de flota", icon=":material/calendar_month:")

pie("Variaciones contra el mes anterior (en ventas, contra el mismo período del mes anterior). "
    "Metas referenciales por validar con la Jefatura de Operaciones. Datos ilustrativos.")
