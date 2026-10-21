"""Paleta, componentes visuales comunes y regla del semáforo.

Todas las páginas usan estos helpers para que el tablero se vea igual en
todas partes. Para cambiar un color se cambia aquí y en config.toml.
"""
import streamlit as st

from core.formato import fmt_num

# ---------------------------------------------------------------- paleta
ROJO = "#F21F2D"          # marca, «No cumple», en taller
NEGRO = "#201C19"         # texto, serie principal, en viaje
VERDE = "#1E9D51"         # «Cumple», disponible
GRIS_CLARO = "#EBECEA"    # fondos secundarios
BLANCO = "#FFFEFE"        # fondo principal
# derivados
ROJO_CLARO = "#F98F96"    # «Alerta»
GRIS_OSCURO = "#63605E"   # texto secundario, series secundarias
GRIS_MEDIO = "#A6A4A3"    # ejes, «Sin meta», sin señal
VERDE_CLARO = "#8ECEA8"

ESTADOS = {
    "cumple":    ("Cumple", VERDE),
    "alerta":    ("Alerta", ROJO_CLARO),
    "no_cumple": ("No cumple", ROJO),
    "sin_meta":  ("Sin meta definida", GRIS_MEDIO),
}
TOLERANCIA = 0.10   # «Alerta» si está a menos de 10 % de la meta


def estado(valor, meta, sentido="mayor_mejor"):
    """Devuelve la clave del estado del semáforo."""
    if meta is None or valor is None:
        return "sin_meta"
    if sentido == "mayor_mejor":
        if valor >= meta:
            return "cumple"
        return "alerta" if valor >= meta * (1 - TOLERANCIA) else "no_cumple"
    if valor <= meta:
        return "cumple"
    return "alerta" if valor <= meta * (1 + TOLERANCIA) else "no_cumple"


def badge(clave):
    texto, color = ESTADOS[clave]
    return f'<span style="color:{color};font-weight:600">● {texto}</span>'


def texto_estado(clave):
    """Para tablas: ícono y texto, sin HTML."""
    return f"● {ESTADOS[clave][0]}"


