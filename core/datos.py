"""Punto único de acceso a los datos para todas las páginas.

HOY:     usa core/datos_demo.py (datos ficticios).
DESPUÉS: cambiar FUENTE a "dw" y completar las consultas SQL marcadas con
         TODO; las páginas no se tocan porque las columnas son las mismas.
"""
import streamlit as st

from core import datos_demo, datos_demo_gerencia

FUENTE = "demo"   # "demo" | "dw"
METAS = datos_demo.METAS                       # operaciones
METAS_GERENCIA = datos_demo_gerencia.METAS     # gerencia


@st.cache_data(ttl=30, show_spinner=False)       # tiempo real: se refresca cada 30 s
def estado_actual():
    if FUENTE == "demo":
        return datos_demo.estado_actual()
    # TODO: API del GPS + estado del ERP (viaje abierto / OT abierta) unidos por patente
    raise NotImplementedError


@st.cache_data(ttl=3600, show_spinner=False)
def ventas_diarias():
    if FUENTE == "demo":
        return datos_demo.ventas_diarias()
    # TODO: SELECT fecha, cliente, COUNT(*) viajes, SUM(ingreso) ... FROM dw.fact_viaje ...
    raise NotImplementedError


@st.cache_data(ttl=3600, show_spinner=False)
def conductores_mes():
    if FUENTE == "demo":
        return datos_demo.conductores_mes()
    # TODO: viajes e ingreso por conductor y mes + km y litros de los tramos asignados
    raise NotImplementedError


@st.cache_data(ttl=3600, show_spinner=False)
def estado_diario():
    if FUENTE == "demo":
        return datos_demo.estado_diario()
    # TODO: SELECT ... FROM dw.fact_estado_diario_equipo JOIN dw.dim_equipo ...
    raise NotImplementedError


# ------------------------------------------------------------------ gerencia
@st.cache_data(ttl=3600, show_spinner=False)
def viajes():
    if FUENTE == "demo":
        return datos_demo_gerencia.viajes()
    # TODO: comun.v_fact_viaje + costos asignados (combustible, comisión, hoja de ruta, peajes)
    raise NotImplementedError


@st.cache_data(ttl=3600, show_spinner=False)
def tramos_combustible():
    if FUENTE == "demo":
        return datos_demo_gerencia.tramos_combustible()
    # TODO: SELECT ... FROM fact_tramo_combustible JOIN dim_equipo ...
    raise NotImplementedError


@st.cache_data(ttl=3600, show_spinner=False)
def ordenes_taller():
    if FUENTE == "demo":
        return datos_demo_gerencia.ordenes_taller()
    # TODO: fact_orden_taller + SUM(costo) de fact_consumo_repuesto sin combustible
    raise NotImplementedError


def fecha_actualizacion():
    from datetime import datetime
    return datetime.now().strftime("%d-%m-%Y %H:%M")
