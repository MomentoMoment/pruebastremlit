"""Datos FICTICIOS para revisar el diseño. Ninguna cifra, patente, cliente
ni conductor es real.

Cada función devuelve un DataFrame con las mismas columnas que entregará
después la consulta SQL al data warehouse, así que al pasar a datos reales
solo se reemplaza este módulo (ver core/datos.py).
"""
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

N_CAMIONES = 44
N_CONDUCTORES = 40
CLIENTES = [f"Cliente {c}" for c in "ABCDEFGHIJ"]
GRUPOS = ["Larga distancia norte", "Regional Coquimbo", "Frío"]
BASE = (-29.9701, -71.2645)  # base Coquimbo

# Puntos aproximados de la Ruta 5 (sur → norte), para ubicar camiones en ruta
RUTA5 = [(-35.43, -71.66), (-34.17, -70.74), (-33.45, -70.66), (-32.45, -71.24),
         (-31.91, -71.51), (-30.60, -71.20), (-29.97, -71.26), (-29.90, -71.25),
         (-28.57, -70.76), (-27.37, -70.33), (-26.35, -70.62), (-25.40, -70.48),
         (-23.65, -70.40), (-22.46, -68.93)]
TRAMOS = ["Coquimbo – Santiago", "Santiago – Coquimbo", "Coquimbo – Antofagasta",
          "Santiago – Antofagasta", "Antofagasta – Calama", "Coquimbo – Copiapó",
          "Santiago – Vallenar", "Coquimbo – Rancagua"]


def _rng(semilla):
    return np.random.default_rng(42 + semilla)


def patentes():
    r = _rng(0)
    letras = "BCDFGHJKLPRSTVWXYZ"
    vistas, salida = set(), []
    while len(salida) < N_CAMIONES:
        p = "".join(r.choice(list(letras), 4)) + "-" + f"{r.integers(10, 99)}"
        if p not in vistas:
            vistas.add(p)
            salida.append(p)
    return salida


def _punto_en_ruta(r):
    i = r.integers(0, len(RUTA5) - 1)
    t = r.random()
    (a1, o1), (a2, o2) = RUTA5[i], RUTA5[i + 1]
    return a1 + (a2 - a1) * t + r.normal(0, 0.01), o1 + (o2 - o1) * t + r.normal(0, 0.01)


def estado_actual():
    """Una fila por camión: estado según ERP + última posición GPS."""
    r = _rng(1)
    ahora = datetime.now().replace(microsecond=0)
    estados = ["en_viaje"] * 31 + ["en_base"] * 9 + ["en_taller"] * 4
    filas = []
    for i, pat in enumerate(patentes()):
        est = estados[i]
        if est == "en_viaje":
            lat, lon = _punto_en_ruta(r)
            tramo, cliente = r.choice(TRAMOS), r.choice(CLIENTES)
        else:
            lat, lon = BASE[0] + r.normal(0, 0.004), BASE[1] + r.normal(0, 0.004)
            tramo, cliente = "—", "—"
        minutos = int(r.integers(0, 6))
        sin_senal = i in (5, 22)          # dos camiones sin señal GPS
        if sin_senal:
            minutos = int(r.integers(45, 300))
        filas.append({
            "patente": pat,
            "estado": "sin_senal" if sin_senal else est,
            "estado_erp": est,
            "lat": lat, "lon": lon,
            "conductor": f"Conductor {i + 1:02d}" if est == "en_viaje" else "—",
            "viaje": tramo, "cliente": cliente,
            "ultima_posicion": ahora - timedelta(minutes=minutos),
            "ultima_carga": (ahora - timedelta(hours=int(r.integers(2, 90)))).strftime("%d-%m-%Y")
                            + (" · Base Coquimbo" if r.random() < 0.7 else " · En ruta"),
            "ot_abierta": f"OT-{int(r.integers(10000, 99999))}" if est == "en_taller" else "—",
        })
    return pd.DataFrame(filas)


def ventas_diarias():
    """Una fila por día y cliente: viajes e ingreso. Desde hace 26 meses hasta hoy."""
    r = _rng(2)
    hoy = date.today()
    dias = pd.date_range(date(hoy.year - 2, 1, 1), hoy, freq="D")
    peso = r.dirichlet(np.ones(len(CLIENTES)) * 2)
    filas = []
    for d in dias:
        tendencia = 1 + 0.004 * ((d.year - hoy.year) * 12 + d.month - hoy.month)
        base_dia = 13_800_000 * tendencia * (0.55 if d.dayofweek == 6 else 1.0)
        for c, w in zip(CLIENTES, peso):
            ingreso = max(0, r.normal(base_dia * w, base_dia * w * 0.35))
            viajes = int(round(ingreso / r.normal(323_000, 30_000)))
            filas.append({"fecha": d.date(), "cliente": c, "viajes": max(viajes, 0),
                          "ingreso": round(ingreso, -3)})
    return pd.DataFrame(filas)


def conductores_mes():
    """Una fila por conductor y mes: viajes, ingreso, km y litros."""
    r = _rng(3)
    hoy = date.today()
    meses = pd.period_range(f"{hoy.year - 1}-01", f"{hoy.year}-{hoy.month:02d}", freq="M")
    nivel = r.normal(1.0, 0.18, N_CONDUCTORES)
    rend = r.normal(2.65, 0.18, N_CONDUCTORES)
    grupo = [GRUPOS[i % 3] for i in range(N_CONDUCTORES)]
    filas = []
    for p in meses:
        for i in range(N_CONDUCTORES):
            ingreso = max(2e6, r.normal(9_200_000 * nivel[i], 900_000))
            km = max(2000, r.normal(11_500 * nivel[i], 1500))
            filas.append({"anio": p.year, "mes": p.month,
                          "conductor": f"Conductor {i + 1:02d}", "grupo": grupo[i],
                          "viajes": int(ingreso / 320_000), "ingreso": round(ingreso, -3),
                          "km": round(km), "litros": round(km / max(1.9, r.normal(rend[i], 0.06)))})
    return pd.DataFrame(filas)


def estado_diario():
    """Una fila por camión y día (como dw.fact_estado_diario_equipo)."""
    r = _rng(4)
    hoy = date.today()
    dias = pd.date_range(date(hoy.year - 1, 1, 1), hoy - timedelta(days=1), freq="D")
    filas = []
    for j, pat in enumerate(patentes()):
        prob_taller = r.uniform(0.03, 0.14)
        prob_viaje = r.uniform(0.80, 0.95)
        racha = 0
        for d in dias:
            if racha > 0:
                racha -= 1
                en_taller = 1
            elif r.random() < prob_taller / 3:
                racha = int(r.integers(1, 5))
                en_taller = 1
            else:
                en_taller = 0
            horas = float(r.uniform(8, 24)) if en_taller else float(r.choice([0, 0, 0, 2, 4]))
            con_viaje = 0 if en_taller else int(r.random() < prob_viaje)
            filas.append({"fecha": d.date(), "patente": pat, "horas_taller": round(horas, 1),
                          "en_taller": en_taller, "con_viaje": con_viaje})
    return pd.DataFrame(filas)


# Metas referenciales (por validar con la Jefatura de Operaciones).
# Después vendrán de la tabla dw.meta.
METAS = {
    "venta_mensual": 380_000_000,
    "disponibilidad": 92.0,
    "dias_trabajados": 85.0,
    "rendimiento": 2.70,
    "produccion": 100.0,
}