# ---------------------------------------------------------------- CSS
def aplicar_estilo():
    st.markdown(
        f"""
        <style>
          .block-container {{padding-top: 1.2rem; padding-bottom: 1rem;}}
          .logo-box {{width:88px;height:40px;border:1px dashed {GRIS_MEDIO};
                      display:flex;align-items:center;justify-content:center;
                      color:{GRIS_OSCURO};font-size:12px;border-radius:4px}}
          .kpi {{background:{BLANCO};border:1px solid {GRIS_CLARO};border-radius:8px;
                 padding:14px 16px;height:100%}}
          .kpi .nombre {{font-size:13px;color:{GRIS_OSCURO};font-weight:600}}
          .kpi .valor {{font-size:30px;font-weight:700;color:{NEGRO};line-height:1.2;margin:4px 0}}
          .kpi .linea {{font-size:12.5px;color:{GRIS_OSCURO};margin-top:2px}}
          .conteo {{background:{BLANCO};border:1px solid {GRIS_CLARO};border-radius:8px;
                    padding:12px 16px}}
          .conteo .n {{font-size:34px;font-weight:700;line-height:1.1}}
          .conteo .t {{font-size:13px;color:{GRIS_OSCURO}}}
          .leyenda {{font-size:12.5px;color:{GRIS_OSCURO};padding:6px 0}}
          .leyenda span {{margin-right:18px}}
          .pie {{font-size:11.5px;color:{GRIS_OSCURO};border-top:1px solid {GRIS_CLARO};
                 margin-top:18px;padding-top:8px}}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- componentes
def encabezado(titulo, subtitulo):
    aplicar_estilo()
    c1, c2 = st.columns([1, 11], vertical_alignment="center")
    with c1:
        st.markdown('<div class="logo-box">LOGO</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<h2 style='margin:0'>{titulo}</h2>"
            f"<div style='color:{GRIS_OSCURO};font-size:13px'>{subtitulo}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(f"<div style='height:3px;background:{ROJO};margin:8px 0 14px 0'></div>",
                unsafe_allow_html=True)


def _fmt(v, unidad, dec):
    if v is None:
        return "—"
    if unidad == "$":
        return f"${fmt_num(v, 0)}"
    return f"{fmt_num(v, dec)} {unidad}".strip()


def tarjeta_kpi(nombre, valor, unidad="", dec=1, meta=None, sentido="mayor_mejor",
                delta=None, unidad_delta=None, comparacion="vs mes anterior", nota=None):
    """Tarjeta con valor, meta, diferencia, estado y variación con su período explícito.

    El color de la flecha depende de si el cambio es favorable según el sentido
    del indicador, no de si el número sube o baja.
    """
    clave = estado(valor, meta, sentido)
    partes = [f'<div class="kpi"><div class="nombre">{nombre}</div>',
              f'<div class="valor">{_fmt(valor, unidad, dec)}</div>']
    if meta is not None and valor is not None:
        dif = valor - meta
        signo = "+" if dif >= 0 else "−"
        u = "pp" if unidad == "%" else unidad
        partes.append(f'<div class="linea">Meta: {_fmt(meta, unidad, dec)} · '
                      f'{signo}{_fmt(abs(dif), u if u != "$" else "$", dec)}</div>')
    partes.append(f'<div class="linea">{badge(clave)}</div>')
    if delta is not None:
        favorable = (delta >= 0) if sentido == "mayor_mejor" else (delta <= 0)
        color = VERDE if favorable else ROJO
        flecha = "▲" if delta >= 0 else "▼"
        ud = unidad_delta or ("pp" if unidad == "%" else unidad)
        partes.append(f'<div class="linea">{comparacion}: '
                      f'<span style="color:{color};font-weight:600">{flecha} '
                      f'{_fmt(abs(delta), ud if ud != "$" else "$", dec)}</span></div>')
    if nota:
        partes.append(f'<div class="linea">{nota}</div>')
    partes.append("</div>")
    st.markdown("".join(partes), unsafe_allow_html=True)


def conteo(titulo, n, color):
    st.markdown(
        f'<div class="conteo" style="border-left:6px solid {color}">'
        f'<div class="n">{n}</div><div class="t">{titulo}</div></div>',
        unsafe_allow_html=True,
    )


def leyenda_semaforo():
    st.markdown(
        '<div class="leyenda">' + "".join(f"<span>{badge(k)}</span>" for k in ESTADOS) +
        f"<span>Alerta = a menos de {int(TOLERANCIA * 100)} % de la meta</span></div>",
        unsafe_allow_html=True,
    )


def pie(texto):
    st.markdown(f'<div class="pie">{texto}</div>', unsafe_allow_html=True)


def estilo_grafico(fig, alto=360):
    """Formato común para todos los gráficos Plotly."""
    fig.update_layout(
        height=alto,
        template="plotly_white",
        paper_bgcolor=BLANCO,
        plot_bgcolor=BLANCO,
        font=dict(color=NEGRO, size=12),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        separators=",.",          # coma decimal, punto de miles
    )
    fig.update_xaxes(gridcolor=GRIS_CLARO, linecolor=GRIS_MEDIO)
    fig.update_yaxes(gridcolor=GRIS_CLARO, linecolor=GRIS_MEDIO)
    return fig


CONFIG_GRAFICO = {"displayModeBar": False}


def filtro_periodo(clave, anios=(2024, 2025, 2026), anio_def=None, mes_def=None):
    """Filtros de año y mes (el de año es obligatorio en todas las páginas)."""
    from datetime import date
    from core.formato import MESES

    hoy = date.today()
    anio_def = anio_def or hoy.year
    mes_def = mes_def or hoy.month
    c1, c2, _ = st.columns([1, 1, 4])
    anio = c1.selectbox("Año", anios, index=list(anios).index(anio_def), key=f"{clave}_anio")
    mes = c2.selectbox("Mes", range(1, 13), index=mes_def - 1,
                       format_func=lambda m: MESES[m - 1], key=f"{clave}_mes")
    return anio, mes


# ---------------------------------------------------------------- exportar
def boton_exportar(tablas, nombre_archivo, clave):
    """Botones de descarga en Excel y CSV con los números SIN formato.

    tablas: dict {"Nombre de hoja": DataFrame}. El CSV lleva solo la primera tabla.
    """
    import io

    import pandas as pd

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        for hoja, df in tablas.items():
            df.to_excel(xl, sheet_name=hoja[:31], index=False)
    primera = next(iter(tablas.values()))
    c1, c2, _ = st.columns([1, 1, 4])
    c1.download_button("Descargar Excel", buf.getvalue(), f"{nombre_archivo}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       icon=":material/download:", key=f"{clave}_xlsx", use_container_width=True)
    c2.download_button("Descargar CSV", primera.to_csv(index=False).encode("utf-8-sig"),
                       f"{nombre_archivo}.csv", "text/csv", icon=":material/download:",
                       key=f"{clave}_csv", use_container_width=True)


def grafico_tendencia(serie, titulo, meta, etiqueta_meta, sufijo="", dec=1):
    """Línea de 12 meses con meta discontinua (leyenda: Valor real / Meta)."""
    import plotly.graph_objects as go

    f = go.Figure()
    f.add_scatter(x=serie["mes"], y=serie["valor"], name="Valor real", mode="lines+markers",
                  line=dict(color=NEGRO, width=3))
    if meta is not None:
        f.add_scatter(x=serie["mes"], y=[meta] * len(serie), name=etiqueta_meta, mode="lines",
                      line=dict(color=GRIS_OSCURO, width=1.5, dash="dash"))
    ult = serie.dropna().tail(1)
    if not ult.empty:
        f.add_annotation(x=ult["mes"].iloc[0], y=ult["valor"].iloc[0],
                         text=f"{fmt_num(ult['valor'].iloc[0], dec)}{sufijo}", showarrow=False,
                         yshift=14, font=dict(color=NEGRO, size=12))
    f.update_layout(title=titulo)
    return estilo_grafico(f, 320)
