"""Datos FICTICIOS del tablero de Gerencia. Ninguna cifra, patente ni cliente es real.

Las columnas son las que entregarán después las consultas al data warehouse:
- viajes():              comun.v_fact_viaje + costos asignados (combustible, peajes, ...)
- tramos_combustible():  fact_tramo_combustible (bloques entre cargas en base)
- ordenes_taller():      fact_orden_taller + costo de fact_consumo_repuesto (sin combustible)
"""
from datetime import date

import numpy as np
import pandas as pd

from core.datos_demo import CLIENTES, TRAMOS, patentes

TIPOS_SERVICIO = ["Frío", "Seco", "Multitemperatura"]


def _rng(semilla):
    return np.random.default_rng(100 + semilla)


def _meses(n=25):
    hoy = date.today()
    return pd.period_range(end=pd.Period(year=hoy.year, month=hoy.month, freq="M"), periods=n, freq="M")


def patentes_ramplas():
    r = _rng(9)
    return [f"R{''.join(r.choice(list('BCDFGHJKLPRSTVWXYZ'), 3))}-{r.integers(10, 99)}" for _ in range(30)]


def viajes():
    """Una fila por viaje, con ingreso y costo directo estimado por componente."""
    r = _rng(1)
    hoy = date.today()
    filas = []
    margen_cli = dict(zip(CLIENTES, r.normal(0.19, 0.07, len(CLIENTES))))
    peaje_tramo = dict(zip(TRAMOS, r.uniform(15_000, 80_000, len(TRAMOS))))
    for p in _meses():
        n = int(r.normal(1250, 60))
        dias_mes = p.days_in_month if (p.year, p.month) != (hoy.year, hoy.month) else hoy.day
        dia = r.integers(1, dias_mes + 1, n)
        cli = r.choice(CLIENTES, n)
        tramo = r.choice(TRAMOS, n)
        serv = r.choice(TIPOS_SERVICIO, n, p=[0.35, 0.5, 0.15])
        ingreso = np.maximum(80_000, r.normal(325_000, 90_000, n)).round(-3)
        margen = np.array([margen_cli[c] for c in cli]) + r.normal(0, 0.06, n) - 0.03 * (serv == "Frío")
        costo = ingreso * (1 - margen)
        peajes = np.array([peaje_tramo[t] for t in tramo]) * r.uniform(0.9, 1.1, n)
        comision = ingreso * 0.11
        hoja = costo * r.uniform(0.08, 0.13, n)
        combustible = np.maximum(costo - peajes - comision - hoja, costo * 0.35)
        filas.append(pd.DataFrame({
            "fecha": [date(p.year, p.month, int(d)) for d in dia],
            "cliente": cli, "tramo": tramo, "tipo_servicio": serv, "ingreso": ingreso,
            "costo_combustible": combustible.round(-2), "costo_comision": comision.round(-2),
            "costo_hoja_ruta": hoja.round(-2), "costo_peajes": peajes.round(-2),
        }))
    v = pd.concat(filas, ignore_index=True)
    v["costo_directo"] = v[["costo_combustible", "costo_comision", "costo_hoja_ruta", "costo_peajes"]].sum(axis=1)
    return v


def tramos_combustible():
    """Una fila por camión y tramo entre cargas en base (estanque lleno)."""
    r = _rng(2)
    filas = []
    rend_base = dict(zip(patentes(), r.normal(2.65, 0.17, 44)))
    for p in _meses():
        for pat, rb in rend_base.items():
            for _ in range(int(r.integers(10, 16))):
                km = float(r.uniform(400, 1400))
                rend = rb + r.normal(0, 0.12)
                if r.random() < 0.035:                      # errores de registro
                    rend = float(r.choice([0.6, 6.5, 8.0]))
                litros = km / rend
                filas.append({
                    "patente": pat,
                    "fecha_cierre": date(p.year, p.month, int(r.integers(1, p.days_in_month + 1))),
                    "km": round(km), "litros": round(litros, 1),
                    "litros_esperados": round(km / 2.70, 1),   # km / rendimiento de referencia
                    "valido": 1 <= rend <= 5,
                })
    t = pd.DataFrame(filas)
    hoy = date.today()
    return t[pd.to_datetime(t["fecha_cierre"]) <= pd.Timestamp(hoy)]


def ordenes_taller():
    """Una fila por OT cerrada: equipo, tipo, días en taller y costo de materiales."""
    r = _rng(3)
    equipos = [(p, "Tracto") for p in patentes()] + [(p, "Rampla") for p in patentes_ramplas()]
    filas = []
    n_ot = 0
    for p in _meses():
        for pat, tipo_eq in equipos:
            for _ in range(int(r.poisson(1.1 if tipo_eq == "Tracto" else 0.6))):
                n_ot += 1
                prev = r.random() < 0.72
                dias = r.gamma(2, 0.85) if prev else r.gamma(2, 1.9)
                costo = r.gamma(2, 640_000 if prev else 520_000)
                filas.append({
                    "nro_ot": f"OT-{20000 + n_ot}", "patente": pat, "tipo_equipo": tipo_eq,
                    "fecha_salida": date(p.year, p.month, int(r.integers(1, p.days_in_month + 1))),
                    "tipo_mantencion": "PREVENTIVA" if prev else "CORRECTIVA",
                    "dias_taller": round(dias, 2), "costo": round(costo, -3),
                })
    o = pd.DataFrame(filas)
    return o[pd.to_datetime(o["fecha_salida"]) <= pd.Timestamp(date.today())]


# Metas referenciales (por validar con la Gerencia). Después vendrán de dw.meta.
METAS = {
    "margen": 20.0,               # % — mayor es mejor
    "rendimiento": 2.70,          # km/l — mayor es mejor
    "consumo_vs_esperado": 100.0, # % real / esperado — menor es mejor
    "costo_km": 130.0,            # $/km — menor es mejor
    "pct_preventivo": 80.0,       # % — mayor es mejor
    "dias_preventiva": 2.0,       # días — menor es mejor
    "dias_correctiva": 3.0,       # días — menor es mejor
    "cumplimiento_preventivo": None,  # sin datos de programación todavía
}
