# =========================================================
# Q-INTEGRITY – DENSIDADES (DEMO WEB) ✅ FULL app.py
# FIXES PARA STREAMLIT CLOUD (DEMO HOY):
# 1) "Método" SIEMPRE guarda (selectbox con index=None + placeholder)
# 2) NO revienta con StreamlitAPIException (reset seguro por FORM_VER)
# 3) Guardado robusto en Excel en /data (escritura atómica)
# 4) Tabla + filtros + eliminar por ID + descargar Excel
# =========================================================

import os
import tempfile
from datetime import date, datetime

import pandas as pd
import streamlit as st

# -----------------------------
# CONFIG UI
# -----------------------------
st.set_page_config(page_title="Q-INTEGRITY | Densidades (DEMO)", layout="wide")

# -----------------------------
# PATHS SEGUROS (WEB)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, "qintegrity_densidades.xlsx")
SHEET_NAME = "BD"

# -----------------------------
# CONSTANTES
# -----------------------------
METODOS = [
    "Cono de Arena",
    "Densímetro Nuclear",
    "Método del Globo",
    "Otro",
]

COLS = [
    "ID_Registro",
    "Fecha",
    "Proyecto",
    "Frente",
    "Método",
    "Densidad_Húmeda",
    "Humedad",
    "Densidad_Seca",
    "DM_Proctor",
    "%Compactación",
    "Observaciones",
    "Creado_En",
]

