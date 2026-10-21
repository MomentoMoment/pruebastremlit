"""Acceso con usuario y contraseña.

- Las contraseñas no se guardan: solo su hash PBKDF2-SHA256 con sal, en
  .streamlit/secrets.toml (fuera del código).
- Tras 5 intentos fallidos se bloquea el formulario 60 segundos.
- Para producción se puede reemplazar por st.login (OpenID Connect) si la
  empresa tiene Microsoft 365 o Google Workspace.
"""
import hashlib
import hmac
import os
import time

import streamlit as st

ITERACIONES = 200_000
MAX_INTENTOS = 5
BLOQUEO_SEG = 60


def generar_hash(clave: str) -> str:
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, ITERACIONES)
    return f"{sal.hex()}${h.hex()}"


def _verificar(clave: str, guardado: str) -> bool:
    try:
        sal_hex, hash_hex = guardado.split("$")
    except ValueError:
        return False
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal_hex), ITERACIONES)
    return hmac.compare_digest(h.hex(), hash_hex)


def usuario_actual():
    return st.session_state.get("usuario")


def cerrar_sesion():
    for k in ("usuario", "nombre_usuario", "rol"):
        st.session_state.pop(k, None)
    st.rerun()


def pagina_acceso():
    """Pantalla de login. Es la única página visible sin sesión."""
    from core.estilo import aplicar_estilo, ROJO, GRIS_OSCURO

    aplicar_estilo()
    _, centro, _ = st.columns([1, 1.2, 1])
    with centro:
        st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align:center">
                  <div class="logo-box" style="margin:0 auto 12px auto">LOGO</div>
                  <h2 style="margin:0">Tableros de gestión</h2>
                  <p style="color:{GRIS_OSCURO};margin:4px 0 0 0">Acceso restringido</p>
                  <div style="height:3px;background:{ROJO};margin:12px 0 4px 0"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            bloqueado_hasta = st.session_state.get("bloqueado_hasta", 0)
            if time.time() < bloqueado_hasta:
                st.error(f"Demasiados intentos. Espere {int(bloqueado_hasta - time.time())} segundos.")
                return

            with st.form("login", clear_on_submit=False):
                usuario = st.text_input("Usuario")
                clave = st.text_input("Contraseña", type="password")
                entrar = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

            if entrar:
                usuarios = st.secrets.get("usuarios", {})
                datos = usuarios.get(usuario)
                if datos and _verificar(clave, datos.get("clave_hash", "")):
                    st.session_state["usuario"] = usuario
                    st.session_state["nombre_usuario"] = datos.get("nombre", usuario)
                    st.session_state["rol"] = datos.get("rol", "")
                    st.session_state["intentos"] = 0
                    st.rerun()
                else:
                    n = st.session_state.get("intentos", 0) + 1
                    st.session_state["intentos"] = n
                    if n >= MAX_INTENTOS:
                        st.session_state["bloqueado_hasta"] = time.time() + BLOQUEO_SEG
                        st.session_state["intentos"] = 0
                    st.error("Usuario o contraseña incorrectos.")
