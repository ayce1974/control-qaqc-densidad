
# =========================================================
# Q-INTEGRITY – DENSIDADES (PANTALLA 1 + PANTALLA 2) ✅ FINAL PRO
# ENTREGABLE ÚNICO (PEGAR COMPLETO EN app.py)
#
# CORRECCIONES CLAVE (SIN FALLAS):
# 1) Arranque limpio: formulario parte en blanco (sin “fantasmas”) y se limpia al guardar.
# 2) Eliminación REAL: borra por ID_Registro (visible) pero internamente por RowKey (seguro).
#    - Funciona igual en Pantalla 1 y Pantalla 2.
# 3) Pantalla 2 limpia por defecto (sin datos “pegados”): exige botón "Aplicar filtros" para mostrar.
# 4) Tabla con COLOR (bandas + estado A/O/R) usando pandas Styler (cuando Streamlit lo soporta).
# 5) Umbral O auto-ajustado para no quedar “sueltísimo” bajo A (banda A-2.0 por defecto).
# 6) Export Excel por pantalla: Datos + KPIs (listo para Power BI).
# 7) Listas administrables en qintegrity_config.xlsx (Sectores / Métodos / Tramos).
# 8) Menú lateral PRO: botones grandes (Pantalla 1 / Pantalla 2) + estado activo.
# =========================================================

import os
import io
import uuid
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Q-INTEGRITY | Densidades", layout="wide")

DATA_FILE = "qintegrity_densidades.xlsx"
CONFIG_FILE = "qintegrity_config.xlsx"
TEMPLATE_FILE = "QI-DEN-PLT_FINAL_CORREGIDO_v12.xlsx"  # opcional (si existe)

FIG_W = 3.2
FIG_H = 2.2
TITLE_FS = 10
TICK_FS = 8
LABEL_FS = 9

DEFAULT_TOL_HUM_OPT = 2.0   # ±2.0%
DEFAULT_OBS_BAND = 2.0      # banda Observado = A - 2.0 (si O muy bajo se ajusta)
DEFAULT_KEEP_VALUES = False # arranque profesional: NO mantener

