"""Cálculo de indicadores. Siempre Σ numerador / Σ denominador, nunca promedio de porcentajes."""
import calendar
from datetime import date

import pandas as pd


def mes_anterior(anio, mes):
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


def ultimo_dia_comparable(anio, mes):
    """Si el mes es el actual, se compara hasta el día de hoy; si no, el mes completo."""
    hoy = date.today()
    if (anio, mes) == (hoy.year, hoy.month):
        return hoy.day
    return calendar.monthrange(anio, mes)[1]


def filtrar_mes(df, anio, mes, hasta_dia=None, col="fecha"):
    f = pd.to_datetime(df[col])
    m = (f.dt.year == anio) & (f.dt.month == mes)
    if hasta_dia:
        m &= f.dt.day <= hasta_dia
    return df[m]


def venta_mes(ventas, anio, mes):
    """Venta del mes y del mismo período del mes anterior (días 1..N)."""
    dia = ultimo_dia_comparable(anio, mes)
    a_ant, m_ant = mes_anterior(anio, mes)
    dia_ant = min(dia, calendar.monthrange(a_ant, m_ant)[1])
    act = filtrar_mes(ventas, anio, mes, dia)
    ant = filtrar_mes(ventas, a_ant, m_ant, dia_ant)
    return act, ant, dia


def flota_mes(estado, anio, mes):
    """Disponibilidad y días trabajados de un mes (o de una selección de camiones)."""
    d = filtrar_mes(estado, anio, mes)
    return resumen_flota(d)


def resumen_flota(d):
    total = len(d)
    taller = int(d["en_taller"].sum())
    disponibles = total - taller
    con_viaje = int(((d["con_viaje"] == 1) & (d["en_taller"] == 0)).sum())
    return {
        "dias_totales": total,
        "dias_taller": taller,
        "dias_disponibles": disponibles,
        "dias_con_viaje": con_viaje,
        "disponibilidad": 100 * disponibles / total if total else None,
        "dias_trabajados": 100 * con_viaje / disponibles if disponibles else None,
    }


def produccion_conductores(cond, anio, mes):
    """Producción = ingreso del conductor / ingreso promedio de su grupo × 100."""
    d = cond[(cond.anio == anio) & (cond.mes == mes)].copy()
    if d.empty:
        return d
    d["produccion"] = 100 * d["ingreso"] / d.groupby("grupo")["ingreso"].transform("mean")
    d["rendimiento"] = d["km"] / d["litros"]
    return d
