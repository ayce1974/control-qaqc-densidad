# =========================================================
# Q-INTEGRITY – DENSIDADES (WEB DEMO)
# APP COMPLETA – FIX DEFINITIVO CAMPO METODO
# =========================================================

import os
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Q-INTEGRITY | Densidades",
    layout="wide"
)

DATA_FILE = "qintegrity_densidades.xlsx"

METODOS = [
    "Densímetro Nuclear",
    "Cono de Arena",
    "Membrana de Goma",
    "Reemplazo",
]

COLUMNAS = [
    "RowKey",
    "Fecha",
    "Operador",
    "Metodo",
    "Observaciones",
    "Creado_El",
]

# ---------------------------------------------------------
# CARGA / GUARDA DATOS
# ---------------------------------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.read_excel(DATA_FILE)

    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = ""

    df["Metodo"] = df["Metodo"].fillna("").astype(str)
    df["Operador"] = df["Operador"].fillna("").astype(str)
    df["Observaciones"] = df["Observaciones"].fillna("").astype(str)

    return df[COLUMNAS]


def save_data(df):
    df.to_excel(DATA_FILE, index=False)


# ---------------------------------------------------------
# SESSION STATE (UNICO, SIN DUPLICADOS)
# ---------------------------------------------------------
if "operador" not in st.session_state:
    st.session_state.operador = ""

if "metodo" not in st.session_state:
    st.session_state.metodo = METODOS[0]

if "obs" not in st.session_state:
    st.session_state.obs = ""


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.title("Q-INTEGRITY – Densidades (Demo Web)")

df = load_data()

with st.form("form_ingreso", clear_on_submit=False):

    col1, col2 = st.columns(2)

    with col1:
        operador = st.text_input(
            "Operador (DIGITAR)",
            key="operador"
        )

    with col2:
        metodo = st.selectbox(
            "Método",
            METODOS,
            index=METODOS.index(st.session_state.metodo)
            if st.session_state.metodo in METODOS else 0,
            key="metodo"
        )

    obs = st.text_area(
        "Observaciones",
        key="obs"
    )

    guardar = st.form_submit_button("GUARDAR REGISTRO")


# ---------------------------------------------------------
# GUARDAR
# ---------------------------------------------------------
if guardar:

    if operador.strip() == "":
        st.error("Operador obligatorio")
        st.stop()

    if metodo.strip() == "":
        st.error("Método obligatorio")
        st.stop()

    nuevo = {
        "RowKey": str(uuid.uuid4()),
        "Fecha": date.today(),
        "Operador": operador.strip(),
        "Metodo": metodo.strip(),
        "Observaciones": obs.strip(),
        "Creado_El": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
    save_data(df)

    st.session_state.operador = ""
    st.session_state.obs = ""

    st.success("Registro guardado correctamente")


# ---------------------------------------------------------
# TABLA
# ---------------------------------------------------------
st.subheader("Registros guardados")
st.dataframe(df, use_container_width=True)
