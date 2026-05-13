import streamlit as st
import pandas as pd
import pdfplumber
import json
import io
import re
from datetime import date, datetime
import google.generativeai as genai
from dotenv import load_dotenv
import os

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestor Ambiental IA",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Estilos CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

:root {
    --verde: #1a7a4a;
    --verde-claro: #2ecc71;
    --verde-oscuro: #0d3d25;
    --crema: #f5f0e8;
    --gris: #6b7280;
    --rojo: #e74c3c;
    --amarillo: #f39c12;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: #f0f4f0 !important;
    font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stHeader"] { background: transparent !important; }

.header-banner {
    background: linear-gradient(135deg, #0d3d25 0%, #1a7a4a 60%, #2ecc71 100%);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.header-banner::before {
    content: "♻";
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 8rem;
    opacity: 0.08;
    line-height: 1;
}
.header-banner h1 {
    font-family: 'IBM Plex Mono', monospace;
    color: #fff;
    font-size: 1.9rem;
    font-weight: 600;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.header-banner p {
    color: rgba(255,255,255,0.75);
    margin: 0;
    font-size: 0.95rem;
    font-weight: 300;
}
.header-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    color: #fff;
    margin-bottom: 0.8rem;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.card {
    background: #fff;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 1.2rem;
    border: 1px solid #e8f0eb;
}
.card-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--verde);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 1rem;
    font-weight: 600;
}

.stButton > button {
    background: linear-gradient(135deg, #1a7a4a, #2ecc71) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(26,122,74,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26,122,74,0.4) !important;
}

.status-ok {
    background: #e8f8ef;
    border-left: 4px solid #2ecc71;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.4rem 0;
    font-size: 0.88rem;
    color: #0d3d25;
}
.status-error {
    background: #fdf0ee;
    border-left: 4px solid #e74c3c;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.4rem 0;
    font-size: 0.88rem;
    color: #7b1a12;
}

.metric-box {
    background: linear-gradient(135deg, #0d3d25, #1a7a4a);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: white;
    text-align: center;
}
.metric-box .num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
}
.metric-box .label {
    font-size: 0.75rem;
    opacity: 0.75;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
}

.footer {
    text-align: center;
    padding: 2rem;
    color: var(--gris);
    font-size: 0.8rem;
    border-top: 1px solid #e0e8e3;
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Cargar API Key ───────────────────────────────────────────────────────────
load_dotenv()

def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
    return key

# ── Extracción de texto del PDF ──────────────────────────────────────────────
def extract_text_from_pdf(pdf_file) -> str:
    text_pages = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    text_pages.append(f"--- PÁGINA {i+1} ---\n{t}")
    except Exception as e:
        raise RuntimeError(f"No se pudo leer el PDF: {e}")
    if not text_pages:
        raise RuntimeError("El PDF no contiene texto extraíble (puede ser imagen escaneada sin OCR).")
    return "\n\n".join(text_pages)

# ── Prompt de extracción ─────────────────────────────────────────────────────
PROMPT_EXTRACCION = """Eres un experto en normativa ambiental mexicana (SEMARNAT/NOM-055-SEMARNAT-2003).
Se te proporciona el texto extraído de un "Manifiesto de Entrega, Transporte y Recepción de Residuos Peligrosos" de México.

Extrae EXACTAMENTE los siguientes campos y devuelve SOLO un objeto JSON válido (sin backticks, sin texto extra):

{
  "consecutivo": "Número de folio/manifiesto. Busca 'No.', 'Núm.', 'Folio', o secuencia numérica al inicio del documento. Ej: '047912'",
  "nombre_residuo": "Nombre del residuo peligroso de la sección 5. Ej: 'ACEITE Y LUBRICANTE USADO Y GASTADO'",
  "cantidad": "Cantidad y unidad de la sección 5. Ej: '6,000 LTS' o '1.116 TON'. Si hay varias, sepáralas con coma.",
  "cretib": "Características de peligrosidad CRETIB marcadas con X en sección 5. Solo las letras activas. Ej: 'T' o 'C,T' o 'C,R,E,T,I,B'",
  "fecha_salida": "Fecha de la sección 7 (generador), donde dice 'Fecha:'. Formato DD/MM/AAAA.",
  "responsable": "Nombre completo del responsable firmante de la sección 7 (generador). NO incluir transportista ni destinatario.",
  "fase_siguiente": "Nombre y/o razón social del destinatario de la sección 15. Incluir texto entre paréntesis si lo hay. Ej: 'LUBRICANTES JUGUER S.A. DE C.V. (CENTRO DE ACOPIO)'",
  "area_resguardo": "Mismo valor que fase_siguiente (nombre del destino/centro de acopio de sección 15).",
  "transportista_nombre": "Nombre o razón social del transportista, secciones 8-12.",
  "transportista_autorizacion": "Número de autorización SEMARNAT del transportista, sección 9. Formato alfanumérico.",
  "destinatario_nombre": "Nombre o razón social del destinatario, secciones 15-17.",
  "destinatario_autorizacion": "Número de autorización SEMARNAT del destinatario, sección 16."
}

REGLAS IMPORTANTES:
- Si un campo no existe en el documento, usa exactamente: "No especificado"
- Para CRETIB: solo las letras con marca/tache/X. Ejemplo: si solo T tiene X, responde "T"
- Para fecha_salida: busca en la zona del generador (parte superior del manifiesto), no la del transportista ni destinatario
- El responsable es SOLO el de la sección 7 del generador
- NO inventes datos. Si no está claro, usa "No especificado"
- Responde ÚNICAMENTE el JSON, sin ningún texto adicional

TEXTO DEL MANIFIESTO:
{texto}
"""

# ── Llamada a Gemini ─────────────────────────────────────────────────────────
def extraer_datos_gemini(texto: str, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = PROMPT_EXTRACCION.replace("{texto}", texto[:12000])  # límite seguro de tokens

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=1500,
        )
    )

    raw = response.text.strip()
    # Limpiar posibles backticks si el modelo los añade
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"La IA devolvió JSON inválido: {e}\n\nRespuesta recibida:\n{raw[:500]}")

    # Garantizar que todos los campos existan
    campos = [
        "consecutivo", "nombre_residuo", "cantidad", "cretib",
        "fecha_salida", "responsable", "fase_siguiente", "area_resguardo",
        "transportista_nombre", "transportista_autorizacion",
        "destinatario_nombre", "destinatario_autorizacion"
    ]
    for c in campos:
        if c not in data or not data[c]:
            data[c] = "No especificado"

    return data

# ── Generar Excel ────────────────────────────────────────────────────────────
def generar_excel(registros: list, fecha_ingreso: str) -> bytes:
    filas = []
    for r in registros:
        filas.append({
            "Consecutivo (No. Manifiesto)": r.get("consecutivo", ""),
            "Nombre del Residuo Peligroso": r.get("nombre_residuo", ""),
            "Cantidad Generada": r.get("cantidad", ""),
            "Características CRETIB": r.get("cretib", ""),
            "Fecha de Ingreso al Almacén": fecha_ingreso,
            "Fecha de Salida del Almacén": r.get("fecha_salida", ""),
            "Señalamiento Fase Siguiente": r.get("fase_siguiente", ""),
            "Área de Resguardo / Transferencia": r.get("area_resguardo", ""),
            "Transportista - Nombre/Razón Social": r.get("transportista_nombre", ""),
            "Transportista - No. Autorización SEMARNAT": r.get("transportista_autorizacion", ""),
            "Destinatario - Nombre/Razón Social": r.get("destinatario_nombre", ""),
            "Destinatario - No. Autorización SEMARNAT": r.get("destinatario_autorizacion", ""),
            "Nombre del Responsable": r.get("responsable", ""),
        })

    df = pd.DataFrame(filas)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Bitácora RP")

        ws = writer.sheets["Bitácora RP"]

        from openpyxl.styles import (
            PatternFill, Font, Alignment, Border, Side
        )

        # Colores
        verde_header = PatternFill("solid", fgColor="0D5C2E")
        verde_sub    = PatternFill("solid", fgColor="1A7A4A")
        crema_par    = PatternFill("solid", fgColor="F5FAF7")
        blanco       = PatternFill("solid", fgColor="FFFFFF")

        borde_fino = Border(
            left=Side(style="thin", color="C8DDD0"),
            right=Side(style="thin", color="C8DDD0"),
            top=Side(style="thin", color="C8DDD0"),
            bottom=Side(style="thin", color="C8DDD0"),
        )

        # Fila de encabezado institucional
        ws.insert_rows(1)
        ws.merge_cells("A1:M1")
        titulo_cell = ws["A1"]
        titulo_cell.value = "BITÁCORA DE RESIDUOS PELIGROSOS — FORMATO SEMARNAT"
        titulo_cell.font = Font(bold=True, color="FFFFFF", size=13, name="Calibri")
        titulo_cell.fill = verde_header
        titulo_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        # Fila de fecha generación
        ws.insert_rows(2)
        ws.merge_cells("A2:M2")
        fecha_cell = ws["A2"]
        fecha_cell.value = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}   |   Fecha de ingreso al almacén aplicada: {fecha_ingreso}"
        fecha_cell.font = Font(italic=True, color="FFFFFF", size=9, name="Calibri")
        fecha_cell.fill = verde_sub
        fecha_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 18

        # Encabezados de columna (ahora fila 3)
        header_row = 3
        for cell in ws[header_row]:
            cell.font = Font(bold=True, color="FFFFFF", size=9, name="Calibri")
            cell.fill = verde_header
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = borde_fino
        ws.row_dimensions[header_row].height = 36

        # Datos (filas 4 en adelante)
        for row_idx, row in enumerate(ws.iter_rows(min_row=header_row+1, max_row=ws.max_row), start=0):
            fill = crema_par if row_idx % 2 == 0 else blanco
            for cell in row:
                cell.fill = fill
                cell.border = borde_fino
                cell.font = Font(size=9, name="Calibri")
                cell.alignment = Alignment(vertical="center", wrap_text=True)

        # Anchos de columna
        anchos = [18, 35, 15, 14, 20, 20, 35, 30, 35, 28, 35, 28, 28]
        for i, ancho in enumerate(anchos, start=1):
            col_letter = ws.cell(row=1, column=i).column_letter
            ws.column_dimensions[col_letter].width = ancho

        # Congelar encabezados
        ws.freeze_panes = ws.cell(row=header_row+1, column=1)

    output.seek(0)
    return output.read()

