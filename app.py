# =========================================================
# Q-INTEGRITY – DENSIDADES (PANTALLA 1 + PANTALLA 2)
# FIXES PRO:
# 1) Sector/Zona y Tramo: SOLO DIGITAR (sin listas obligatorias)
# 2) Editar registros (P1 y P2): cargar por ID -> guardar cambios (UPDATE real)
# 3) Recalcular: botón real (force rerun)
# 4) Limpiar: robusto (siempre a la primera)
# 5) Eliminar funciona (limpia IDs inválidos del multiselect)
# 6) Valida numéricos: si pones letras en coords/cota/dm/etc, NO guarda
# 7) Anti duplicado (doble click + ventana anti duplicación)
#
# FIX ÚNICO PEDIDO (SIN CAMBIAR EL PROGRAMA):
# ✅ MÉTODO GUARDA SIEMPRE + NO SE DUPLICA + EDITAR CARGA BIEN MÉTODO
# (Se corrige SOLO la lógica de carga/selección/guardado del campo Método)
# =========================================================

import os
import io
import uuid
import time
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
TEMPLATE_FILE = "QI-DEN-PLT_FINAL_CORREGIDO_v12.xlsx"  # opcional

FIG_W = 3.2
FIG_H = 2.2
TITLE_FS = 10
TICK_FS = 8
LABEL_FS = 9

DEFAULT_TOL_HUM_OPT = 2.0
DEFAULT_OBS_BAND = 2.0
DEFAULT_KEEP_VALUES = False

ANTI_DOUBLECLICK_SECONDS = 1.2
ANTI_DUPLICATE_WINDOW_SECONDS = 8

