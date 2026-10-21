"""Tableros de gestión — Transportes Callegari (versión de diseño, datos ficticios).

Ejecutar:  streamlit run app.py

Navegación según el rol del usuario (definido en .streamlit/secrets.toml):
- Sin sesión: solo la página de acceso (no hay menú).
- rol "gerencia":    Inicio, Costos y margen, Combustible, Mantención.
- rol "operaciones": Inicio, Flota en tiempo real, Ventas, Conductores, Control de flota.
Cada rol ve SOLO su tablero: las páginas del otro no existen en su sesión.
"""
import streamlit as st

from core.auth import cerrar_sesion, pagina_acceso, usuario_actual

st.set_page_config(page_title="Tableros de gestión — Callegari",
                   page_icon=":material/local_shipping:", layout="wide")

if not usuario_actual():
    st.navigation([st.Page(pagina_acceso, title="Acceso", icon=":material/lock:")],
                  position="hidden").run()
    st.stop()

TABLEROS = {
    "gerencia": {
        "Tablero de Gerencia": [
            st.Page("vistas/gerencia/inicio.py", title="Inicio", icon=":material/home:", default=True),
            st.Page("vistas/gerencia/costos.py", title="Costos y margen", icon=":material/paid:"),
            st.Page("vistas/gerencia/combustible.py", title="Combustible", icon=":material/local_gas_station:"),
            st.Page("vistas/gerencia/mantencion.py", title="Mantención", icon=":material/build:"),
        ]
    },
    "operaciones": {
        "Tablero de Operaciones": [
            st.Page("vistas/operaciones/inicio.py", title="Inicio", icon=":material/home:", default=True),
            st.Page("vistas/operaciones/flota.py", title="Flota en tiempo real", icon=":material/map:"),
            st.Page("vistas/operaciones/ventas.py", title="Ventas", icon=":material/payments:"),
            st.Page("vistas/operaciones/conductores.py", title="Conductores", icon=":material/badge:"),
            st.Page("vistas/operaciones/control_flota.py", title="Control de flota",
                    icon=":material/calendar_month:"),
        ]
    },
}

rol = st.session_state.get("rol", "")
if rol not in TABLEROS:
    st.error("Su usuario no tiene un tablero asignado. Contacte al administrador.")
    if st.button("Cerrar sesión"):
        cerrar_sesion()
    st.stop()

pg = st.navigation(TABLEROS[rol])

with st.sidebar:
    st.caption(f"Sesión: **{st.session_state.get('nombre_usuario', '')}**")
    if st.button("Cerrar sesión", icon=":material/logout:", use_container_width=True):
        cerrar_sesion()
    st.caption("Datos ilustrativos · versión de diseño")

pg.run()
