# Tableros de gestión — Transportes Callegari (versión de diseño, Streamlit)

Datos ficticios. Sirve para revisar diseño y navegación antes de conectar el data warehouse.
Una sola aplicación con dos tableros: cada usuario ve **solo** el de su rol.

## Ejecutar

```
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

copy .streamlit\secrets_ejemplo.toml .streamlit\secrets.toml
python generar_clave.py           # pega el hash en secrets.toml (una vez por usuario)

gerencia12
operaciones

streamlit run app.py
```

En `secrets.toml` cada usuario tiene `rol = "gerencia"` u `rol = "operaciones"`.

## Tableros

| Rol | Páginas |
|---|---|
| gerencia | Inicio · Costos y margen · Combustible · Mantención |
| operaciones | Inicio · Flota en tiempo real · Ventas · Conductores · Control de flota |

## Estructura

```
app.py                         login y navegación según rol
.streamlit/config.toml         paleta del tema
.streamlit/secrets.toml        usuarios, rol y hash de contraseñas (NO se comparte)
core/auth.py                   login (PBKDF2 + bloqueo tras 5 intentos)
core/estilo.py                 paleta, semáforo, tarjetas KPI, leyendas, exportar a Excel/CSV
core/formato.py                números en formato chileno
core/calculos.py               indicadores de operaciones (Σ numerador / Σ denominador)
core/calculos_gerencia.py      indicadores de gerencia
core/datos.py                  ÚNICO punto de acceso a datos (hoy demo, después SQL)
core/datos_demo.py             datos ficticios de operaciones
core/datos_demo_gerencia.py    datos ficticios de gerencia y metas referenciales
vistas/gerencia/*.py           páginas de Gerencia
vistas/operaciones/*.py        páginas de Operaciones
```

## Pasar a datos reales

1. Completar las consultas `TODO` de `core/datos.py` contra el data warehouse (PostgreSQL).
2. Cambiar `FUENTE = "dw"`.
3. Reemplazar las metas (`METAS`, `METAS_GERENCIA`) por la lectura de la tabla de metas.

Las páginas no cambian, porque reciben las mismas columnas.
