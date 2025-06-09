
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CONTROL QAQC - Densidad In Situ", layout="centered")

st.title("🧱 CONTROL QAQC - Módulo Densidad In Situ")
st.markdown("Registra tus ensayos de compactación de forma ordenada y accesible.")

# Campos del formulario
with st.form("densidad_form"):
    orden_trabajo = st.text_input("Orden de trabajo")
    boleta = st.text_input("N° Boleta de densidad")
    certificado = st.text_input("Certificado N°")
    estado_cert = st.selectbox("Estado certificado", ["DMN-001", "DMN-002", "Otro"])
    tipo_material = st.text_input("Tipo de material")
    metodo = st.selectbox("Método", ["Densímetro Nuclear", "Método de Arena", "Otro"])
    densidad_seca = st.number_input("Densidad Seca (g/cm³)", step=0.01)
    dmcs = st.number_input("D.M.C.S. (g/cm³)", step=0.01)
    porcentaje_dmcs = st.number_input("% D.M.C.S.", step=0.1)
    cumple = st.selectbox("Cumple", ["Sí", "No"])
    observaciones = st.text_area("Observaciones")
    submit = st.form_submit_button("Registrar")

# Simulación de guardado en tabla temporal
if submit:
    st.success("Registro guardado correctamente.")
    st.write({
        "Orden": orden_trabajo,
        "Boleta": boleta,
        "Certificado": certificado,
        "Estado": estado_cert,
        "Material": tipo_material,
        "Método": metodo,
        "Densidad Seca": densidad_seca,
        "D.M.C.S.": dmcs,
        "% D.M.C.S.": porcentaje_dmcs,
        "Cumple": cumple,
        "Observaciones": observaciones,
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
