"""Formato chileno de números (miles con punto, decimales con coma), sin depender del locale."""

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
MESES_CORTO = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def fmt_num(x, dec=0):
    if x is None:
        return "—"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_clp(x):
    return "—" if x is None else f"${fmt_num(x, 0)}"


def fmt_pct(x, dec=1):
    return "—" if x is None else f"{fmt_num(x, dec)} %"


def fmt_fecha(d):
    return d.strftime("%d-%m-%Y")


def mes_anio(anio, mes):
    return f"{MESES[mes - 1]} {anio}"
