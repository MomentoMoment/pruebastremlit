"""Indicadores del tablero de Gerencia. Siempre Σ numerador / Σ denominador."""
import pandas as pd

from core.calculos import filtrar_mes
from core.formato import MESES_CORTO


def margen(v):
    ing = v["ingreso"].sum()
    return 100 * (ing - v["costo_directo"].sum()) / ing if ing else None


def rendimiento(t):
    t = t[t["valido"]]
    lit = t["litros"].sum()
    return t["km"].sum() / lit if lit else None


def consumo_vs_esperado(t):
    """Litros reales / litros esperados × 100 (solo tramos válidos). >100 = consumió de más."""
    t = t[t["valido"]]
    esp = t["litros_esperados"].sum()
    return 100 * t["litros"].sum() / esp if esp else None


def costo_km(o, t):
    """Costo de materiales de OT de tractos / km de tramos válidos del mismo período."""
    km = t[t["valido"]]["km"].sum()
    costo = o[o["tipo_equipo"] == "Tracto"]["costo"].sum()
    return costo / km if km else None


def pct_preventivo(o):
    tot = o["costo"].sum()
    return 100 * o.loc[o["tipo_mantencion"] == "PREVENTIVA", "costo"].sum() / tot if tot else None


def dias_promedio(o, tipo):
    s = o[o["tipo_mantencion"] == tipo]
    return s["dias_taller"].sum() / len(s) if len(s) else None


def serie_12m(fn, anio, mes, *tablas_y_cols):
    """Aplica fn mes a mes en los 12 meses que terminan en (anio, mes).

    tablas_y_cols: pares (DataFrame, columna de fecha). fn recibe las tablas filtradas.
    """
    fin = pd.Period(year=anio, month=mes, freq="M")
    filas = []
    for p in pd.period_range(fin - 11, fin, freq="M"):
        partes = [filtrar_mes(df, p.year, p.month, col=col) for df, col in tablas_y_cols]
        filas.append({"mes": f"{MESES_CORTO[p.month - 1]}-{p.year}", "valor": fn(*partes)})
    return pd.DataFrame(filas)


def delta(actual, anterior):
    return actual - anterior if actual is not None and anterior is not None else None