# ---------------------------------------------------------
# ESTILO UI (inputs + tablas más contrastadas + menú pro)
# ---------------------------------------------------------
st.markdown(
    """
<style>
.stApp { background:#f4f6fb; }

/* Header */
.qi-topbar{ background: #0f2f4f; padding: 10px 14px; border-radius: 14px; margin-bottom: 12px; }
.qi-title{ color:#ffffff; font-size:22px; font-weight:900; margin:0; line-height:1.1; }
.qi-subtitle{ color:#cfe0ee; font-size:13px; margin:0; }

/* Cards */
.qi-card{ background:#ffffff; border:1px solid #c7d3e4; border-radius:14px; padding:12px 12px; box-shadow: 0 1px 0 rgba(0,0,0,0.02); }
.hr { height:1px; background:#d6deea; margin: 12px 0; }

.qi-section{
  background:#ffffff;
  border:1px solid #c7d3e4;
  border-radius:14px;
  padding:12px 12px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
  margin-bottom: 10px;
}
.qi-h3{ font-size:16px; font-weight:900; margin:0 0 8px 0; color:#0f172a; }

/* Inputs */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="datepicker"] > div{
  background:#eaf1fb !important;
  border:1px solid #7fa0d2 !important;
  border-radius:12px !important;
}
label { font-weight: 900 !important; color:#0f172a !important; }

/* DataFrame */
div[data-testid="stDataFrame"] div[role="grid"]{
  border: 2px solid #aabbd6 !important;
  border-radius: 12px !important;
}
div[data-testid="stDataFrame"] div[role="grid"] *{ border-color: #c7d3e4 !important; }
div[data-testid="stDataFrame"] div[role="columnheader"]{
  background: #dfe8f7 !important;
  font-weight: 900 !important;
  color:#0f172a !important;
}
div[data-testid="stDataFrame"] div[role="gridcell"]{ background: #ffffff !important; }

/* Chips */
.qi-chip{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:900; font-size:12px; margin-right:8px; }
.qi-green{ background:#e7f6ea; color:#1b5e20; border:1px solid #bfe8c6; }
.qi-amber{ background:#fff4db; color:#7a4f00; border:1px solid #ffd68a; }
.qi-red{ background:#fde7ea; color:#8a1c1c; border:1px solid #f6b9c1; }
.qi-muted{ color:#475569; }

/* Buttons */
button[kind="primary"] { border-radius: 12px !important; font-weight: 900 !important; }
button { border-radius: 12px !important; font-weight: 800 !important; }

/* Sidebar menu cards */
.qi-navcard{
  width:100%;
  padding:12px 12px;
  border-radius:14px;
  border:2px solid #c7d3e4;
  background:#ffffff;
  margin-bottom:10px;
}
.qi-navcard-title{ font-weight:900; color:#0f172a; font-size:14px; }
.qi-navcard-sub{ font-weight:800; color:#475569; font-size:12px; margin-top:2px; }
.qi-navcard-active{
  border-color:#0f2f4f !important;
  background:#0f2f4f !important;
}
.qi-navcard-active .qi-navcard-title,
.qi-navcard-active .qi-navcard-sub{
  color:#ffffff !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# Header
colA, colB = st.columns([1, 12])
with colA:
    st.markdown("## 🛡️")
with colB:
    st.markdown(
        """
    <div class="qi-topbar">
        <p class="qi-title">Q-INTEGRITY</p>
        <p class="qi-subtitle">Módulo Densidades · Pantalla 1 (Ingreso/Eliminar) + Pantalla 2 (KPIs/Dashboard/Export)</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# COLUMNAS BD
# ---------------------------------------------------------
COLUMNS = [
    "RowKey",  # interno (NO mostrar)

    "ID_Registro",
    "Codigo_Proyecto",
    "Proyecto",
    "N_Registro",
    "N_Control",
    "N_Acta",
    "Fecha_control",

    "Sector_Zona",
    "Tramo",
    "Frente_Tramo",
    "Capa_N",
    "Espesor_capa_cm",
    "Dm_inicio",
    "Dm_termino",
    "Dm_Control",
    "Coordenada_Norte",
    "Coordenada_Este",
    "Cota",

    "Operador",
    "Metodo",
    "Profundidad_cm",

    "Densidad_Humeda_gcm3",
    "Humedad_medida_pct",
    "Humedad_Optima_pct",
    "Delta_Humedad_pct",
    "Ventana_Humedad",
    "Densidad_Seca_gcm3",
    "DMCS_Proctor_gcm3",
    "pct_Compactacion",

    "Umbral_Cumple_pct",
    "Umbral_Observado_pct",

    "Estado_QAQC",
    "Observacion",
    "Timestamp",
]

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _safe_uuid() -> str:
    return str(uuid.uuid4())

def ensure_data_file(path: str) -> None:
    if not os.path.exists(path):
        pd.DataFrame(columns=COLUMNS).to_excel(path, index=False)

def ensure_config_file(path: str) -> None:
    if not os.path.exists(path):
        df = pd.DataFrame({
            "Sectores": ["Sector 1", "Sector 2", "Bermas", "Subrasante", "Sub-base", "Base", "Carpeta"],
            "Metodos": ["Cono de Arena", "Densímetro Nuclear", "Corte y Pesada", "Balón de caucho"],
            "Tramos":  ["Tramo 1", "Tramo 2", "Km 0+000 a 0+500", "Km 0+500 a 1+000"],
        })
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Listas")

def load_config_lists(path: str) -> Dict[str, List[str]]:
    ensure_config_file(path)
    try:
        df = pd.read_excel(path, sheet_name="Listas")
        sectores = df.get("Sectores", pd.Series([], dtype=str)).dropna().astype(str).tolist()
        metodos  = df.get("Metodos",  pd.Series([], dtype=str)).dropna().astype(str).tolist()
        tramos   = df.get("Tramos",   pd.Series([], dtype=str)).dropna().astype(str).tolist()
        def clean(xs): return [x.strip() for x in xs if str(x).strip()]
        return {"sectores": clean(sectores), "metodos": clean(metodos), "tramos": clean(tramos)}
    except Exception:
        return {"sectores": ["Sector 1", "Sector 2"], "metodos": ["Cono de Arena", "Densímetro Nuclear"], "tramos": ["Tramo 1", "Tramo 2"]}

def save_config_lists(path: str, sectores: List[str], metodos: List[str], tramos: List[str]) -> None:
    def clean(xs): return [x.strip() for x in xs if str(x).strip()]
    df = pd.DataFrame({
        "Sectores": pd.Series(clean(sectores)),
        "Metodos":  pd.Series(clean(metodos)),
        "Tramos":   pd.Series(clean(tramos)),
    })
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Listas")

def load_lists_from_template(template_path: str) -> Dict:
    defaults = {"sectores": [], "metodos": [], "umbral_cumple": 92.0, "umbral_obs": 90.0}
    if (not template_path) or (not os.path.exists(template_path)):
        return defaults
    try:
        df_l = pd.read_excel(template_path, sheet_name="Listas")
        def pull_any(possible_cols: List[str]) -> List[str]:
            for c in possible_cols:
                if c in df_l.columns:
                    vals = df_l[c].dropna().astype(str).tolist()
                    vals = [v.strip() for v in vals if v.strip()]
                    if vals:
                        return vals
            return []
        sectores = pull_any(["Sector", "Sectores", "Sector_Zona", "Columna2"])
        metodos  = pull_any(["Metodo", "Método", "Metodos", "Métodos", "Columna5"])

        umbral_cumple = defaults["umbral_cumple"]
        umbral_obs = defaults["umbral_obs"]
        if "Columna7" in df_l.columns and "Columna8" in df_l.columns:
            params = pd.DataFrame({"k": df_l["Columna7"], "v": df_l["Columna8"]}).dropna()
            params["k"] = params["k"].astype(str).str.strip()
            for _, r in params.iterrows():
                try:
                    k = str(r["k"])
                    v = float(r["v"])
                    if "Umbral_A" in k or "UMBRAL_A" in k:
                        umbral_cumple = v
                    if "Umbral_O" in k or "UMBRAL_O" in k:
                        umbral_obs = v
                except Exception:
                    pass
        return {"sectores": sectores, "metodos": metodos, "umbral_cumple": float(umbral_cumple), "umbral_obs": float(umbral_obs)}
    except Exception:
        return defaults

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path) if os.path.exists(path) else pd.DataFrame(columns=COLUMNS)

    rename_map = {
        "Observación": "Observacion",
        "Método": "Metodo",
        "%_Compactación": "pct_Compactacion",
        "% Compactación": "pct_Compactacion",
        "Humedad_Óptima_pct": "Humedad_Optima_pct",
        "Humedad Óptima": "Humedad_Optima_pct",
        "Fecha": "Fecha_control",
        "_RowKey": "RowKey",  # por si viene de versiones viejas
    }
    df.rename(columns={c: rename_map.get(c, c) for c in df.columns}, inplace=True)

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = np.nan

    df = df[COLUMNS].copy()
    df["ID_Registro"] = pd.to_numeric(df["ID_Registro"], errors="coerce")
    df["Fecha_control"] = pd.to_datetime(df["Fecha_control"], errors="coerce")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    num_cols = [
        "Capa_N","Espesor_capa_cm","Dm_inicio","Dm_termino","Dm_Control",
        "Coordenada_Norte","Coordenada_Este","Cota","Profundidad_cm",
        "Densidad_Humeda_gcm3","Humedad_medida_pct","Humedad_Optima_pct","Delta_Humedad_pct",
        "Densidad_Seca_gcm3","DMCS_Proctor_gcm3","pct_Compactacion",
        "Umbral_Cumple_pct","Umbral_Observado_pct"
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # RowKey robusto
    df["RowKey"] = df["RowKey"].astype(str)
    needs_key = df["RowKey"].isna() | (df["RowKey"].str.strip() == "") | (df["RowKey"].str.lower() == "nan")
    if needs_key.any():
        df.loc[needs_key, "RowKey"] = [_safe_uuid() for _ in range(int(needs_key.sum()))]
        save_data(df, path)

    return df

def save_data(df: pd.DataFrame, path: str) -> None:
    out = df.copy()
    for c in COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[COLUMNS]
    out.to_excel(path, index=False)

def next_id(df: pd.DataFrame) -> int:
    if df.empty or df["ID_Registro"].dropna().empty:
        return 1
    return int(df["ID_Registro"].dropna().max()) + 1

def calc_densidad_seca(dh: float, w_pct: float) -> float:
    return float(dh) / (1.0 + float(w_pct) / 100.0)

def calc_pct_comp(ds: float, dmcs: float) -> float:
    return (float(ds) / float(dmcs)) * 100.0 if float(dmcs) else np.nan

def adjust_umbral_obs(umbral_a: float, umbral_o_raw: float, band: float = DEFAULT_OBS_BAND) -> float:
    o_min = max(0.0, float(umbral_a) - float(band))
    return max(float(umbral_o_raw), o_min)

def estado_qaqc(pct: float, umbral_a: float, umbral_o: float) -> str:
    if pd.isna(pct):
        return "—"
    if pct >= float(umbral_a):
        return "CUMPLE"
    if pct >= float(umbral_o):
        return "OBSERVADO"
    return "NO CUMPLE"

def kpi_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="qi-card">
            <div style="color:#64748b;font-size:0.90rem;font-weight:900">{label}</div>
            <div style="color:#0f172a;font-size:2.0rem;font-weight:900;margin-top:4px">{value}</div>
            <div style="color:#475569;font-size:0.95rem;margin-top:2px">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def export_excel_bytes(df_data: pd.DataFrame, df_kpi: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_data.to_excel(writer, index=False, sheet_name="Datos")
        df_kpi.to_excel(writer, index=False, sheet_name="KPIs")
    return out.getvalue()

def compute_kpis(df_in: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    d = df_in.copy()
    d["Estado_QAQC"] = d["Estado_QAQC"].astype(str).str.upper().str.strip()

    total = int(len(d))
    a = int((d["Estado_QAQC"] == "CUMPLE").sum())
    o = int((d["Estado_QAQC"] == "OBSERVADO").sum())
    r = int((d["Estado_QAQC"] == "NO CUMPLE").sum())

    prom = float(np.nanmean(d["pct_Compactacion"])) if d["pct_Compactacion"].notna().any() else np.nan
    mx = float(np.nanmax(d["pct_Compactacion"])) if d["pct_Compactacion"].notna().any() else np.nan
    mn = float(np.nanmin(d["pct_Compactacion"])) if d["pct_Compactacion"].notna().any() else np.nan

    pct_cumple = (a / total * 100.0) if total else 0.0

    df_kpi = pd.DataFrame({
        "Metrica": [
            "Total_muestras",
            "Cant_Aprobacion",
            "Cant_Observacion",
            "Cant_Rechazo",
            "Pct_Cumple",
            "Promedio_Compactacion",
            "Max_Compactacion",
            "Min_Compactacion",
        ],
        "Valor": [
            total,
            a,
            o,
            r,
            round(pct_cumple, 2),
            round(prom, 2) if not np.isnan(prom) else np.nan,
            round(mx, 2) if not np.isnan(mx) else np.nan,
            round(mn, 2) if not np.isnan(mn) else np.nan,
        ],
    })

    return df_kpi, {"total": total, "a": a, "o": o, "r": r, "pct_cumple": pct_cumple, "prom": prom, "mx": mx, "mn": mn}

def control_series_by_blocks_of_3(df_f: pd.DataFrame) -> pd.DataFrame:
    d = df_f.copy()
    d = d.dropna(subset=["Fecha_control"])
    d = d.sort_values(["Fecha_control", "Timestamp", "ID_Registro"], ascending=True)

    if d.empty:
        return pd.DataFrame(columns=["fecha", "block", "x_label", "pct_mean"])

    out_rows = []
    for fecha_val, g in d.groupby(d["Fecha_control"].dt.date):
        g2 = g.dropna(subset=["pct_Compactacion"]).copy()
        if g2.empty:
            continue
        g2 = g2.reset_index(drop=True)
        g2["idx"] = np.arange(len(g2))
        g2["block"] = (g2["idx"] // 3) + 1
        for b, gb in g2.groupby("block"):
            pct_mean = float(np.nanmean(gb["pct_Compactacion"].astype(float).values))
            x_label = f"{fecha_val} (B{int(b)})"
            out_rows.append({"fecha": fecha_val, "block": int(b), "x_label": x_label, "pct_mean": pct_mean})

    return pd.DataFrame(out_rows)

def parse_float(txt: str) -> Optional[float]:
    if txt is None:
        return None
    s = str(txt).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None

def parse_int(txt: str) -> Optional[int]:
    if txt is None:
        return None
    s = str(txt).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def style_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    def row_bg(row):
        stt = str(row.get("Estado_QAQC", "")).upper().strip()
        if stt == "CUMPLE":
            return ["background-color: #eef9f0"] * len(row)
        if stt == "OBSERVADO":
            return ["background-color: #fff7e6"] * len(row)
        if stt == "NO CUMPLE":
            return ["background-color: #fdeff1"] * len(row)
        return [""] * len(row)

    sty = (
        df.style
        .apply(row_bg, axis=1)
        .set_table_styles([
            {"selector": "th", "props": "background-color:#dfe8f7; color:#0f172a; font-weight:900;"},
            {"selector": "td", "props": "border:1px solid #d7e1f0;"},
            {"selector": "table", "props": "border-collapse:collapse; width:100%;"},
        ])
    )
    return sty

def reset_form():
    keys = [
        "p1_fecha_ctrl", "p1_cod_proy", "p1_proyecto", "p1_n_reg", "p1_n_ctrl", "p1_n_acta",
        "p1_sector_sel", "p1_sector_otro",
        "p1_tramo_sel", "p1_tramo_otro",
        "p1_frente",
        "p1_capa_txt", "p1_esp_txt",
        "p1_dm_ini_txt", "p1_dm_ter_txt", "p1_dm_ctrl_txt",
        "p1_coord_n_txt", "p1_coord_e_txt", "p1_cota_txt",
        "p1_operador", "p1_met_sel", "p1_met_otro",
        "p1_prof_txt", "p1_dh_txt", "p1_h_txt", "p1_hopt_txt", "p1_dmcs_txt",
        "p1_obs",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

def delete_by_ids(df_all: pd.DataFrame, ids_to_delete: List[int]) -> Tuple[pd.DataFrame, int]:
    """
    Elimina registros por ID_Registro (visible) mapeando a RowKey (interno).
    Devuelve (df_nuevo, cantidad_eliminada).
    """
    if not ids_to_delete:
        return df_all, 0
    ids_float = [float(x) for x in ids_to_delete]
    keys = df_all[df_all["ID_Registro"].astype(float).isin(ids_float)]["RowKey"].astype(str).tolist()
    if not keys:
        return df_all, 0
    df_new = df_all[~df_all["RowKey"].astype(str).isin(keys)].copy()
    return df_new, len(keys)

# ---------------------------------------------------------
# INIT
# ---------------------------------------------------------
ensure_data_file(DATA_FILE)
ensure_config_file(CONFIG_FILE)

tpl = load_lists_from_template(TEMPLATE_FILE)
cfg = load_config_lists(CONFIG_FILE)

sectores = list(dict.fromkeys([*cfg["sectores"], *tpl.get("sectores", [])]))
metodos  = list(dict.fromkeys([*cfg["metodos"],  *tpl.get("metodos",  [])]))
tramos   = cfg["tramos"][:] if cfg.get("tramos") else ["Tramo 1", "Tramo 2"]

if not sectores: sectores = ["Sector 1", "Sector 2"]
if not metodos:  metodos  = ["Cono de Arena", "Densímetro Nuclear"]
if not tramos:   tramos   = ["Tramo 1", "Tramo 2"]

# ---------------------------------------------------------
# SIDEBAR – PARAMETROS + LISTAS
# ---------------------------------------------------------
st.sidebar.markdown("### Parámetros QA/QC")

tol_hum_opt = st.sidebar.number_input(
    "Tolerancia Humedad Óptima (±%)", value=float(DEFAULT_TOL_HUM_OPT), step=0.5, format="%.1f"
)

if "UMBRAL_A" not in st.session_state:
    st.session_state["UMBRAL_A"] = float(tpl.get("umbral_cumple", 92.0) or 92.0)
if "UMBRAL_O_RAW" not in st.session_state:
    st.session_state["UMBRAL_O_RAW"] = float(tpl.get("umbral_obs", 90.0) or 90.0)

UMBRAL_A = st.sidebar.number_input(
    "Umbral A (CUMPLE ≥ %)", value=float(st.session_state["UMBRAL_A"]), step=0.5, format="%.1f"
)
UMBRAL_O_RAW = st.sidebar.number_input(
    "Umbral O (OBSERVADO ≥ %)", value=float(st.session_state["UMBRAL_O_RAW"]), step=0.5, format="%.1f"
)

UMBRAL_O = adjust_umbral_obs(float(UMBRAL_A), float(UMBRAL_O_RAW), band=float(DEFAULT_OBS_BAND))
st.session_state["UMBRAL_A"] = float(UMBRAL_A)
st.session_state["UMBRAL_O_RAW"] = float(UMBRAL_O_RAW)

st.sidebar.markdown(
    f"""
<div class="qi-card">
  <div style="font-weight:900;color:#0f172a;margin-bottom:6px">Leyenda A/O/R</div>
  <span class="qi-chip qi-green">A · CUMPLE</span>
  <span class="qi-chip qi-amber">O · OBSERVADO</span>
  <span class="qi-chip qi-red">R · NO CUMPLE</span>
  <div class="qi-muted" style="margin-top:8px;font-size:0.95rem">
    <b>O auto-ajustado</b> para quedar cerca de A: <br>
    A={float(UMBRAL_A):.1f}% · O(usado)={float(UMBRAL_O):.1f}% <br>
    (banda mínima: A-{DEFAULT_OBS_BAND:.1f}%)
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar.expander("⚙️ Administrar listas (Sectores / Métodos / Tramos)", expanded=False):
    st.caption("Se guarda en qintegrity_config.xlsx (sheet: Listas).")
    txt_sec = st.text_area("Sectores (1 por línea)", value="\n".join(sectores), height=140)
    txt_met = st.text_area("Métodos (1 por línea)", value="\n".join(metodos), height=120)
    txt_tra = st.text_area("Tramos (1 por línea)", value="\n".join(tramos), height=100)
    if st.button("💾 Guardar listas", use_container_width=True):
        new_sec = [x.strip() for x in txt_sec.splitlines() if x.strip()]
        new_met = [x.strip() for x in txt_met.splitlines() if x.strip()]
        new_tra = [x.strip() for x in txt_tra.splitlines() if x.strip()]
        save_config_lists(CONFIG_FILE, new_sec, new_met, new_tra)
        st.success("Listas guardadas.")
        st.rerun()

# ---------------------------------------------------------
# MENÚ LATERAL PRO (BOTONES GRANDES)
# ---------------------------------------------------------
st.sidebar.markdown("<div class='hr'></div>", unsafe_allow_html=True)
st.sidebar.markdown("### 🧭 Navegación")

if "PAGE" not in st.session_state:
    st.session_state["PAGE"] = "P1"

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("🧾 P1", use_container_width=True):
        st.session_state["PAGE"] = "P1"
        st.rerun()
with c2:
    if st.button("📊 P2", use_container_width=True):
        st.session_state["PAGE"] = "P2"
        st.rerun()

p1_active = "qi-navcard qi-navcard-active" if st.session_state["PAGE"] == "P1" else "qi-navcard"
p2_active = "qi-navcard qi-navcard-active" if st.session_state["PAGE"] == "P2" else "qi-navcard"

st.sidebar.markdown(
    f"""
<div class="{p1_active}">
  <div class="qi-navcard-title">🧾 Pantalla 1 · Ingreso / Eliminar</div>
  <div class="qi-navcard-sub">Formulario · Cálculos · Tabla · Borrado · Export base</div>
</div>
<div class="{p2_active}">
  <div class="qi-navcard-title">📊 Pantalla 2 · Dashboard KPIs</div>
  <div class="qi-navcard-sub">Filtros · KPIs · Gráficos · Control · Export filtrado</div>
</div>
""",
    unsafe_allow_html=True,
)

page = "Pantalla 1 – Ingreso / Eliminar" if st.session_state["PAGE"] == "P1" else "Pantalla 2 – Dashboard KPIs"

# ---------------------------------------------------------
# FORM DEFAULTS (VACÍO REAL)
# ---------------------------------------------------------
if "p1_keep" not in st.session_state:
    st.session_state["p1_keep"] = bool(DEFAULT_KEEP_VALUES)

# ---------------------------------------------------------
# PANTALLA 1
# ---------------------------------------------------------
if page == "Pantalla 1 – Ingreso / Eliminar":
    st.caption("Pantalla 1 · Ingreso + Cálculos + Tabla (Ver) + Eliminación por ID + Export (Base + KPIs)")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    keep_values = st.checkbox(
        "Mantener valores después de guardar (si lo desmarcas, queda todo en blanco)",
        value=bool(st.session_state.get("p1_keep", False)),
    )
    st.session_state["p1_keep"] = keep_values

    with st.form("form_ingreso", clear_on_submit=False):
        st.markdown("<div class='qi-section'><div class='qi-h3'>Identificación y Control</div>", unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            fecha_ctrl = st.date_input("Fecha control", value=st.session_state.get("p1_fecha_ctrl", date.today()))
            codigo_proy = st.text_input("Código de Proyecto", value=st.session_state.get("p1_cod_proy", "")).strip()
        with a2:
            proyecto = st.text_input("Proyecto (DIGITAR)", value=st.session_state.get("p1_proyecto", "")).strip()
            n_registro = st.text_input("N° Registro", value=st.session_state.get("p1_n_reg", "")).strip()
        with a3:
            n_control = st.text_input("N° Control", value=st.session_state.get("p1_n_ctrl", "")).strip()
            n_acta = st.text_input("N° Acta", value=st.session_state.get("p1_n_acta", "")).strip()
        with a4:
            sec_opts = ["— Seleccionar —", *sectores, "Otro (digitar)"]
            sec_sel = st.selectbox("Sector/Zona", sec_opts, index=0, key="p1_sector_sel")
            sec_otro = ""
            if sec_sel == "Otro (digitar)":
                sec_otro = st.text_input("Sector/Zona (otro)", value=st.session_state.get("p1_sector_otro", ""))
            tramo_opts = ["— Seleccionar —", *tramos, "Otro (digitar)"]
            tramo_sel = st.selectbox("Tramo", tramo_opts, index=0, key="p1_tramo_sel")
            tramo_otro = ""
            if tramo_sel == "Otro (digitar)":
                tramo_otro = st.text_input("Tramo (otro)", value=st.session_state.get("p1_tramo_otro", ""))

        sector_final = (sec_otro.strip() if sec_sel == "Otro (digitar)" else ("" if sec_sel == "— Seleccionar —" else sec_sel)).strip()
        tramo_final  = (tramo_otro.strip() if tramo_sel == "Otro (digitar)" else ("" if tramo_sel == "— Seleccionar —" else tramo_sel)).strip()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='qi-section'><div class='qi-h3'>Ubicación / Geometría</div>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            capa_txt = st.text_input("N° Capa", value=st.session_state.get("p1_capa_txt", ""), placeholder="Ej: 1")
            esp_txt  = st.text_input("Espesor capa (cm)", value=st.session_state.get("p1_esp_txt", ""), placeholder="Ej: 30.0")
        with b2:
            dm_ini_txt = st.text_input("Dm inicio", value=st.session_state.get("p1_dm_ini_txt", ""), placeholder="Ej: 0")
            dm_ter_txt = st.text_input("Dm término", value=st.session_state.get("p1_dm_ter_txt", ""), placeholder="Ej: 100")
        with b3:
            dm_ctrl_txt = st.text_input("Dm Control", value=st.session_state.get("p1_dm_ctrl_txt", ""), placeholder="Ej: 50")
            cota_txt    = st.text_input("Cota", value=st.session_state.get("p1_cota_txt", ""), placeholder="Ej: 123.456")
        with b4:
            coord_n_txt = st.text_input("Coordenada Norte", value=st.session_state.get("p1_coord_n_txt", ""), placeholder="Ej: 6220000.000")
            coord_e_txt = st.text_input("Coordenada Este",  value=st.session_state.get("p1_coord_e_txt", ""), placeholder="Ej: 350000.000")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='qi-section'><div class='qi-h3'>Operación / Ensayo</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            operador = st.text_input("Operador (DIGITAR)", value=st.session_state.get("p1_operador", "")).strip()
            prof_txt = st.text_input("Profundidad (cm)", value=st.session_state.get("p1_prof_txt", ""), placeholder="Ej: 20")
        with c2:
            met_opts = ["— Seleccionar —", *metodos, "Otro (digitar)"]
            met_sel = st.selectbox("Método", met_opts, index=0, key="p1_met_sel")
            met_otro = ""
            if met_sel == "Otro (digitar)":
                met_otro = st.text_input("Método (otro)", value=st.session_state.get("p1_met_otro", ""))
            frente = st.text_input("Frente / Detalle", value=st.session_state.get("p1_frente", "")).strip()
        metodo_final = (met_otro.strip() if met_sel == "Otro (digitar)" else ("" if met_sel == "— Seleccionar —" else met_sel)).strip()

        with c3:
            dh_txt = st.text_input("Densidad Húmeda (g/cm³)", value=st.session_state.get("p1_dh_txt", ""), placeholder="Ej: 2.200")
            h_txt  = st.text_input("Humedad medida (%)", value=st.session_state.get("p1_h_txt", ""), placeholder="Ej: 5.5")
        with c4:
            hopt_txt = st.text_input("Humedad óptima Proctor (%)", value=st.session_state.get("p1_hopt_txt", ""), placeholder="Ej: 6.0")
            dmcs_txt = st.text_input("DMCS Proctor (g/cm³)", value=st.session_state.get("p1_dmcs_txt", ""), placeholder="Ej: 2.200")

        observacion = st.text_area("Observación", value=st.session_state.get("p1_obs", ""))

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Guardar registro", type="primary")

        if submitted:
            capa = parse_int(capa_txt)
            espesor_cm = parse_float(esp_txt)
            dm_ini = parse_float(dm_ini_txt)
            dm_ter = parse_float(dm_ter_txt)
            dm_control = parse_float(dm_ctrl_txt)
            cota = parse_float(cota_txt)
            coord_n = parse_float(coord_n_txt)
            coord_e = parse_float(coord_e_txt)
            prof_cm = parse_float(prof_txt)

            dens_h = parse_float(dh_txt)
            hum_pct = parse_float(h_txt)
            hum_opt = parse_float(hopt_txt)
            dmcs = parse_float(dmcs_txt)

            if not codigo_proy:
                st.error("⚠️ Falta Código de Proyecto.")
            elif not proyecto:
                st.error("⚠️ Falta Proyecto.")
            elif not operador:
                st.error("⚠️ Falta Operador.")
            elif not sector_final:
                st.error("⚠️ Falta Sector/Zona.")
            elif not metodo_final:
                st.error("⚠️ Falta Método.")
            elif dens_h is None or dens_h <= 0:
                st.error("⚠️ Densidad Húmeda inválida.")
            elif dmcs is None or dmcs <= 0:
                st.error("⚠️ DMCS Proctor inválido.")
            elif hum_pct is None or hum_pct < 0:
                st.error("⚠️ Humedad medida inválida.")
            elif hum_opt is None or hum_opt < 0:
                st.error("⚠️ Humedad óptima inválida.")
            else:
                dens_s = calc_densidad_seca(float(dens_h), float(hum_pct))
                pct_comp = calc_pct_comp(float(dens_s), float(dmcs))

                delta_h = float(hum_pct) - float(hum_opt)
                ventana = "OK" if abs(delta_h) <= float(tol_hum_opt) else "OBSERVADO"  # SOLO informativo

                estado = estado_qaqc(float(pct_comp), float(UMBRAL_A), float(UMBRAL_O))

                df_now = load_data(DATA_FILE)
                nuevo = {
                    "RowKey": _safe_uuid(),
                    "ID_Registro": next_id(df_now),

                    "Codigo_Proyecto": codigo_proy,
                    "Proyecto": proyecto,
                    "N_Registro": n_registro,
                    "N_Control": n_control,
                    "N_Acta": n_acta,
                    "Fecha_control": pd.to_datetime(fecha_ctrl),

                    "Sector_Zona": sector_final,
                    "Tramo": tramo_final,
                    "Frente_Tramo": frente,
                    "Capa_N": float(capa) if capa is not None else np.nan,
                    "Espesor_capa_cm": float(espesor_cm) if espesor_cm is not None else np.nan,
                    "Dm_inicio": float(dm_ini) if dm_ini is not None else np.nan,
                    "Dm_termino": float(dm_ter) if dm_ter is not None else np.nan,
                    "Dm_Control": float(dm_control) if dm_control is not None else np.nan,
                    "Coordenada_Norte": float(coord_n) if coord_n is not None else np.nan,
                    "Coordenada_Este": float(coord_e) if coord_e is not None else np.nan,
                    "Cota": float(cota) if cota is not None else np.nan,

                    "Operador": operador,
                    "Metodo": metodo_final,
                    "Profundidad_cm": float(prof_cm) if prof_cm is not None else np.nan,

                    "Densidad_Humeda_gcm3": float(dens_h),
                    "Humedad_medida_pct": float(hum_pct),
                    "Humedad_Optima_pct": float(hum_opt),
                    "Delta_Humedad_pct": float(delta_h),
                    "Ventana_Humedad": str(ventana),
                    "Densidad_Seca_gcm3": float(dens_s),
                    "DMCS_Proctor_gcm3": float(dmcs),
                    "pct_Compactacion": float(pct_comp),

                    "Umbral_Cumple_pct": float(UMBRAL_A),
                    "Umbral_Observado_pct": float(UMBRAL_O),

                    "Estado_QAQC": estado,
                    "Observacion": str(observacion).strip(),
                    "Timestamp": pd.to_datetime(datetime.now()),
                }

                df2 = pd.concat([df_now, pd.DataFrame([nuevo])], ignore_index=True)
                save_data(df2, DATA_FILE)

                if keep_values:
                    st.session_state["p1_fecha_ctrl"] = fecha_ctrl
                    st.session_state["p1_cod_proy"] = codigo_proy
                    st.session_state["p1_proyecto"] = proyecto
                    st.session_state["p1_n_reg"] = n_registro
                    st.session_state["p1_n_ctrl"] = n_control
                    st.session_state["p1_n_acta"] = n_acta
                    st.session_state["p1_sector_otro"] = sec_otro
                    st.session_state["p1_tramo_otro"] = tramo_otro
                    st.session_state["p1_frente"] = frente
                    st.session_state["p1_capa_txt"] = capa_txt
                    st.session_state["p1_esp_txt"] = esp_txt
                    st.session_state["p1_dm_ini_txt"] = dm_ini_txt
                    st.session_state["p1_dm_ter_txt"] = dm_ter_txt
                    st.session_state["p1_dm_ctrl_txt"] = dm_ctrl_txt
                    st.session_state["p1_coord_n_txt"] = coord_n_txt
                    st.session_state["p1_coord_e_txt"] = coord_e_txt
                    st.session_state["p1_cota_txt"] = cota_txt
                    st.session_state["p1_operador"] = operador
                    st.session_state["p1_met_otro"] = met_otro
                    st.session_state["p1_prof_txt"] = prof_txt
                    st.session_state["p1_dh_txt"] = dh_txt
                    st.session_state["p1_h_txt"] = h_txt
                    st.session_state["p1_hopt_txt"] = hopt_txt
                    st.session_state["p1_dmcs_txt"] = dmcs_txt
                    st.session_state["p1_obs"] = observacion
                else:
                    reset_form()

                st.success("Registro guardado correctamente ✅")
                st.rerun()

    # KPIs rápidos (solo si hay valores digitados)
    dens_h_v = parse_float(st.session_state.get("p1_dh_txt", ""))
    hum_v = parse_float(st.session_state.get("p1_h_txt", ""))
    hopt_v = parse_float(st.session_state.get("p1_hopt_txt", ""))
    dmcs_v = parse_float(st.session_state.get("p1_dmcs_txt", ""))

    try:
        if dens_h_v is not None and hum_v is not None and dmcs_v is not None and dmcs_v > 0 and dens_h_v > 0:
            dens_s_v = calc_densidad_seca(float(dens_h_v), float(hum_v))
            pct_v = calc_pct_comp(float(dens_s_v), float(dmcs_v))
        else:
            dens_s_v, pct_v = np.nan, np.nan

        if hum_v is not None and hopt_v is not None:
            delta_v = float(hum_v) - float(hopt_v)
            ventana_v = "OK" if abs(delta_v) <= float(tol_hum_opt) else "OBSERVADO"
        else:
            delta_v, ventana_v = np.nan, "—"

        estado_v = estado_qaqc(float(pct_v), float(UMBRAL_A), float(UMBRAL_O)) if pd.notna(pct_v) else "—"
    except Exception:
        dens_s_v, pct_v, delta_v, ventana_v, estado_v = np.nan, np.nan, np.nan, "—", "—"

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1: kpi_card("Densidad Seca (g/cm³)", f"{dens_s_v:.3f}" if pd.notna(dens_s_v) else "—")
    with r2: kpi_card("% Compactación", f"{pct_v:.1f}%" if pd.notna(pct_v) else "—", f"A={UMBRAL_A:.1f}% · O={UMBRAL_O:.1f}%")
    with r3: kpi_card("Δ Humedad (Terreno-Proctor)", f"{delta_v:+.2f}%" if pd.notna(delta_v) else "—", f"Ventana ±{tol_hum_opt:.1f}% → {ventana_v}")
    with r4:
        color = "#1b5e20" if estado_v == "CUMPLE" else ("#7a4f00" if estado_v == "OBSERVADO" else "#8a1c1c")
        st.markdown(
            f"""
            <div class="qi-card">
                <div style="color:#64748b;font-size:0.90rem;font-weight:900">Estado QA/QC</div>
                <div style="color:{color};font-size:1.8rem;font-weight:900;margin-top:6px">{estado_v}</div>
                <div class="qi-muted" style="margin-top:6px">
                    <span class="qi-chip qi-green">A · CUMPLE</span>
                    <span class="qi-chip qi-amber">O · OBSERVADO</span>
                    <span class="qi-chip qi-red">R · NO CUMPLE</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # Export base completa + KPIs
    df_all = load_data(DATA_FILE)
    df_kpi_all, _ = compute_kpis(df_all)
    xbytes_all = export_excel_bytes(df_all.drop(columns=["RowKey"]), df_kpi_all)

    e1, e2 = st.columns([1.4, 2.6])
    with e1:
        st.download_button(
            "⬇️ Exportar Excel (Base completa + KPIs)",
            data=xbytes_all,
            file_name=f"QINTEGRITY_Densidades_Base_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with e2:
        st.info("Exporta: **Datos (base completa)** + **KPIs** (listo Power BI).")

    # Tabla vista (SIN RowKey)
    st.subheader("Registros (Base de datos) — Ver / Eliminar")

    if df_all.empty:
        st.info("Aún no hay registros.")
    else:
        df_show = df_all.sort_values(["Timestamp", "ID_Registro"], ascending=False).copy()

        max_rows = int(len(df_show))
        filas_visibles = max_rows if max_rows <= 1 else st.slider("Filas visibles", 1, max_rows, min(80, max_rows))

        df_view = df_show.head(int(filas_visibles)).copy()
        df_view_user = df_view.drop(columns=["RowKey"]).copy()

        try:
            st.dataframe(style_table(df_view_user), use_container_width=True, height=340)
        except Exception:
            st.dataframe(df_view_user, use_container_width=True, height=340)

        ids = df_view["ID_Registro"].dropna().astype(int).tolist()
        ids = sorted(list(dict.fromkeys(ids)))

        if "p1_del_ids" not in st.session_state:
            st.session_state["p1_del_ids"] = []

        st.session_state["p1_del_ids"] = [x for x in st.session_state["p1_del_ids"] if x in ids]

        sel_ids = st.multiselect("Selecciona ID_Registro a eliminar", options=ids, default=st.session_state["p1_del_ids"])
        st.session_state["p1_del_ids"] = sel_ids

        b1, b2 = st.columns([1.4, 2.6])
        with b1:
            if st.button("🗑️ ELIMINAR seleccionados (BORRA EL REGISTRO COMPLETO)", type="primary", use_container_width=True):
                if not sel_ids:
                    st.warning("No seleccionaste ningún ID_Registro.")
                else:
                    df_new, n_del = delete_by_ids(df_all, sel_ids)
                    save_data(df_new, DATA_FILE)
                    st.session_state["p1_del_ids"] = []
                    st.success(f"Eliminados {n_del} registro(s).")
                    st.rerun()
        with b2:
            st.caption("Borrado seguro interno por RowKey, pero el usuario elimina por **ID_Registro** (visible).")

# ---------------------------------------------------------
# PANTALLA 2 (DASHBOARD) - LIMPIA POR DEFECTO
# ---------------------------------------------------------
else:
    st.caption("Pantalla 2 · Dashboard KPIs + Gráficos + Control chart + Tabla (Eliminar/Export)")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    df_all = load_data(DATA_FILE)
    if df_all.empty:
        st.info("Aún no hay registros. Ingresa datos en Pantalla 1.")
        st.stop()

    st.subheader("Filtros")
    f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 3, 2])

    with f1:
        cods = sorted([c for c in df_all["Codigo_Proyecto"].dropna().astype(str).unique().tolist() if c.strip()])
        sel_cod = st.multiselect("Código Proyecto", options=cods, default=[])

    with f2:
        prys = sorted([p for p in df_all["Proyecto"].dropna().astype(str).unique().tolist() if p.strip()])
        sel_proy = st.multiselect("Proyecto", options=prys, default=[])

    with f3:
        ops = sorted([o for o in df_all["Operador"].dropna().astype(str).unique().tolist() if o.strip()])
        op_opts = ["— (Todos)"] + ops
        sel_op = st.selectbox("Operador (solo 1)", options=op_opts, index=0)

    with f4:
        dmin = df_all["Fecha_control"].min()
        dmax = df_all["Fecha_control"].max()
        dmin = dmin.date() if pd.notna(dmin) else date.today()
        dmax = dmax.date() if pd.notna(dmax) else date.today()
        rango = st.date_input("Rango fecha", value=(dmin, dmax))

    with f5:
        applied = st.button("✅ Aplicar filtros", type="primary", use_container_width=True)

    if "P2_APPLIED" not in st.session_state:
        st.session_state["P2_APPLIED"] = False

    if applied:
        st.session_state["P2_APPLIED"] = True

    if not st.session_state["P2_APPLIED"]:
        st.info("Pantalla 2 está **limpia** por defecto. Presiona **Aplicar filtros** para cargar KPIs/Gráficos/Tabla.")
        st.stop()

    # Aplicar filtros (con limpieza real)
    df_f = df_all.copy()
    df_f["Fecha_control"] = pd.to_datetime(df_f["Fecha_control"], errors="coerce")

    if isinstance(rango, tuple) and len(rango) == 2:
        d1, d2 = rango
        df_f = df_f[(df_f["Fecha_control"].dt.date >= d1) & (df_f["Fecha_control"].dt.date <= d2)]

    if sel_cod:
        df_f = df_f[df_f["Codigo_Proyecto"].astype(str).isin([str(x) for x in sel_cod])]
    if sel_proy:
        df_f = df_f[df_f["Proyecto"].astype(str).isin([str(x) for x in sel_proy])]
    if sel_op and sel_op != "— (Todos)":
        df_f = df_f[df_f["Operador"].astype(str).str.strip() == str(sel_op).strip()]

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # KPIs
    st.subheader("KPIs (Dashboard)")
    df_kpi, k = compute_kpis(df_f)

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Total muestras", str(k["total"]))
    with k2: kpi_card("Aprobación (A)", str(k["a"]))
    with k3: kpi_card("Observación (O)", str(k["o"]))
    with k4: kpi_card("Rechazo (R)", str(k["r"]))

    k5, k6, k7, k8 = st.columns(4)
    with k5: kpi_card("% Cumple", f"{k['pct_cumple']:.1f}%")
    with k6: kpi_card("Promedio Compactación", f"{k['prom']:.1f}%" if not np.isnan(k["prom"]) else "—")
    with k7: kpi_card("Máx Compactación", f"{k['mx']:.1f}%" if not np.isnan(k["mx"]) else "—")
    with k8: kpi_card("Mín Compactación", f"{k['mn']:.1f}%" if not np.isnan(k["mn"]) else "—")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # Gráficos
    st.subheader("Gráficos (filtrados)")
    g1, g2, g3 = st.columns([1, 1, 2])

    with g1:
        fig1, ax1 = plt.subplots(figsize=(FIG_W, FIG_H))
        ax1.bar(["A", "O", "R"], [k["a"], k["o"], k["r"]])
        ax1.set_title("Estados QA/QC (A/O/R)", fontsize=TITLE_FS)
        ax1.grid(axis="y", linestyle="--", alpha=0.25)
        ax1.tick_params(axis="both", labelsize=TICK_FS)
        plt.tight_layout(pad=0.6)
        st.pyplot(fig1)

    with g2:
        fig2, ax2 = plt.subplots(figsize=(FIG_W, FIG_H))
        ax2.bar(["% Cumple"], [k["pct_cumple"]])
        ax2.set_ylim(0, 100)
        ax2.set_title("% Cumple", fontsize=TITLE_FS)
        ax2.grid(axis="y", linestyle="--", alpha=0.25)
        ax2.tick_params(axis="both", labelsize=TICK_FS)
        ax2.text(0, min(100, k["pct_cumple"] + 2), f"{k['pct_cumple']:.1f}%", ha="center", fontsize=LABEL_FS)
        plt.tight_layout(pad=0.6)
        st.pyplot(fig2)

    with g3:
        st.markdown("**% Compactación por fecha (promedio diario)**")
        if df_f["pct_Compactacion"].notna().any() and df_f["Fecha_control"].notna().any():
            s = df_f.groupby(df_f["Fecha_control"].dt.date)["pct_Compactacion"].mean().sort_index()
            fig3, ax3 = plt.subplots(figsize=(6.2, 2.4))
            ax3.plot(list(s.index), list(s.values), marker="o")
            ax3.axhline(float(UMBRAL_A), linestyle="--")
            ax3.axhline(float(UMBRAL_O), linestyle="--")
            ax3.set_ylabel("% Comp", fontsize=LABEL_FS)
            ax3.set_xlabel("Fecha", fontsize=LABEL_FS)
            ax3.tick_params(axis="x", rotation=45, labelsize=TICK_FS)
            ax3.grid(axis="y", linestyle="--", alpha=0.25)
            plt.tight_layout(pad=0.6)
            st.pyplot(fig3)
        else:
            st.info("Sin datos de compactación para graficar.")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # Control chart
    st.subheader("Gráfico de control (por fecha, cada 3 controles)")
    cs = control_series_by_blocks_of_3(df_f)

    if cs.empty:
        st.info("No hay suficientes registros con % compactación para el control.")
    else:
        mean = float(np.mean(cs["pct_mean"].values))
        std = float(np.std(cs["pct_mean"].values, ddof=1)) if len(cs) > 1 else 0.0
        ucl = mean + 3 * std
        lcl = mean - 3 * std

        figc, axc = plt.subplots(figsize=(8.2, 2.8))
        axc.plot(cs["x_label"].tolist(), cs["pct_mean"].tolist(), marker="o")
        axc.axhline(mean, linestyle="--", label="Media")
        axc.axhline(ucl, linestyle="--", label="UCL")
        axc.axhline(lcl, linestyle="--", label="LCL")
        axc.set_ylabel("% Comp (bloques de 3)", fontsize=LABEL_FS)
        axc.set_xlabel("Fecha (Bloque)", fontsize=LABEL_FS)
        axc.tick_params(axis="x", rotation=45, labelsize=TICK_FS)
        axc.grid(axis="y", linestyle="--", alpha=0.25)
        axc.legend(fontsize=8, loc="best")
        plt.tight_layout(pad=0.6)
        st.pyplot(figc)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # Tabla + export + eliminar
    st.subheader("Registros filtrados — Eliminar / Exportar")

    if df_f.empty:
        st.info("No hay registros con los filtros actuales.")
    else:
        df_view = df_f.sort_values(["Timestamp", "ID_Registro"], ascending=False).copy()

        max_rows = int(len(df_view))
        filas_visibles = max_rows if max_rows <= 1 else st.slider("Filas visibles (filtrado)", 1, max_rows, min(120, max_rows))

        df_view = df_view.head(int(filas_visibles)).copy()
        df_view_user = df_view.drop(columns=["RowKey"]).copy()

        try:
            st.dataframe(style_table(df_view_user), use_container_width=True, height=340)
        except Exception:
            st.dataframe(df_view_user, use_container_width=True, height=340)

        a1, a2, a3 = st.columns([1.2, 1.6, 3.2])

        with a1:
            ids = df_view["ID_Registro"].dropna().astype(int).tolist()
            ids = sorted(list(dict.fromkeys(ids)))

            sel_ids = st.multiselect("ID_Registro a eliminar", options=ids, default=[])

            if st.button("🗑️ ELIMINAR seleccionados", type="primary", use_container_width=True):
                if not sel_ids:
                    st.warning("No seleccionaste ningún ID_Registro.")
                else:
                    df_new, n_del = delete_by_ids(df_all, sel_ids)
                    save_data(df_new, DATA_FILE)
                    st.success(f"Eliminados {n_del} registro(s).")
                    # resetea aplicado para evitar “fantasmas” en pantalla 2
                    st.session_state["P2_APPLIED"] = False
                    st.rerun()

        with a2:
            export_df = df_f.drop(columns=["RowKey"]).copy()
            xbytes = export_excel_bytes(export_df, df_kpi)
            st.download_button(
                "⬇️ Exportar Excel (Filtrado + KPIs)",
                data=xbytes,
                file_name=f"QINTEGRITY_Densidades_Dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with a3:
            st.caption("El usuario elimina por **ID_Registro**. Internamente se borra seguro por RowKey. Export: **Datos filtrados + KPIs**.")