# -----------------------------
# HELPERS
# -----------------------------
def safe_write_excel(df: pd.DataFrame, path: str) -> None:
    """Escritura atómica para evitar corrupción / cortes en Cloud."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    try:
        with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=SHEET_NAME)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
            for c in COLS:
                if c not in df.columns:
                    df[c] = None
            df = df[COLS]
            return df
        except Exception:
            # En demo: si el archivo está malo, partimos limpio
            return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)


def parse_float(x, field_name: str) -> float:
    try:
        s = str(x).strip().replace(",", ".")
        if s == "":
            raise ValueError("vacío")
        return float(s)
    except Exception:
        st.error(f"⚠️ **{field_name}** debe ser numérico (ej: 2.015).")
        st.stop()


def densidad_seca(dens_humeda: float, humedad_pct: float) -> float:
    w = humedad_pct / 100.0
    return dens_humeda / (1.0 + w)


def compactacion_pct(dens_seca: float, dm_proctor: float) -> float:
    return (dens_seca / dm_proctor) * 100.0


# -----------------------------
# SESSION STATE (RESET SEGURO)
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = load_data()

if "FORM_VER" not in st.session_state:
    st.session_state.FORM_VER = 1

def reset_form_hard():
    # ✅ Reset seguro en Cloud: NO toca keys ya creadas
    st.session_state.FORM_VER += 1


# -----------------------------
# UI
# -----------------------------
st.title("Q-INTEGRITY | Densidades – DEMO WEB")
st.caption("Versión demo estable para Streamlit Cloud: guarda Método + no revienta al limpiar/guardar.")

left, right = st.columns([1.05, 1.6], gap="large")

# =========================================================
# FORM INGRESO
# =========================================================
with left:
    st.subheader("Ingreso de Registro")

    with st.form(key=f"FORM_INGRESO_{st.session_state.FORM_VER}", clear_on_submit=False):
        fecha = st.date_input(
            "Fecha",
            value=date.today(),
            key=f"fecha_{st.session_state.FORM_VER}",
        )
        proyecto = st.text_input(
            "Proyecto",
            value="",
            key=f"proyecto_{st.session_state.FORM_VER}",
        )
        frente = st.text_input(
            "Frente / Detalle",
            value="",
            key=f"frente_{st.session_state.FORM_VER}",
        )

        # ✅ FIX: Método en web (sin "— Seleccionar —" como opción)
        metodo = st.selectbox(
            "Método",
            options=METODOS,
            index=None,
            placeholder="Seleccionar método",
            key=f"metodo_{st.session_state.FORM_VER}",
        )

        c1, c2 = st.columns(2)
        with c1:
            dens_humeda_in = st.text_input(
                "Densidad Húmeda",
                value="",
                key=f"dens_humeda_{st.session_state.FORM_VER}",
                placeholder="Ej: 2.015",
            )
        with c2:
            humedad_in = st.text_input(
                "Humedad (%)",
                value="",
                key=f"humedad_{st.session_state.FORM_VER}",
                placeholder="Ej: 8.2",
            )

        dm_proctor_in = st.text_input(
            "DM Proctor (Densidad Máx. Seca)",
            value="",
            key=f"dm_proctor_{st.session_state.FORM_VER}",
            placeholder="Ej: 2.120",
        )

        obs = st.text_area(
            "Observaciones",
            value="",
            height=90,
            key=f"obs_{st.session_state.FORM_VER}",
        )

        b1, b2 = st.columns(2)
        guardar = b1.form_submit_button("💾 Guardar", use_container_width=True)
        limpiar = b2.form_submit_button("🧹 Limpiar", use_container_width=True)

    if limpiar:
        reset_form_hard()
        st.rerun()

    if guardar:
        # Validaciones duras
        if not str(proyecto).strip():
            st.error("⚠️ Debe ingresar **Proyecto**.")
            st.stop()

        if metodo is None:
            st.error("⚠️ Debe seleccionar un **Método**.")
            st.stop()

        dens_humeda = parse_float(dens_humeda_in, "Densidad Húmeda")
        humedad = parse_float(humedad_in, "Humedad (%)")
        dm_proctor = parse_float(dm_proctor_in, "DM Proctor")

        d_seca = densidad_seca(dens_humeda, humedad)
        comp = compactacion_pct(d_seca, dm_proctor)

        now = datetime.now()
        id_reg = f"DEN-{now.strftime('%Y%m%d-%H%M%S')}"

        nuevo = {
            "ID_Registro": id_reg,
            "Fecha": pd.to_datetime(fecha),
            "Proyecto": str(proyecto).strip(),
            "Frente": str(frente).strip(),
            "Método": str(metodo).strip(),
            "Densidad_Húmeda": dens_humeda,
            "Humedad": humedad,
            "Densidad_Seca": float(d_seca),
            "DM_Proctor": dm_proctor,
            "%Compactación": float(comp),
            "Observaciones": str(obs).strip(),
            "Creado_En": now,
        }

        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nuevo])], ignore_index=True)
        safe_write_excel(st.session_state.df, DATA_FILE)

        st.success("✅ Registro guardado completo (incluye Método).")
        reset_form_hard()
        st.rerun()

    st.divider()
    st.subheader("Descarga rápida (DEMO)")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            st.download_button(
                "⬇️ Descargar Excel BD",
                data=f,
                file_name="qintegrity_densidades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.info("Aún no existe el Excel. Guarda el primer registro y aparecerá.")

# =========================================================
# TABLA / KPIs / ELIMINAR
# =========================================================
with right:
    st.subheader("Registros Guardados")

    df = st.session_state.df.copy()

    if df.empty:
        st.info("Aún no hay registros.")
    else:
        # KPIs
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total registros", f"{len(df):,}".replace(",", "."))
        with k2:
            if df["%Compactación"].notna().any():
                st.metric("Prom. %Compactación", f"{df['%Compactación'].mean():.2f}")
            else:
                st.metric("Prom. %Compactación", "—")
        with k3:
            st.metric("Último ID", str(df["ID_Registro"].iloc[-1]))

        # Filtros
        f1, f2, f3 = st.columns([1.2, 1.0, 1.0])
        with f1:
            filtro_proy = st.text_input("Filtrar Proyecto (contiene)", value="")
        with f2:
            filtro_met = st.selectbox(
                "Filtrar Método",
                options=["(Todos)"] + sorted(df["Método"].dropna().astype(str).unique().tolist()),
                index=0,
            )
        with f3:
            orden = st.selectbox("Orden", options=["Más recientes", "Más antiguos"], index=0)

        view = df.copy()
        if filtro_proy.strip():
            view = view[view["Proyecto"].astype(str).str.contains(filtro_proy.strip(), case=False, na=False)]
        if filtro_met != "(Todos)":
            view = view[view["Método"].astype(str) == filtro_met]

        asc = True if orden == "Más antiguos" else False
        view = view.sort_values("Creado_En", ascending=asc)

        st.dataframe(view, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Eliminar registro (por ID_Registro)")

        ids = view["ID_Registro"].astype(str).tolist()
        if not ids:
            st.warning("No hay registros en el filtrado para eliminar.")
        else:
            id_borrar = st.selectbox("Selecciona ID", options=ids, index=0)
            if st.button("🗑️ Eliminar seleccionado", use_container_width=True):
                st.session_state.df = st.session_state.df[
                    st.session_state.df["ID_Registro"].astype(str) != str(id_borrar)
                ].reset_index(drop=True)
                safe_write_excel(st.session_state.df, DATA_FILE)
                st.success(f"✅ Eliminado: {id_borrar}")
                st.rerun()

st.caption("DEMO WEB estable: si esto corre, el demo pasa. Luego integramos con tu módulo real.")
