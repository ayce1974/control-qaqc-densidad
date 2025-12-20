# =========================================================
# Q-INTEGRITY – DENSIDADES (DEMO WEB) ✅
# FIX CRÍTICO: "Método" no se guardaba en Streamlit Cloud
# - Selectbox con index=None + placeholder (sin "— Seleccionar —" como opción)
# - Validación dura: si no hay método, NO guarda
# - Guardado robusto en Excel (carpeta /data + escritura atómica)
# - Tabla + eliminar por ID
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
# RUTAS SEGURAS (WEB)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, "qintegrity_densidades.xlsx")

# -----------------------------
# HELPERS
# -----------------------------
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

def safe_write_excel(df: pd.DataFrame, path: str) -> None:
    """Escritura atómica para evitar excel corrupto / cortes."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    try:
        with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="BD")
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
            df = pd.read_excel(DATA_FILE, sheet_name="BD", engine="openpyxl")
            for c in COLS:
                if c not in df.columns:
                    df[c] = None
            df = df[COLS]
            return df
        except Exception:
            # Si el archivo existe pero está malo, partimos limpio para no morir en demo
            return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)

def calc_densidad_seca(dens_humeda: float, humedad_pct: float) -> float:
    # D_seca = D_humeda / (1 + w)
    w = humedad_pct / 100.0
    return dens_humeda / (1.0 + w)

def calc_compactacion(dens_seca: float, dm_proctor: float) -> float:
    return (dens_seca / dm_proctor) * 100.0

def must_float(x, field_name: str) -> float:
    try:
        v = float(str(x).replace(",", "."))
        return v
    except Exception:
        st.error(f"⚠️ Campo inválido: **{field_name}**. Debe ser numérico.")
        st.stop()

# -----------------------------
# SESSION STATE
# -----------------------------
if "df" not in st.session_state:
    st.session_state.df = load_data()

if "form_key" not in st.session_state:
    st.session_state.form_key = 1

def reset_form():
    st.session_state.form_key += 1

# -----------------------------
# HEADER
# -----------------------------
st.title("Q-INTEGRITY | Densidades – DEMO WEB")
st.caption("Fix aplicado: el campo **Método** ahora se guarda correctamente en la web.")

# -----------------------------
# LAYOUT
# -----------------------------
left, right = st.columns([1.05, 1.6], gap="large")

# =============================
# FORMULARIO INGRESO
# =============================
with left:
    st.subheader("Ingreso de Registro")

    with st.form(key=f"form_ingreso_{st.session_state.form_key}", clear_on_submit=False):
        fecha = st.date_input("Fecha", value=date.today())
        proyecto = st.text_input("Proyecto", value="")
        frente = st.text_input("Frente / Detalle", value="")

        # ✅ FIX REAL (NO USAR "— Seleccionar —" COMO OPCIÓN)
        METODOS = [
            "Cono de Arena",
            "Densímetro Nuclear",
            "Método del Globo",
            "Otro",
        ]
        metodo = st.selectbox(
            "Método",
            options=METODOS,
            index=None,  # 🔥 CLAVE EN WEB
            placeholder="Seleccionar método",
        )

        c1, c2 = st.columns(2)
        with c1:
            dens_humeda_in = st.text_input("Densidad Húmeda", value="")
        with c2:
            humedad_in = st.text_input("Humedad (%)", value="")

        dm_proctor_in = st.text_input("DM Proctor (Densidad Máx. Seca)", value="")
        obs = st.text_area("Observaciones", value="", height=90)

        b1, b2 = st.columns(2)
        submit = b1.form_submit_button("💾 Guardar", use_container_width=True)
        limpiar = b2.form_submit_button("🧹 Limpiar", use_container_width=True)

    if limpiar:
        reset_form()
        st.rerun()

    if submit:
        # VALIDACIONES DURAS
        if not proyecto.strip():
            st.error("⚠️ Debe ingresar **Proyecto**.")
            st.stop()

        if metodo is None:
            st.error("⚠️ Debe seleccionar un **Método** antes de guardar.")
            st.stop()

        dens_humeda = must_float(dens_humeda_in, "Densidad Húmeda")
        humedad = must_float(humedad_in, "Humedad (%)")
        dm_proctor = must_float(dm_proctor_in, "DM Proctor")

        dens_seca = calc_densidad_seca(dens_humeda, humedad)
        compact = calc_compactacion(dens_seca, dm_proctor)

        # ID visible para demo
        now = datetime.now()
        id_reg = f"DEN-{now.strftime('%Y%m%d-%H%M%S')}"

        nuevo = {
            "ID_Registro": id_reg,
            "Fecha": pd.to_datetime(fecha),
            "Proyecto": proyecto.strip(),
            "Frente": frente.strip(),
            "Método": metodo,  # ✅ SE GUARDA BIEN
            "Densidad_Húmeda": dens_humeda,
            "Humedad": humedad,
            "Densidad_Seca": dens_seca,
            "DM_Proctor": dm_proctor,
            "%Compactación": compact,
            "Observaciones": obs.strip(),
            "Creado_En": now,
        }

        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([nuevo])], ignore_index=True)

        # Guardar a Excel
        safe_write_excel(st.session_state.df, DATA_FILE)

        st.success("✅ Registro guardado completo (incluye Método).")
        reset_form()
        st.rerun()

    st.divider()
    st.subheader("Exportación (DEMO)")
    st.write("Excel se guarda automáticamente en `data/qintegrity_densidades.xlsx`.")

# =============================
# TABLA + ELIMINAR
# =============================
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
            st.metric("Prom. %Compactación", f"{df['%Compactación'].dropna().mean():.2f}" if df["%Compactación"].notna().any() else "—")
        with k3:
            st.metric("Último registro", str(df["ID_Registro"].iloc[-1]))

        # Filtros rápidos
        f1, f2 = st.columns(2)
        with f1:
            filtro_proy = st.text_input("Filtrar Proyecto (contiene)", value="")
        with f2:
            filtro_metodo = st.selectbox(
                "Filtrar Método",
                options=["(Todos)"] + sorted(df["Método"].dropna().astype(str).unique().tolist()),
                index=0,
            )

        view = df.copy()
        if filtro_proy.strip():
            view = view[view["Proyecto"].astype(str).str.contains(filtro_proy.strip(), case=False, na=False)]
        if filtro_metodo != "(Todos)":
            view = view[view["Método"].astype(str) == filtro_metodo]

        st.dataframe(
            view.sort_values("Creado_En", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("Eliminar registro (por ID_Registro)")

        ids = view["ID_Registro"].astype(str).tolist()
        if not ids:
            st.warning("No hay registros en el filtrado para eliminar.")
        else:
            id_borrar = st.selectbox("Selecciona ID a eliminar", options=ids, index=0)
            if st.button("🗑️ Eliminar seleccionado", use_container_width=True):
                st.session_state.df = st.session_state.df[st.session_state.df["ID_Registro"].astype(str) != str(id_borrar)].reset_index(drop=True)
                safe_write_excel(st.session_state.df, DATA_FILE)
                st.success(f"✅ Eliminado: {id_borrar}")
                st.rerun()

    st.divider()
    st.subheader("Descargar Excel (para demo)")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            st.download_button(
                "⬇️ Descargar qintegrity_densidades.xlsx",
                data=f,
                file_name="qintegrity_densidades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.warning("Aún no existe el Excel. Guarda el primer registro y aparecerá.")