# ---------------------------------------------------------
# ESTILO UI
# ---------------------------------------------------------
st.markdown(
    """
<style>
.stApp { background:#f4f6fb; }

.qi-topbar{ background: #0f2f4f; padding: 10px 14px; border-radius: 14px; margin-bottom: 12px; }
.qi-title{ color:#ffffff; font-size:22px; font-weight:900; margin:0; line-height:1.1; }
.qi-subtitle{ color:#cfe0ee; font-size:13px; margin:0; }

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

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="datepicker"] > div{
  background:#eaf1fb !important;
  border:1px solid #7fa0d2 !important;
  border-radius:12px !important;
}
div[data-baseweb="input"] input{ color:#0f172a !important; font-weight:800 !important; }
div[data-baseweb="textarea"] textarea{ color:#0f172a !important; font-weight:800 !important; }
div[data-baseweb="select"] span{ color:#0f172a !important; font-weight:800 !important; }
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="textarea"] textarea::placeholder{ color:#64748b !important; opacity:1 !important; }

label { font-weight: 900 !important; color:#0f172a !important; }

div[data-testid="stDataFrame"] div[role="grid"]{
  border: 2px solid #aabbd6 !important;
  border-radius: 12px !important;
}
div[data-testid="stDataFrame"] div[role="columnheader"]{
  background: #dfe8f7 !important;
  font-weight: 900 !important;
  color:#0f172a !important;
}
div[data-testid="stDataFrame"] div[role="gridcell"]{ background: #ffffff !important; }

.qi-chip{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:900; font-size:12px; margin-right:8px; }
.qi-green{ background:#e7f6ea; color:#1b5e20; border:1px solid #bfe8c6; }
.qi-amber{ background:#fff4db; color:#7a4f00; border:1px solid #ffd68a; }
.qi-red{ background:#fde7ea; color:#8a1c1c; border:1px solid #f6b9c1; }
.qi-muted{ color:#475569; }

button[kind="primary"] { border-radius: 12px !important; font-weight: 900 !important; }
button { border-radius: 12px !important; font-weight: 800 !important; }

section[data-testid="stSidebar"]{ background:#0f2f4f !important; }
section[data-testid="stSidebar"] *{ color:#e5e7eb !important; }
section[data-testid="stSidebar"] label{ color:#e5e7eb !important; }
section[data-testid="stSidebar"] .qi-card, section[data-testid="stSidebar"] .qi-card *{ color:#0f172a !important; }
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stTextArea textarea{ color:#0f172a !important; }
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
        <p class="qi-subtitle">Módulo Densidades · Pantalla 1 (Ingreso/Editar/Eliminar) + Pantalla 2 (KPIs/Dashboard/Export)</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# COLUMNAS BD
# ---------------------------------------------------------
COLUMNS = [
    "RowKey",
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
        pd.DataFrame(columns=COLUMNS).to_excel(path, index=False, engine="openpyxl")

def ensure_config_file(path: str) -> None:
    """Config solo para Métodos (sectores/tramos ya NO se usan por decisión de negocio: se digitan)."""
    if os.path.exists(path):
        return
    metodos  = ["Cono de Arena", "Densímetro Nuclear", "Corte y Pesada", "Balón de caucho"]
    df = pd.DataFrame({"Metodos": metodos})
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Listas")

def load_config_lists(path: str) -> Dict[str, List[str]]:
    ensure_config_file(path)
    try:
        df = pd.read_excel(path, sheet_name="Listas")
        metodos = df.get("Metodos", pd.Series([], dtype=str)).dropna().astype(str).tolist()
        metodos = [m.strip() for m in metodos if str(m).strip()]
        return {"metodos": metodos}
    except Exception:
        return {"metodos": ["Cono de Arena", "Densímetro Nuclear"]}

def save_config_lists(path: str, metodos: List[str]) -> None:
    metodos = [m.strip() for m in metodos if str(m).strip()]
    df = pd.DataFrame({"Metodos": metodos})
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Listas")

def load_lists_from_template(template_path: str) -> Dict:
    defaults = {"metodos": [], "umbral_cumple": 92.0, "umbral_obs": 90.0}
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

        metodos = pull_any(["Metodo", "Método", "Metodos", "Métodos", "Columna5"])

        umbral_cumple = defaults["umbral_cumple"]
        umbral_obs = defaults["umbral_obs"]
        if "Columna7" in df_l.columns and "Columna8" in df_l.columns:
            params = pd.DataFrame({"k": df_l["Columna7"], "v": df_l["Columna8"]}).dropna()
            params["k"] = params["k"].astype(str).str.strip()
            for _, r in params.iterrows():
                try:
                    k = str(r["k"]); v = float(r["v"])
                    if "Umbral_A" in k or "UMBRAL_A" in k: umbral_cumple = v
                    if "Umbral_O" in k or "UMBRAL_O" in k: umbral_obs = v
                except Exception:
                    pass

        return {"metodos": metodos, "umbral_cumple": float(umbral_cumple), "umbral_obs": float(umbral_obs)}
    except Exception:
        return defaults

def save_data(df: pd.DataFrame, path: str) -> None:
    out = df.copy()
    for c in COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[COLUMNS]
    out.to_excel(path, index=False, engine="openpyxl")

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path) if os.path.exists(path) else pd.DataFrame(columns=COLUMNS)
    rename_map = {"Observación": "Observacion", "Método": "Metodo", "Fecha": "Fecha_control", "_RowKey": "RowKey"}
    df.rename(columns={c: rename_map.get(c, c) for c in df.columns}, inplace=True)

    for c in COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[COLUMNS].copy()

    df["ID_Registro"] = pd.to_numeric(df["ID_Registro"], errors="coerce")
    df["Fecha_control"] = pd.to_datetime(df["Fecha_control"], errors="coerce")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # IMPORTANT: asegurar texto Metodo/Operador para no romper widgets
    df["Metodo"] = df["Metodo"].fillna("").astype(str)
    df["Operador"] = df["Operador"].fillna("").astype(str)

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

    if df["ID_Registro"].notna().any():
        df.loc[df["ID_Registro"].notna(), "ID_Registro"] = df.loc[df["ID_Registro"].notna(), "ID_Registro"].astype(int)

    return df

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
            "Total_muestras","Cant_Aprobacion","Cant_Observacion","Cant_Rechazo","Pct_Cumple",
            "Promedio_Compactacion","Max_Compactacion","Min_Compactacion"
        ],
        "Valor": [
            total, a, o, r, round(pct_cumple, 2),
            round(prom, 2) if not np.isnan(prom) else np.nan,
            round(mx, 2) if not np.isnan(mx) else np.nan,
            round(mn, 2) if not np.isnan(mn) else np.nan,
        ],
    })
    return df_kpi, {"total": total, "a": a, "o": o, "r": r, "pct_cumple": pct_cumple, "prom": prom, "mx": mx, "mn": mn}

def control_series_by_blocks_of_3(df_f: pd.DataFrame) -> pd.DataFrame:
    d = df_f.copy()
    d = d.dropna(subset=["Fecha_control"]).sort_values(["Fecha_control","Timestamp","ID_Registro"], ascending=True)
    if d.empty:
        return pd.DataFrame(columns=["fecha","block","x_label","pct_mean"])

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
            out_rows.append({"fecha": fecha_val, "block": int(b), "x_label": f"{fecha_val} (B{int(b)})", "pct_mean": pct_mean})
    return pd.DataFrame(out_rows)

def parse_int(txt: str) -> Optional[int]:
    if txt is None: return None
    s = str(txt).strip().replace(",", ".")
    if s == "": return None
    try: return int(float(s))
    except Exception: return None

def parse_float_loose(txt: str) -> Optional[float]:
    if txt is None: return None
    s = str(txt).strip().replace(",", ".")
    if s == "": return None
    try: return float(s)
    except Exception: return None

def is_invalid_number_if_filled(label: str, raw: str) -> Optional[str]:
    """Si el usuario escribió algo y NO es numérico -> error"""
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    v = parse_float_loose(s)
    if v is None:
        return f"⚠️ {label}: debe ser NUMÉRICO (no letras)."
    return None

def style_table(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    def row_bg(row):
        stt = str(row.get("Estado_QAQC", "")).upper().strip()
        if stt == "CUMPLE": return ["background-color: #eef9f0"] * len(row)
        if stt == "OBSERVADO": return ["background-color: #fff7e6"] * len(row)
        if stt == "NO CUMPLE": return ["background-color: #fdeff1"] * len(row)
        return [""] * len(row)
    return (
        df.style
        .apply(row_bg, axis=1)
        .set_table_styles([
            {"selector": "th", "props": "background-color:#dfe8f7; color:#0f172a; font-weight:900;"},
            {"selector": "td", "props": "border:1px solid #d7e1f0;"},
            {"selector": "table", "props": "border-collapse:collapse; width:100%;"},
        ])
    )

def set_last_saved(calc: Optional[Dict]):
    if calc is None:
        st.session_state.pop("LAST_SAVED_CALC", None)
    else:
        st.session_state["LAST_SAVED_CALC"] = calc

def get_last_saved() -> Optional[Dict]:
    d = st.session_state.get("LAST_SAVED_CALC", None)
    return d if isinstance(d, dict) else None

def reset_form_hard(clear_last_saved: bool = True):
    """Reset robusto: setea valores (no pop) + rerun externo."""
    defaults = {
        "p1_fecha_ctrl": date.today(),
        "p1_cod_proy": "",
        "p1_proyecto": "",
        "p1_n_reg": "",
        "p1_n_ctrl": "",
        "p1_n_acta": "",
        "p1_sector_txt": "",
        "p1_tramo_txt": "",
        "p1_frente": "",
        "p1_capa_txt": "",
        "p1_esp_txt": "",
        "p1_dm_ini_txt": "",
        "p1_dm_ter_txt": "",
        "p1_dm_ctrl_txt": "",
        "p1_coord_n_txt": "",
        "p1_coord_e_txt": "",
        "p1_cota_txt": "",
        "p1_operador": "",
        "p1_met_sel": "— Seleccionar —",
        "p1_met_otro": "",
        "p1_prof_txt": "",
        "p1_obs": "",
        "p1_dh_num": 0.0,
        "p1_h_num": 0.0,
        "p1_hopt_num": 0.0,
        "p1_dmcs_num": 0.0,
        "p1_del_ids": [],
        "P1_EDIT_ID": None,
        "P1_EDIT_ROWKEY": None,
    }
    for k, v in defaults.items():
        st.session_state[k] = v

    if clear_last_saved:
        set_last_saved(None)

def delete_by_ids(df_all: pd.DataFrame, ids_to_delete: List[int]) -> Tuple[pd.DataFrame, int]:
    if df_all.empty or not ids_to_delete:
        return df_all, 0
    ids_to_delete = [int(x) for x in ids_to_delete]
    before = len(df_all)
    df_new = df_all.copy()
    df_new["ID_Registro"] = pd.to_numeric(df_new["ID_Registro"], errors="coerce")
    df_new = df_new[~df_new["ID_Registro"].isin(ids_to_delete)].copy()
    return df_new, (before - len(df_new))

def record_signature(d: Dict) -> str:
    parts = [
        str(d.get("Codigo_Proyecto","")).strip(),
        str(d.get("Proyecto","")).strip(),
        str(d.get("Fecha_control","")).strip(),
        str(d.get("Sector_Zona","")).strip(),
        str(d.get("Tramo","")).strip(),
        str(d.get("Operador","")).strip(),
        str(d.get("Metodo","")).strip(),
        str(d.get("Densidad_Humeda_gcm3","")).strip(),
        str(d.get("Humedad_medida_pct","")).strip(),
        str(d.get("Humedad_Optima_pct","")).strip(),
        str(d.get("DMCS_Proctor_gcm3","")).strip(),
        str(d.get("N_Control","")).strip(),
        str(d.get("N_Registro","")).strip(),
        str(d.get("N_Acta","")).strip(),
    ]
    return "|".join(parts)

def is_duplicate_recent(df: pd.DataFrame, sig: str, seconds: int = ANTI_DUPLICATE_WINDOW_SECONDS) -> bool:
    if df.empty or "Timestamp" not in df.columns:
        return False
    try:
        now = datetime.now()
        d2 = df.dropna(subset=["Timestamp"]).copy()
        if d2.empty: return False
        d2 = d2.sort_values("Timestamp", ascending=False).head(50)
        d2["__sig"] = d2.apply(lambda r: record_signature(r.to_dict()), axis=1)
        d2["__dt"] = pd.to_datetime(d2["Timestamp"], errors="coerce")
        d2 = d2.dropna(subset=["__dt"])
        if d2.empty: return False
        recent = d2[(now - d2["__dt"]).dt.total_seconds() <= float(seconds)]
        return bool((recent["__sig"] == sig).any())
    except Exception:
        return False

def get_record_by_id(df: pd.DataFrame, rid: int) -> Optional[pd.Series]:
    if df.empty:
        return None
    d = df.copy()
    d["ID_Registro"] = pd.to_numeric(d["ID_Registro"], errors="coerce")
    d = d[d["ID_Registro"] == int(rid)]
    if d.empty:
        return None
    d = d.sort_values("Timestamp", ascending=False)
    return d.iloc[0]

def load_record_into_form(row: pd.Series):
    """Carga registro en inputs P1 para editar."""
    st.session_state["P1_EDIT_ID"] = int(row.get("ID_Registro"))
    st.session_state["P1_EDIT_ROWKEY"] = str(row.get("RowKey"))

    st.session_state["p1_fecha_ctrl"] = row.get("Fecha_control").date() if pd.notna(row.get("Fecha_control")) else date.today()
    st.session_state["p1_cod_proy"] = str(row.get("Codigo_Proyecto") or "")
    st.session_state["p1_proyecto"] = str(row.get("Proyecto") or "")
    st.session_state["p1_n_reg"] = str(row.get("N_Registro") or "")
    st.session_state["p1_n_ctrl"] = str(row.get("N_Control") or "")
    st.session_state["p1_n_acta"] = str(row.get("N_Acta") or "")

    st.session_state["p1_sector_txt"] = str(row.get("Sector_Zona") or "")
    st.session_state["p1_tramo_txt"] = str(row.get("Tramo") or "")
    st.session_state["p1_frente"] = str(row.get("Frente_Tramo") or "")

    st.session_state["p1_capa_txt"] = "" if pd.isna(row.get("Capa_N")) else str(int(row.get("Capa_N")))
    st.session_state["p1_esp_txt"] = "" if pd.isna(row.get("Espesor_capa_cm")) else str(float(row.get("Espesor_capa_cm")))
    st.session_state["p1_dm_ini_txt"] = "" if pd.isna(row.get("Dm_inicio")) else str(float(row.get("Dm_inicio")))
    st.session_state["p1_dm_ter_txt"] = "" if pd.isna(row.get("Dm_termino")) else str(float(row.get("Dm_termino")))
    st.session_state["p1_dm_ctrl_txt"] = "" if pd.isna(row.get("Dm_Control")) else str(float(row.get("Dm_Control")))

    st.session_state["p1_coord_n_txt"] = "" if pd.isna(row.get("Coordenada_Norte")) else str(float(row.get("Coordenada_Norte")))
    st.session_state["p1_coord_e_txt"] = "" if pd.isna(row.get("Coordenada_Este")) else str(float(row.get("Coordenada_Este")))
    st.session_state["p1_cota_txt"] = "" if pd.isna(row.get("Cota")) else str(float(row.get("Cota")))

    st.session_state["p1_operador"] = str(row.get("Operador") or "")
    st.session_state["p1_prof_txt"] = "" if pd.isna(row.get("Profundidad_cm")) else str(float(row.get("Profundidad_cm")))

    # =========================================================
    # FIX DEFINITIVO MÉTODO (CARGA EDIT SIN ROMPER SELECTBOX)
    # - Si el método está en la lista -> lo selecciona
    # - Si NO está -> pone "Otro (digitar)" y rellena p1_met_otro
    # =========================================================
    metodo_val = str(row.get("Metodo") or "").strip()

    # lista actual de métodos (guardada en session_state al iniciar)
    met_list = st.session_state.get("METODOS_LIST", [])
    met_opts = ["— Seleccionar —", *met_list, "Otro (digitar)"]

    if metodo_val and (metodo_val in met_opts):
        st.session_state["p1_met_sel"] = metodo_val
        st.session_state["p1_met_otro"] = ""
    elif metodo_val:
        st.session_state["p1_met_sel"] = "Otro (digitar)"
        st.session_state["p1_met_otro"] = metodo_val
    else:
        st.session_state["p1_met_sel"] = "— Seleccionar —"
        st.session_state["p1_met_otro"] = ""

    st.session_state["p1_dh_num"] = float(row.get("Densidad_Humeda_gcm3")) if pd.notna(row.get("Densidad_Humeda_gcm3")) else 0.0
    st.session_state["p1_h_num"] = float(row.get("Humedad_medida_pct")) if pd.notna(row.get("Humedad_medida_pct")) else 0.0
    st.session_state["p1_hopt_num"] = float(row.get("Humedad_Optima_pct")) if pd.notna(row.get("Humedad_Optima_pct")) else 0.0
    st.session_state["p1_dmcs_num"] = float(row.get("DMCS_Proctor_gcm3")) if pd.notna(row.get("DMCS_Proctor_gcm3")) else 0.0

    st.session_state["p1_obs"] = str(row.get("Observacion") or "")

def apply_update_by_rowkey(df: pd.DataFrame, rowkey: str, new_values: Dict) -> Tuple[pd.DataFrame, bool]:
    if df.empty:
        return df, False
    d = df.copy()
    mask = d["RowKey"].astype(str) == str(rowkey)
    if not mask.any():
        return df, False
    for k, v in new_values.items():
        if k in d.columns:
            d.loc[mask, k] = v
    return d, True

# ---------------------------------------------------------
# INIT
# ---------------------------------------------------------
ensure_data_file(DATA_FILE)
ensure_config_file(CONFIG_FILE)

tpl = load_lists_from_template(TEMPLATE_FILE)
cfg = load_config_lists(CONFIG_FILE)

metodos = list(dict.fromkeys([*cfg.get("metodos", []), *tpl.get("metodos", [])])) or ["Cono de Arena", "Densímetro Nuclear"]

# ✅ guardar lista final en session_state para que EDIT cargue bien método
st.session_state["METODOS_LIST"] = metodos

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("### Parámetros QA/QC")

tol_hum_opt = st.sidebar.number_input(
    "Tolerancia Humedad Óptima (±%)",
    value=float(st.session_state.get("TOL_HUM_OPT", DEFAULT_TOL_HUM_OPT)),
    step=0.5, format="%.1f"
)
st.session_state["TOL_HUM_OPT"] = float(tol_hum_opt)

if "UMBRAL_A" not in st.session_state:
    st.session_state["UMBRAL_A"] = float(tpl.get("umbral_cumple", 92.0) or 92.0)
if "UMBRAL_O_RAW" not in st.session_state:
    st.session_state["UMBRAL_O_RAW"] = float(tpl.get("umbral_obs", 90.0) or 90.0)

UMBRAL_A = st.sidebar.number_input("Umbral A (CUMPLE ≥ %)", value=float(st.session_state["UMBRAL_A"]), step=0.5, format="%.1f")
UMBRAL_O_RAW = st.sidebar.number_input("Umbral O (OBSERVADO ≥ %)", value=float(st.session_state["UMBRAL_O_RAW"]), step=0.5, format="%.1f")
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
    <b>O auto-ajustado</b>: A={float(UMBRAL_A):.1f}% · O(usado)={float(UMBRAL_O):.1f}%
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar.expander("⚙️ Administrar lista (Métodos)", expanded=False):
    txt_met = st.text_area("Métodos (1 por línea)", value="\n".join(metodos), height=160, key="cfg_met")
    if st.button("💾 Guardar lista", use_container_width=True):
        new_met = [x.strip() for x in txt_met.splitlines() if x.strip()]
        save_config_lists(CONFIG_FILE, new_met)
        st.success("Lista guardada.")
        st.rerun()

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

# ---------------------------------------------------------
# DEFAULTS
# ---------------------------------------------------------
if "p1_keep" not in st.session_state:
    st.session_state["p1_keep"] = bool(DEFAULT_KEEP_VALUES)

# =========================================================
# PANTALLA 1
# =========================================================
if st.session_state["PAGE"] == "P1":
    st.caption("Pantalla 1 · Ingreso + Cálculos + Tabla (Ver) + Edición + Eliminación por ID + Export (Base + KPIs)")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    df_all0 = load_data(DATA_FILE)
    ids_all0 = sorted(df_all0["ID_Registro"].dropna().astype(int).unique().tolist()) if not df_all0.empty else []

    topb1, topb2, topb3, topb4, topb5 = st.columns([2.2, 1.1, 1.3, 1.8, 2.0])

    with topb1:
        keep_values = st.checkbox(
            "Mantener valores después de guardar (si lo desmarcas, queda todo en blanco)",
            value=bool(st.session_state.get("p1_keep", False)),
            key="p1_keep_chk"
        )
        st.session_state["p1_keep"] = bool(keep_values)

    with topb2:
        if st.button("🧹 LIMPIAR", use_container_width=True):
            reset_form_hard(clear_last_saved=True)
            st.rerun()

    with topb3:
        if st.button("🔄 RECALCULAR", use_container_width=True):
            st.session_state["FORCE_RECALC_TS"] = time.time()
            st.rerun()

    with topb4:
        edit_id = st.selectbox(
            "✏️ Editar ID",
            options=[None] + ids_all0,
            index=0,
            key="P1_EDIT_PICK",
            help="Selecciona un ID, carga en formulario y luego guarda cambios."
        )

    with topb5:
        with st.expander("🗑️ Demo (opcional)", expanded=False):
            if st.button("VACIAR BASE (borra todo)", type="primary", use_container_width=True):
                save_data(pd.DataFrame(columns=COLUMNS), DATA_FILE)
                reset_form_hard(clear_last_saved=True)
                st.success("Base vaciada.")
                st.rerun()

    if edit_id is not None:
        if st.button("✏️ Cargar ID seleccionado en formulario", use_container_width=True):
            df_temp = load_data(DATA_FILE)
            row = get_record_by_id(df_temp, int(edit_id))
            if row is None:
                st.error("No encontré ese ID en la base.")
            else:
                load_record_into_form(row)
                st.success(f"ID {int(edit_id)} cargado. Modifica y luego presiona **Guardar cambios**.")
                st.rerun()

    # ---------- SECCIÓN 1 ----------
    st.markdown("<div class='qi-section'><div class='qi-h3'>Identificación y Control</div>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        fecha_ctrl = st.date_input("Fecha control", value=st.session_state.get("p1_fecha_ctrl", date.today()), key="p1_fecha_ctrl")
        codigo_proy = st.text_input("Código de Proyecto", value=st.session_state.get("p1_cod_proy", ""), key="p1_cod_proy").strip()
    with a2:
        proyecto = st.text_input("Proyecto (DIGITAR)", value=st.session_state.get("p1_proyecto", ""), key="p1_proyecto").strip()
        n_registro = st.text_input("N° Registro", value=st.session_state.get("p1_n_reg", ""), key="p1_n_reg").strip()
    with a3:
        n_control = st.text_input("N° Control", value=st.session_state.get("p1_n_ctrl", ""), key="p1_n_ctrl").strip()
        n_acta = st.text_input("N° Acta", value=st.session_state.get("p1_n_acta", ""), key="p1_n_acta").strip()
    with a4:
        sector_final = st.text_input("Sector/Zona (DIGITAR)", value=st.session_state.get("p1_sector_txt", ""), key="p1_sector_txt").strip()
        tramo_final  = st.text_input("Tramo (DIGITAR)", value=st.session_state.get("p1_tramo_txt", ""), key="p1_tramo_txt").strip()

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- SECCIÓN 2 ----------
    st.markdown("<div class='qi-section'><div class='qi-h3'>Ubicación / Geometría</div>", unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        capa_txt = st.text_input("N° Capa", value=st.session_state.get("p1_capa_txt", ""), placeholder="Ej: 1", key="p1_capa_txt")
        esp_txt  = st.text_input("Espesor capa (cm)", value=st.session_state.get("p1_esp_txt", ""), placeholder="Ej: 30.0", key="p1_esp_txt")
    with b2:
        dm_ini_txt = st.text_input("Dm inicio", value=st.session_state.get("p1_dm_ini_txt", ""), placeholder="Ej: 0", key="p1_dm_ini_txt")
        dm_ter_txt = st.text_input("Dm término", value=st.session_state.get("p1_dm_ter_txt", ""), placeholder="Ej: 100", key="p1_dm_ter_txt")
    with b3:
        dm_ctrl_txt = st.text_input("Dm Control", value=st.session_state.get("p1_dm_ctrl_txt", ""), placeholder="Ej: 50", key="p1_dm_ctrl_txt")
        cota_txt    = st.text_input("Cota", value=st.session_state.get("p1_cota_txt", ""), placeholder="Ej: 123.456", key="p1_cota_txt")
    with b4:
        coord_n_txt = st.text_input("Coordenada Norte", value=st.session_state.get("p1_coord_n_txt", ""), placeholder="Ej: 6220000.000", key="p1_coord_n_txt")
        coord_e_txt = st.text_input("Coordenada Este",  value=st.session_state.get("p1_coord_e_txt", ""), placeholder="Ej: 350000.000", key="p1_coord_e_txt")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- SECCIÓN 3 ----------
    st.markdown("<div class='qi-section'><div class='qi-h3'>Operación / Ensayo</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        operador = st.text_input("Operador (DIGITAR)", value=st.session_state.get("p1_operador", ""), key="p1_operador").strip()
        prof_txt = st.text_input("Profundidad (cm)", value=st.session_state.get("p1_prof_txt", ""), placeholder="Ej: 20", key="p1_prof_txt")

    # =========================================================
    # FIX DEFINITIVO MÉTODO (WIDGET ÚNICO + ÍNDICE CORRECTO)
    # =========================================================
    with c2:
        met_opts = ["— Seleccionar —", *metodos, "Otro (digitar)"]
        current_met = st.session_state.get("p1_met_sel", "— Seleccionar —")
        if current_met not in met_opts:
            # si quedó algún valor raro por edición antigua, lo manda a "Otro"
            current_met = "Otro (digitar)" if str(st.session_state.get("p1_met_otro", "")).strip() else "— Seleccionar —"
            st.session_state["p1_met_sel"] = current_met

        met_sel = st.selectbox("Método", met_opts, index=met_opts.index(current_met), key="p1_met_sel")

        met_otro = ""
        if met_sel == "Otro (digitar)":
            met_otro = st.text_input("Método (otro)", value=st.session_state.get("p1_met_otro", ""), key="p1_met_otro")

        frente = st.text_input("Frente / Detalle", value=st.session_state.get("p1_frente", ""), key="p1_frente").strip()

    metodo_final = (met_otro.strip() if met_sel == "Otro (digitar)" else ("" if met_sel == "— Seleccionar —" else met_sel)).strip()

    with c3:
        dh_num = st.number_input("Densidad Húmeda (g/cm³)", value=float(st.session_state.get("p1_dh_num", 0.0)), min_value=0.0, step=0.001, format="%.3f", key="p1_dh_num")
        h_num  = st.number_input("Humedad medida (%)", value=float(st.session_state.get("p1_h_num", 0.0)), min_value=0.0, step=0.1, format="%.1f", key="p1_h_num")
    with c4:
        hopt_num = st.number_input("Humedad óptima Proctor (%)", value=float(st.session_state.get("p1_hopt_num", 0.0)), min_value=0.0, step=0.1, format="%.1f", key="p1_hopt_num")
        dmcs_num = st.number_input("DMCS Proctor (g/cm³)", value=float(st.session_state.get("p1_dmcs_num", 0.0)), min_value=0.0, step=0.001, format="%.3f", key="p1_dmcs_num")

    observacion = st.text_area("Observación", value=st.session_state.get("p1_obs", ""), key="p1_obs")
    st.markdown("</div>", unsafe_allow_html=True)

    # ==============================
    # CALC (LIVE) + FALLBACK A ÚLTIMO GUARDADO
    # ==============================
    dens_h_v = float(dh_num) if float(dh_num) > 0 else None
    hum_v    = float(h_num) if float(h_num) > 0 else None
    hopt_v   = float(hopt_num) if float(hopt_num) > 0 else None
    dmcs_v   = float(dmcs_num) if float(dmcs_num) > 0 else None

    has_live = (dens_h_v is not None) and (hum_v is not None) and (hopt_v is not None) and (dmcs_v is not None) and (dmcs_v > 0)

    dens_s_disp, pct_disp = np.nan, np.nan
    delta_disp, vent_disp = np.nan, "—"
    estado_disp = "—"

    if has_live:
        dens_s_disp = calc_densidad_seca(dens_h_v, hum_v)
        pct_disp = calc_pct_comp(dens_s_disp, dmcs_v)
        estado_disp = estado_qaqc(float(pct_disp), float(UMBRAL_A), float(UMBRAL_O)) if pd.notna(pct_disp) else "—"
        delta_disp = hum_v - hopt_v
        vent_disp = "OK" if abs(delta_disp) <= float(tol_hum_opt) else "OBSERVADO"
    else:
        last = get_last_saved()
        if last:
            dens_s_disp = last.get("dens_s", np.nan)
            pct_disp = last.get("pct", np.nan)
            delta_disp = last.get("delta", np.nan)
            vent_disp = last.get("ventana", "—")
            estado_disp = last.get("estado", "—")

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1: kpi_card("Densidad Seca (g/cm³)", f"{dens_s_disp:.3f}" if pd.notna(dens_s_disp) else "—")
    with r2: kpi_card("% Compactación", f"{pct_disp:.1f}%" if pd.notna(pct_disp) else "—", f"A={float(UMBRAL_A):.1f}% · O={float(UMBRAL_O):.1f}%")
    with r3: kpi_card("Δ Humedad (Terreno-Proctor)", f"{delta_disp:+.2f}%" if pd.notna(delta_disp) else "—", f"Ventana ±{float(tol_hum_opt):.1f}% → {vent_disp}")
    with r4:
        color = "#1b5e20" if estado_disp == "CUMPLE" else ("#7a4f00" if estado_disp == "OBSERVADO" else "#8a1c1c")
        st.markdown(
            f"""
            <div class="qi-card">
                <div style="color:#64748b;font-size:0.90rem;font-weight:900">Estado QA/QC</div>
                <div style="color:{color};font-size:1.8rem;font-weight:900;margin-top:6px">{estado_disp}</div>
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

    # Botones Guardar / Guardar cambios
    left_save, mid_save, right_save = st.columns([1.3, 1.3, 3.4])
    with left_save:
        guardar = st.button("💾 Guardar registro", type="primary", use_container_width=True)

    with mid_save:
        guardar_cambios = st.button("💾 Guardar cambios (EDIT)", use_container_width=True)

    with right_save:
        edit_info = ""
        if st.session_state.get("P1_EDIT_ID") and st.session_state.get("P1_EDIT_ROWKEY"):
            edit_info = f"Editando ID={st.session_state['P1_EDIT_ID']} ✅"
        else:
            edit_info = "Modo nuevo registro ✅"
        st.info(f"{edit_info} · Para calcular: llena 4 campos numéricos (DH, H, Hopt, DMCS).")

    # Guardar (nuevo)
    if guardar:
        now_ts = time.time()
        last_ts = float(st.session_state.get("LAST_SUBMIT_TS", 0.0))
        if (now_ts - last_ts) < ANTI_DOUBLECLICK_SECONDS:
            st.warning("⚠️ Botón presionado muy rápido. Se bloqueó para evitar duplicidad.")
            st.stop()
        st.session_state["LAST_SUBMIT_TS"] = now_ts

        errs = []
        for label, raw in [
            ("Espesor capa (cm)", esp_txt),
            ("Dm inicio", dm_ini_txt),
            ("Dm término", dm_ter_txt),
            ("Dm Control", dm_ctrl_txt),
            ("Coordenada Norte", coord_n_txt),
            ("Coordenada Este", coord_e_txt),
            ("Cota", cota_txt),
            ("Profundidad (cm)", prof_txt),
            ("N° Capa", capa_txt),
        ]:
            e = is_invalid_number_if_filled(label, raw)
            if e:
                errs.append(e)

        if not codigo_proy: errs.append("⚠️ Falta Código de Proyecto.")
        if not proyecto:   errs.append("⚠️ Falta Proyecto.")
        if not operador:   errs.append("⚠️ Falta Operador.")
        if not sector_final: errs.append("⚠️ Falta Sector/Zona (digitado).")
        if not metodo_final: errs.append("⚠️ Falta Método.")

        if dens_h_v is None: errs.append("⚠️ Densidad Húmeda inválida (debe ser > 0).")
        if dmcs_v is None or dmcs_v <= 0: errs.append("⚠️ DMCS Proctor inválido (debe ser > 0).")
        if hum_v is None:    errs.append("⚠️ Humedad medida inválida (debe ser > 0).")
        if hopt_v is None:   errs.append("⚠️ Humedad óptima inválida (debe ser > 0).")

        if errs:
            for e in errs:
                st.error(e)
            st.stop()

        capa = parse_int(capa_txt)
        espesor_cm = parse_float_loose(esp_txt)
        dm_ini = parse_float_loose(dm_ini_txt)
        dm_ter = parse_float_loose(dm_ter_txt)
        dm_control = parse_float_loose(dm_ctrl_txt)
        cota = parse_float_loose(cota_txt)
        coord_n = parse_float_loose(coord_n_txt)
        coord_e = parse_float_loose(coord_e_txt)
        prof_cm = parse_float_loose(prof_txt)

        dens_s = calc_densidad_seca(float(dens_h_v), float(hum_v))
        pct_comp = calc_pct_comp(float(dens_s), float(dmcs_v))
        delta_h = float(hum_v) - float(hopt_v)
        ventana = "OK" if abs(delta_h) <= float(tol_hum_opt) else "OBSERVADO"
        estado = estado_qaqc(float(pct_comp), float(UMBRAL_A), float(UMBRAL_O))

        df_now = load_data(DATA_FILE)
        new_id = int(next_id(df_now))

        nuevo = {
            "RowKey": _safe_uuid(),
            "ID_Registro": new_id,
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
            "Densidad_Humeda_gcm3": float(dens_h_v),
            "Humedad_medida_pct": float(hum_v),
            "Humedad_Optima_pct": float(hopt_v),
            "Delta_Humedad_pct": float(delta_h),
            "Ventana_Humedad": str(ventana),
            "Densidad_Seca_gcm3": float(dens_s),
            "DMCS_Proctor_gcm3": float(dmcs_v),
            "pct_Compactacion": float(pct_comp),
            "Umbral_Cumple_pct": float(UMBRAL_A),
            "Umbral_Observado_pct": float(UMBRAL_O),
            "Estado_QAQC": estado,
            "Observacion": str(observacion).strip(),
            "Timestamp": pd.to_datetime(datetime.now()),
        }

        sig = record_signature(nuevo)
        if is_duplicate_recent(df_now, sig, seconds=ANTI_DUPLICATE_WINDOW_SECONDS):
            st.warning("⚠️ Se detectó un duplicado reciente. No se guardó.")
            st.stop()

        df2 = pd.concat([df_now, pd.DataFrame([nuevo])], ignore_index=True)
        save_data(df2, DATA_FILE)

        set_last_saved({
            "id": new_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "dens_s": float(dens_s),
            "pct": float(pct_comp),
            "delta": float(delta_h),
            "ventana": str(ventana),
            "estado": str(estado),
        })

        if not keep_values:
            reset_form_hard(clear_last_saved=False)
            st.session_state["P1_EDIT_ID"] = None
            st.session_state["P1_EDIT_ROWKEY"] = None

        st.success("Registro guardado correctamente ✅")
        st.rerun()

    # Guardar cambios (update)
    if guardar_cambios:
        rowkey = st.session_state.get("P1_EDIT_ROWKEY")
        rid = st.session_state.get("P1_EDIT_ID")

        if not rowkey or not rid:
            st.warning("Primero carga un ID para editar (arriba: Editar ID → Cargar).")
            st.stop()

        errs = []
        for label, raw in [
            ("Espesor capa (cm)", esp_txt),
            ("Dm inicio", dm_ini_txt),
            ("Dm término", dm_ter_txt),
            ("Dm Control", dm_ctrl_txt),
            ("Coordenada Norte", coord_n_txt),
            ("Coordenada Este", coord_e_txt),
            ("Cota", cota_txt),
            ("Profundidad (cm)", prof_txt),
            ("N° Capa", capa_txt),
        ]:
            e = is_invalid_number_if_filled(label, raw)
            if e:
                errs.append(e)

        if not codigo_proy: errs.append("⚠️ Falta Código de Proyecto.")
        if not proyecto:   errs.append("⚠️ Falta Proyecto.")
        if not operador:   errs.append("⚠️ Falta Operador.")
        if not sector_final: errs.append("⚠️ Falta Sector/Zona (digitado).")
        if not metodo_final: errs.append("⚠️ Falta Método.")

        if dens_h_v is None: errs.append("⚠️ Densidad Húmeda inválida (debe ser > 0).")
        if dmcs_v is None or dmcs_v <= 0: errs.append("⚠️ DMCS Proctor inválido (debe ser > 0).")
        if hum_v is None:    errs.append("⚠️ Humedad medida inválida (debe ser > 0).")
        if hopt_v is None:   errs.append("⚠️ Humedad óptima inválida (debe ser > 0).")

        if errs:
            for e in errs:
                st.error(e)
            st.stop()

        capa = parse_int(capa_txt)
        espesor_cm = parse_float_loose(esp_txt)
        dm_ini = parse_float_loose(dm_ini_txt)
        dm_ter = parse_float_loose(dm_ter_txt)
        dm_control = parse_float_loose(dm_ctrl_txt)
        cota = parse_float_loose(cota_txt)
        coord_n = parse_float_loose(coord_n_txt)
        coord_e = parse_float_loose(coord_e_txt)
        prof_cm = parse_float_loose(prof_txt)

        dens_s = calc_densidad_seca(float(dens_h_v), float(hum_v))
        pct_comp = calc_pct_comp(float(dens_s), float(dmcs_v))
        delta_h = float(hum_v) - float(hopt_v)
        ventana = "OK" if abs(delta_h) <= float(tol_hum_opt) else "OBSERVADO"
        estado = estado_qaqc(float(pct_comp), float(UMBRAL_A), float(UMBRAL_O))

        update_values = {
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
            "Densidad_Humeda_gcm3": float(dens_h_v),
            "Humedad_medida_pct": float(hum_v),
            "Humedad_Optima_pct": float(hopt_v),
            "Delta_Humedad_pct": float(delta_h),
            "Ventana_Humedad": str(ventana),
            "Densidad_Seca_gcm3": float(dens_s),
            "DMCS_Proctor_gcm3": float(dmcs_v),
            "pct_Compactacion": float(pct_comp),
            "Umbral_Cumple_pct": float(UMBRAL_A),
            "Umbral_Observado_pct": float(UMBRAL_O),
            "Estado_QAQC": estado,
            "Observacion": str(observacion).strip(),
            "Timestamp": pd.to_datetime(datetime.now()),
        }

        df_now = load_data(DATA_FILE)
        df_new, ok = apply_update_by_rowkey(df_now, str(rowkey), update_values)
        if not ok:
            st.error("No encontré el RowKey del registro. (Puede que se haya eliminado).")
            st.stop()

        save_data(df_new, DATA_FILE)

        set_last_saved({
            "id": int(rid),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "dens_s": float(dens_s),
            "pct": float(pct_comp),
            "delta": float(delta_h),
            "ventana": str(ventana),
            "estado": str(estado),
        })

        st.success(f"Cambios guardados ✅ (ID {int(rid)})")
        st.rerun()

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
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

    st.subheader("Registros (Base de datos) — Ver / Editar / Eliminar")
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

        ids = sorted(df_show["ID_Registro"].dropna().astype(int).unique().tolist())

        prev_sel = st.session_state.get("p1_del_ids", [])
        if isinstance(prev_sel, list):
            st.session_state["p1_del_ids"] = [int(x) for x in prev_sel if str(x).strip().isdigit() and int(x) in ids]

        sel_ids = st.multiselect("Selecciona ID_Registro a eliminar", options=ids, default=st.session_state.get("p1_del_ids", []), key="p1_del_ids")

        b1, b2 = st.columns([1.4, 2.6])
        with b1:
            if st.button("🗑️ ELIMINAR seleccionados (BORRA EL REGISTRO COMPLETO)", type="primary", use_container_width=True):
                if not sel_ids:
                    st.warning("No seleccionaste ningún ID_Registro.")
                else:
                    df_new, n_del = delete_by_ids(df_all, sel_ids)
                    save_data(df_new, DATA_FILE)
                    st.success(f"Eliminados {n_del} registro(s).")
                    st.session_state["p1_del_ids"] = []
                    if st.session_state.get("P1_EDIT_ID") in sel_ids:
                        st.session_state["P1_EDIT_ID"] = None
                        st.session_state["P1_EDIT_ROWKEY"] = None
                    st.rerun()
        with b2:
            st.caption("Eliminación real por **ID_Registro**. Para editar: usa **Editar ID** arriba y carga en formulario.")

# =========================================================
# PANTALLA 2
# =========================================================
else:
    st.caption("Pantalla 2 · Dashboard KPIs + Gráficos + Control chart + Tabla (Editar/Eliminar/Export)")
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    df_all = load_data(DATA_FILE)
    if df_all.empty:
        st.info("Aún no hay registros. Ingresa datos en Pantalla 1.")
        st.stop()

    st.subheader("Filtros")
    f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 3, 2])

    with f1:
        cods = sorted([c for c in df_all["Codigo_Proyecto"].dropna().astype(str).unique().tolist() if c.strip()])
        sel_cod = st.multiselect("Código Proyecto", options=cods, default=[], key="p2_cod")

    with f2:
        prys = sorted([p for p in df_all["Proyecto"].dropna().astype(str).unique().tolist() if p.strip()])
        sel_proy = st.multiselect("Proyecto", options=prys, default=[], key="p2_proy")

    with f3:
        ops = sorted([o for o in df_all["Operador"].dropna().astype(str).unique().tolist() if o.strip()])
        op_opts = ["— (Todos)"] + ops
        sel_op = st.selectbox("Operador (solo 1)", options=op_opts, index=0, key="p2_op")

    with f4:
        dmin = df_all["Fecha_control"].min()
        dmax = df_all["Fecha_control"].max()
        dmin = dmin.date() if pd.notna(dmin) else date.today()
        dmax = dmax.date() if pd.notna(dmax) else date.today()
        rango = st.date_input("Rango fecha", value=(dmin, dmax), key="p2_rango")

    with f5:
        applied = st.button("✅ Aplicar filtros", type="primary", use_container_width=True)

    if "P2_APPLIED" not in st.session_state:
        st.session_state["P2_APPLIED"] = False
    if applied:
        st.session_state["P2_APPLIED"] = True

    if not st.session_state["P2_APPLIED"]:
        st.info("Pantalla 2 está **limpia** por defecto. Presiona **Aplicar filtros** para cargar KPIs/Gráficos/Tabla.")
        st.stop()

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

    st.subheader("Registros filtrados — Editar / Eliminar / Exportar")

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

        a1, a2, a3, a4 = st.columns([1.2, 1.2, 1.6, 3.0])

        with a1:
            ids = sorted(df_f["ID_Registro"].dropna().astype(int).unique().tolist())
            p2_edit_id = st.selectbox("✏️ Editar ID", options=[None] + ids, index=0, key="p2_edit_id")

            if st.button("✏️ Cargar en Pantalla 1", use_container_width=True):
                if p2_edit_id is None:
                    st.warning("Selecciona un ID.")
                else:
                    row = get_record_by_id(df_all, int(p2_edit_id))
                    if row is None:
                        st.error("No encontré ese ID.")
                    else:
                        load_record_into_form(row)
                        st.session_state["PAGE"] = "P1"
                        st.success("Cargado en Pantalla 1. Ahora edita y presiona Guardar cambios (EDIT).")
                        st.rerun()

        with a2:
            prev_sel = st.session_state.get("p2_del", [])
            if isinstance(prev_sel, list):
                st.session_state["p2_del"] = [int(x) for x in prev_sel if str(x).strip().isdigit() and int(x) in ids]

            sel_ids = st.multiselect("ID_Registro a eliminar", options=ids, default=st.session_state.get("p2_del", []), key="p2_del")

            if st.button("🗑️ ELIMINAR seleccionados", type="primary", use_container_width=True):
                if not sel_ids:
                    st.warning("No seleccionaste ningún ID_Registro.")
                else:
                    df_new, n_del = delete_by_ids(df_all, sel_ids)
                    save_data(df_new, DATA_FILE)
                    st.success(f"Eliminados {n_del} registro(s).")
                    st.session_state["P2_APPLIED"] = False
                    st.session_state["p2_del"] = []
                    st.rerun()

        with a3:
            export_df = df_f.drop(columns=["RowKey"]).copy()
            xbytes = export_excel_bytes(export_df, df_kpi)
            st.download_button(
                "⬇️ Exportar Excel (Filtrado + KPIs)",
                data=xbytes,
                file_name=f"QINTEGRITY_Densidades_Dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with a4:
            st.caption("Editar: carga el ID a Pantalla 1. Eliminar: por ID. Export: **Datos filtrados + KPIs** (listo Power BI).")