# ══════════════════════════════════════════════════════════════════════════════
# INTERFAZ PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="header-banner">
    <div class="header-badge">SEMARNAT · NOM-055</div>
    <h1>Gestor Ambiental IA — Bitácora de Residuos Peligrosos</h1>
    <p>Extracción automática de datos desde manifiestos de entrega, transporte y recepción · Powered by Gemini AI</p>
</div>
""", unsafe_allow_html=True)

# ── Configuración de API Key ─────────────────────────────────────────────────
with st.expander("⚙️ Configuración de API Key (Gemini)", expanded=False):
    st.markdown("""
    <div class="card-title">GEMINI API KEY</div>
    """, unsafe_allow_html=True)
    api_key_input = st.text_input(
        "Ingresa tu API Key de Google Gemini:",
        type="password",
        placeholder="AIza...",
        help="Obtén tu key gratis en https://aistudio.google.com/app/apikey"
    )
    st.caption("También puedes definirla en un archivo `.env` como `GEMINI_API_KEY=...` o en `st.secrets`.")

api_key = api_key_input.strip() if api_key_input else get_api_key()

# ── Subida de PDFs ───────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">📄 Subir Manifiestos (PDF)</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Selecciona uno o varios manifiestos en PDF:",
    type=["pdf"],
    accept_multiple_files=True,
    help="Puedes subir múltiples archivos a la vez. Se procesarán secuencialmente.",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} archivo(s) cargado(s):**")
    for f in uploaded_files:
        st.markdown(f'<div class="status-ok">📄 {f.name} — {f.size/1024:.1f} KB</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Botón procesar ───────────────────────────────────────────────────────────
col_btn, col_space = st.columns([1, 3])
with col_btn:
    procesar = st.button("🔍 Procesar manifiestos", use_container_width=True)

if procesar:
    if not uploaded_files:
        st.warning("⚠️ Por favor sube al menos un archivo PDF.")
    elif not api_key:
        st.error("❌ Se requiere una API Key de Gemini. Configúrala en la sección de arriba.")
    else:
        registros = []
        errores = []

        progress_bar = st.progress(0, text="Iniciando procesamiento...")
        log_container = st.container()

        for i, pdf_file in enumerate(uploaded_files):
            pct = int((i / len(uploaded_files)) * 100)
            progress_bar.progress(pct, text=f"Procesando: {pdf_file.name} ({i+1}/{len(uploaded_files)})")

            with log_container:
                with st.spinner(f"Extrayendo datos con IA... → {pdf_file.name}"):
                    try:
                        texto = extract_text_from_pdf(pdf_file)
                        datos = extraer_datos_gemini(texto, api_key)
                        datos["_archivo"] = pdf_file.name
                        registros.append(datos)
                        st.markdown(
                            f'<div class="status-ok">✅ <strong>{pdf_file.name}</strong> — '
                            f'Manifiesto #{datos["consecutivo"]} extraído correctamente.</div>',
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        errores.append((pdf_file.name, str(e)))
                        st.markdown(
                            f'<div class="status-error">❌ <strong>{pdf_file.name}</strong> — Error: {str(e)[:200]}</div>',
                            unsafe_allow_html=True
                        )

        progress_bar.progress(100, text="✅ Procesamiento completado.")
        st.session_state["registros"] = registros
        st.session_state["errores"] = errores

# ── Mostrar resultados ───────────────────────────────────────────────────────
if "registros" in st.session_state and st.session_state["registros"]:
    registros = st.session_state["registros"]

    st.markdown("---")

    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="num">{len(registros)}</div>
            <div class="label">Manifiestos procesados</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        errores_count = len(st.session_state.get("errores", []))
        st.markdown(f"""
        <div class="metric-box">
            <div class="num">{errores_count}</div>
            <div class="label">Errores</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="num">{len(registros) - errores_count}</div>
            <div class="label">Exitosos</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabla de resultados
    st.markdown('<div class="card"><div class="card-title">📋 Datos extraídos (vista previa)</div>', unsafe_allow_html=True)

    df_preview = pd.DataFrame([{
        "# Manifiesto": r["consecutivo"],
        "Residuo": r["nombre_residuo"],
        "Cantidad": r["cantidad"],
        "CRETIB": r["cretib"],
        "Fecha Salida": r["fecha_salida"],
        "Transportista": r["transportista_nombre"],
        "Destinatario": r["destinatario_nombre"],
        "Responsable": r["responsable"],
        "Archivo": r["_archivo"],
    } for r in registros])

    st.dataframe(df_preview, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Fecha de ingreso y generación de Excel ───────────────────────────────
    st.markdown('<div class="card"><div class="card-title">📅 Fecha de ingreso al almacén y descarga</div>', unsafe_allow_html=True)

    col_fecha, col_gen = st.columns([1, 2])

    with col_fecha:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso al almacén (se aplicará a todos los registros):",
            value=date.today(),
            format="DD/MM/YYYY",
        )
        fecha_str = fecha_ingreso.strftime("%d/%m/%Y")

    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 Generar bitácora Excel", use_container_width=True):
            with st.spinner("Generando archivo Excel con formato SEMARNAT..."):
                try:
                    excel_bytes = generar_excel(registros, fecha_str)
                    nombre_archivo = f"Bitacora_RP_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    st.success(f"✅ Bitácora generada con {len(registros)} registro(s).")
                    st.download_button(
                        label="⬇️ Descargar Bitácora Excel",
                        data=excel_bytes,
                        file_name=nombre_archivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Error al generar Excel: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Edición manual de registros ──────────────────────────────────────────
    with st.expander("✏️ Editar / corregir registros manualmente (opcional)"):
        st.caption("Puedes corregir cualquier dato antes de generar el Excel. Los cambios se aplican en tiempo real.")
        campos_editables = [
            "consecutivo", "nombre_residuo", "cantidad", "cretib",
            "fecha_salida", "fase_siguiente", "area_resguardo",
            "transportista_nombre", "transportista_autorizacion",
            "destinatario_nombre", "destinatario_autorizacion", "responsable"
        ]
        for idx, reg in enumerate(registros):
            with st.container():
                st.markdown(f"**📄 Manifiesto #{reg['consecutivo']} — {reg['_archivo']}**")
                cols = st.columns(3)
                for i, campo in enumerate(campos_editables):
                    with cols[i % 3]:
                        nuevo_val = st.text_input(
                            campo.replace("_", " ").title(),
                            value=reg[campo],
                            key=f"{idx}_{campo}"
                        )
                        st.session_state["registros"][idx][campo] = nuevo_val
                st.markdown("---")

elif "registros" in st.session_state and not st.session_state["registros"]:
    st.warning("No se pudieron extraer datos de ningún manifiesto. Revisa los errores mostrados arriba.")

# ── Instrucciones de uso ─────────────────────────────────────────────────────
with st.expander("ℹ️ Instrucciones de uso"):
    st.markdown("""
    **Pasos para generar tu bitácora:**

    1. **Configura tu API Key** de Google Gemini (gratis en [aistudio.google.com](https://aistudio.google.com/app/apikey))
    2. **Sube los PDFs** de tus manifiestos de entrega, transporte y recepción de residuos peligrosos
    3. **Presiona "Procesar manifiestos"** — la IA extrae automáticamente todos los campos
    4. **Verifica la tabla** de datos extraídos y corrige si es necesario (sección editable)
    5. **Selecciona la fecha de ingreso** al almacén (este dato no viene en el manifiesto)
    6. **Genera y descarga** el Excel con formato SEMARNAT listo para usar

    **Campos que se extraen automáticamente del manifiesto:**
    - Número de folio/consecutivo
    - Nombre del residuo peligroso (sección 5)
    - Cantidad y unidad (sección 5)
    - Características CRETIB (sección 5)
    - Fecha de salida del almacén (sección 7 — generador)
    - Nombre del responsable (sección 7 — generador)
    - Transportista y número de autorización SEMARNAT (secciones 8-12)
    - Destinatario y número de autorización SEMARNAT (secciones 15-17)
    - Fase siguiente y área de resguardo (sección 15)

    **⚠️ Nota:** Los PDFs deben tener texto seleccionable. PDFs de imagen sin OCR no son compatibles.
    """)

# Footer
st.markdown("""
<div class="footer">
    Gestor Ambiental IA · Bitácora de Residuos Peligrosos · Formato SEMARNAT México<br>
    Datos procesados localmente · La información no se almacena en servidores externos
</div>
""", unsafe_allow_html=True)
