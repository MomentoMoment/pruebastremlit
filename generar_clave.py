"""Genera el hash de una contraseña para pegarlo en .streamlit/secrets.toml.

Uso:  python generar_clave.py
La contraseña se pide por teclado (no queda en el historial de la terminal).
"""
import getpass

from core.auth import generar_hash

if __name__ == "__main__":
    clave = getpass.getpass("Contraseña: ")
    if clave != getpass.getpass("Repetir contraseña: "):
        raise SystemExit("Las contraseñas no coinciden.")
    if len(clave) < 10:
        raise SystemExit("Use al menos 10 caracteres.")
    print("\nclave_hash =", f'"{generar_hash(clave)}"')
