import streamlit as st
import gspread
import json
import base64
import io
import urllib.parse
from datetime import datetime
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ════════════════════════════════════════════════════════════
# CONFIGURACIÓN E INICIALIZACIÓN
# ════════════════════════════════════════════════════════════
st.set_page_config(page_title="OPTIMARGE EIRL", page_icon="📝", layout="centered")

def get_sheet():
    # En lugar de escribir los datos aquí, los leemos de forma segura desde Streamlit
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Aseguramos que los saltos de línea de la clave privada se procesen bien
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(
        creds_dict, 
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds).open("OPTIMARGE").sheet1
# ════════════════════════════════════════════════════════════
# GENERADOR DE NOTA DE VENTA EN PDF
# ════════════════════════════════════════════════════════════
def generar_nota_venta_pdf(fecha, tipo_doc, num_doc, placa, servicio, monto, numero_nv="001-00001"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "OPTIMARGE E.I.R.L.")
    c.setFont("Helvetica", 9)
    c.drawString(50, 785, "Calle Los Libertadores 320, San Isidro")
    c.drawString(50, 770, "RUC: 20615871355")

    c.rect(400, 750, 150, 60)
    c.setFillColor(colors.black)
    c.rect(400, 790, 150, 20, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(475, 796, "NOTA DE VENTA")
    c.setFillColor(colors.black)
    c.line(400, 770, 550, 770)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(475, 778, "R.U.C. 20615871355")
    c.drawCentredString(475, 755, numero_nv)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(50, 720, "DATOS DE LA OPERACIÓN")
    c.rect(50, 660, 500, 55, fill=0)
    c.setFont("Helvetica", 8)
    c.drawString(60, 700, f"Fecha: {fecha}")
    c.drawString(60, 690, "Empleado: OPTIMARGE PERU")
    c.drawString(60, 680, f"Placa: {placa}")
    c.drawString(60, 670, "Correo: optimargeperu@gmail.com")

    c.setFillColor(colors.lightgrey)
    c.rect(50, 630, 500, 20, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.line(100, 630, 100, 555)
    c.line(400, 630, 400, 555)
    c.line(480, 630, 480, 555)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(60, 637, "Item")
    c.drawString(150, 637, "Descripción")
    c.drawString(410, 637, "V. Unitario")
    c.drawString(490, 637, "Importe")
    c.rect(50, 555, 500, 75, fill=0, stroke=1)
    c.setFont("Helvetica", 9)
    c.drawString(60, 605, "1")
    c.drawString(110, 605, servicio)
    c.drawString(410, 605, f"S/ {monto:,.2f}")
    c.drawRightString(540, 605, f"S/ {monto:,.2f}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(370, 535, "IMPORTE A PAGAR (sin IGV):")
    c.drawString(530, 535, f"S/ {monto:,.2f}")

    c.save()
    buffer.seek(0)
    return buffer.read()

# ════════════════════════════════════════════════════════════
# PANEL WHATSAPP — solo abre chat, PDF se descarga con Streamlit
# ════════════════════════════════════════════════════════════
def panel_whatsapp_solo_chat(mensaje: str, numero_preingresado: str = ""):
    # Limpiar número si ya viene del formulario
    num_limpio = numero_preingresado.strip().replace("+", "").replace("-", "").replace(" ", "")

    msg_js = (mensaje
              .replace("\\", "\\\\")
              .replace("`", "\\`")
              .replace("$", "\\$"))

    html = f"""
    <style>
      .wa-panel {{
        background: #f0fdf4;
        border: 1.5px solid #22c55e;
        border-radius: 12px;
        padding: 18px 20px;
        font-family: sans-serif;
      }}
      .wa-panel h4 {{
        margin: 0 0 12px 0;
        color: #15803d;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 6px;
      }}
      .wa-row {{
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
      }}
      .wa-input {{
        flex: 1;
        min-width: 150px;
        padding: 10px 14px;
        border: 1.5px solid #86efac;
        border-radius: 8px;
        font-size: 15px;
        outline: none;
      }}
      .wa-input:focus {{ border-color: #16a34a; }}
      .wa-input::placeholder {{ color: #9ca3af; font-size: 13px; }}
      .wa-btn {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: #25D366;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 18px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        white-space: nowrap;
      }}
      .wa-btn:hover {{ background: #1db954; }}
      #wa-status {{
        margin-top: 8px;
        font-size: 12px;
        color: #374151;
        min-height: 16px;
      }}
      .wa-hint {{
        font-size: 11px;
        color: #9ca3af;
        margin-top: 6px;
      }}
    </style>

    <div class="wa-panel">
      <h4>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="#25D366">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
          <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.116 1.522 5.847L0 24l6.335-1.498A11.955 11.955 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.373l-.36-.214-3.727.881.916-3.618-.235-.372A9.818 9.818 0 1112 21.818z"/>
        </svg>
        Paso 2 — Abrir chat WhatsApp
      </h4>
      <div class="wa-row">
        <input id="wa-num" class="wa-input" type="tel"
               value="{num_limpio}"
               placeholder="Ej: 987654321" maxlength="15"/>
        <button class="wa-btn" onclick="abrirWA()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="white">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
            <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.116 1.522 5.847L0 24l6.335-1.498A11.955 11.955 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.373l-.36-.214-3.727.881.916-3.618-.235-.372A9.818 9.818 0 1112 21.818z"/>
          </svg>
          Abrir chat WhatsApp
        </button>
      </div>
      <div id="wa-status"></div>
      <div class="wa-hint">💡 Ingresa el número del cliente y haz clic en Abrir chat WhatsApp.</div>
    </div>

    <script>
      const MENSAJE = `{msg_js}`;
      function abrirWA() {{
        const raw    = document.getElementById("wa-num").value.trim();
        const status = document.getElementById("wa-status");
        if (!raw) {{ status.innerHTML = "⚠️ Ingresa el número del cliente."; return; }}
        let numero = raw.replace(/[\\s\\+\\-]/g, "");
        if (/^\\d{{9}}$/.test(numero)) {{
          numero = "51" + numero;
        }} else if (!/^\\d{{10,15}}$/.test(numero)) {{
          status.innerHTML = "⚠️ Número inválido. Usa 9 dígitos peruanos o código internacional.";
          return;
        }}
        const url = "https://wa.me/" + numero + "?text=" + encodeURIComponent(MENSAJE);
        window.open(url, "_blank");
        status.innerHTML = "✅ WhatsApp abierto para <strong>+" + numero + "</strong>. Adjunta el PDF y envía.";
      }}
      document.getElementById("wa-num").addEventListener("keydown", function(e) {{
        if (e.key === "Enter") abrirWA();
      }});
    </script>
    """
    st.components.v1.html(html, height=210)

# ════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ════════════════════════════════════════════════════════════
if "accion"     not in st.session_state: st.session_state.accion     = None
if "idx_editar" not in st.session_state: st.session_state.idx_editar = None
if "form_gen"   not in st.session_state: st.session_state.form_gen   = 0
if "pdf_listo"  not in st.session_state: st.session_state.pdf_listo  = None
if "pdf_meta"   not in st.session_state: st.session_state.pdf_meta   = None

st.title("📝 OPTIMARGE SAC")

# ════════════════════════════════════════════════════════════
# 1. DATOS Y CONEXIÓN
# Columnas Google Sheets:
# A=Timestamp | B=Fecha   | C=Tipo      | D=Doc    | E=Placa
# F=Servicio  | G=PrecioBase | H=IGV    | I=Total  | J=Estado
# K=Origen    | L=NroNV   | M=WhatsApp
# ════════════════════════════════════════════════════════════
sheet       = get_sheet()
todas_filas = sheet.get_all_values()

datos_activos = [(r, i+2) for i, r in enumerate(todas_filas[1:])
                 if len(r) > 9 and r[9] != "ANULADO"]
opciones      = {f"{r[0][1]} | {r[0][3]} | {r[0][5]}": r[1] for r in datos_activos}

# ════════════════════════════════════════════════════════════
# 2. ACCIONES
# ════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)
with col1:
    if st.button("✏️ EDITAR REGISTRO"): st.session_state.accion = "EDITAR"
with col2:
    if st.button("🚫 ANULAR REGISTRO"): st.session_state.accion = "ANULAR"

if st.session_state.accion:
    if not datos_activos:
        st.warning("⚠️ No existen registros activos.")
        if st.button("Cancelar"):
            st.session_state.accion = None
            st.rerun()
    else:
        seleccion = st.selectbox("Selecciona registro a procesar:", list(opciones.keys()), key="selector")
        st.session_state.idx_editar = opciones[seleccion]

        if st.session_state.accion == "ANULAR":
            if st.button("CONFIRMAR ANULACIÓN", type="primary"):
                try:
                    idx_val = int(st.session_state.idx_editar)
                    sheet.update_cell(idx_val, 10, "ANULADO")
                    st.success("✅ Registro marcado como ANULADO.")
                    st.session_state.idx_editar = None
                    st.session_state.accion = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al anular: {e}")

# ════════════════════════════════════════════════════════════
# 3. FORMULARIO
# ════════════════════════════════════════════════════════════
idx   = st.session_state.idx_editar
datos = sheet.row_values(idx) if idx else [None] * 13
gen   = st.session_state.form_gen

# Rellenar hasta 13 columnas para evitar IndexError en registros viejos
while len(datos) < 13:
    datos.append("")

fecha_val = datetime.strptime(datos[1], "%Y-%m-%d") if (idx and datos[1]) else datetime.now()
fecha = st.date_input("Fecha", value=fecha_val, key=f"fecha_{idx}_{gen}")

opciones_doc = ["Boleta", "Factura", "Nota de Venta"]
idx_tipo = 0
if idx and datos[2] in opciones_doc:
    idx_tipo = opciones_doc.index(datos[2])

tipo = st.radio("Tipo de documento:", opciones_doc,
                index=idx_tipo, horizontal=True, key=f"tipo_{idx}_{gen}")

if tipo == "Boleta":
    max_len, label_doc = 8,  "DNI (8 dígitos):"
elif tipo == "Factura":
    max_len, label_doc = 11, "RUC (11 dígitos):"
else:
    max_len, label_doc = 11, "DNI/RUC (Opcional):"

doc = st.text_input(label_doc,
                    value=datos[3] if idx and datos[3] else "",
                    max_chars=max_len, key=f"doc_{idx}_{gen}")

placa = st.text_input("Placa del vehículo:",
                      value=datos[4] if idx and datos[4] else "",
                      key=f"placa_{idx}_{gen}")

lista_base      = ["Lavado Premium", "Lavado Vapor Interior", "Lavado Express"]
lista_servicios = lista_base + ["Otro"]
valor_actual    = datos[5] if idx and datos[5] else "Lavado Premium"
idx_default     = lista_servicios.index(valor_actual) if valor_actual in lista_servicios else 3

serv_sel = st.radio("Tipo de servicio:", lista_servicios,
                    index=idx_default, key=f"serv_{idx}_{gen}")
serv_final = serv_sel
if serv_sel == "Otro":
    serv_final = st.text_input("Escribe el servicio personalizado:",
                               value=valor_actual if valor_actual not in lista_base else "",
                               key=f"serv_otro_{idx}_{gen}")

# ════════════════════════════════════════════════════════════
# 4. CÁLCULOS FINANCIEROS
# ════════════════════════════════════════════════════════════
st.divider()
precio_default  = float(datos[6]) if (idx and datos[6]) else 0.0
monto_base      = st.number_input("Precio Base (S/):", min_value=0.0,
                                  value=precio_default, step=1.0,
                                  key=f"monto_{idx}_{gen}")
igv_calculado   = monto_base * 0.18
total_calculado = monto_base * 1.18

c1, c2, c3 = st.columns(3)
c1.metric("Base",      f"S/ {monto_base:.2f}")
c2.metric("IGV (18%)", f"S/ {igv_calculado:.2f}")
c3.metric("TOTAL",     f"S/ {total_calculado:.2f}")

# ════════════════════════════════════════════════════════════
# 5. REGISTRAR
# Estructura 13 columnas:
# A  B      C     D    E      F         G            H      I       J        K        L      M
# TS Fecha  Tipo  Doc  Placa  Servicio  PrecioBase   IGV    Total   Estado   Origen   NroNV  WhatsApp
# ════════════════════════════════════════════════════════════
numero_wa = ""

st.divider()
if st.button("🚀 REGISTRAR Y PROCESAR", type="primary"):
    if len(doc) >= 8 and serv_final:
        ahora  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_nv = ""

        # Calcular número de NV si aplica
        if tipo == "Nota de Venta":
            total_filas = len(sheet.get_all_values())
            num_nv = f"001-{total_filas:05d}"

        nuevo_registro = [
            ahora,                      # A - Timestamp
            str(fecha),                 # B - Fecha
            tipo,                       # C - Tipo documento
            doc,                        # D - DNI/RUC
            placa,                      # E - Placa
            serv_final,                 # F - Servicio
            f"{monto_base:.2f}",        # G - Precio Base
            f"{igv_calculado:.2f}",     # H - IGV
            f"{total_calculado:.2f}",   # I - Total
            "ACTIVO",                   # J - Estado
            "ORIGINAL",                 # K - Origen
            num_nv,                     # L - N° Nota de Venta
            numero_wa.strip(),          # M - WhatsApp cliente
        ]

        if idx:
            sheet.update(f"A{idx}:M{idx}", [nuevo_registro])
            st.success("✅ Registro actualizado.")
        else:
            sheet.append_row(nuevo_registro)
            st.success("✅ Registro guardado con éxito.")
            st.session_state.form_gen += 1

        if tipo == "Nota de Venta":
            pdf_bytes = generar_nota_venta_pdf(
                str(fecha), tipo, doc, placa, serv_final, monto_base, num_nv
            )
            st.session_state.pdf_listo = pdf_bytes
            st.session_state.pdf_meta  = {
                "nombre_archivo": f"NotaVenta_{doc}_{num_nv}.pdf",
                "numero_nv":      num_nv,
                "doc":            doc,
                "numero_wa":      numero_wa.strip(),
                "mensaje_wa": (
                    f"Hola! Le compartimos su Nota de Venta de OPTIMARGE E.I.R.L.\n\n"
                    f"📋 N°: {num_nv}\n"
                    f"📅 Fecha: {fecha}\n"
                    f"🚗 Placa: {placa}\n"
                    f"🔧 Servicio: {serv_final}\n"
                    f"💰 Importe a pagar: S/ {monto_base:,.2f} (sin IGV)\n\n"
                    f"Gracias por su preferencia. ¡Hasta pronto! 🙌"
                ),
            }

        st.session_state.idx_editar = None
        st.session_state.accion     = None
        st.rerun()
    else:
        st.error(f"❌ Error: El {tipo} requiere {max_len} dígitos y el servicio es obligatorio.")

# ════════════════════════════════════════════════════════════
# 6. DESCARGA PDF + PANEL WHATSAPP
# Paso 1 → descarga PDF (botón nativo Streamlit)
# Paso 2 → número precargado del formulario, abre WhatsApp
# ════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════
# 7. CAMPO WHATSAPP — aparece después de registrar, solo Nota de Venta
# ════════════════════════════════════════════════════════════
if st.session_state.get("pdf_listo") and st.session_state.get("pdf_meta"):
    meta = st.session_state.pdf_meta

    st.divider()
    st.markdown("### 📤 Enviar Nota de Venta al cliente")

    # PASO 1
    st.markdown("**Paso 1 — Descarga el PDF**")
    st.download_button(
        label="📥 DESCARGAR PDF de la Nota de Venta",
        data=st.session_state.pdf_listo,
        file_name=meta["nombre_archivo"],
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    # PASO 2 — número + botón WhatsApp en panel único sin campo extra arriba
    st.markdown("**Paso 2 — Ingresa el número y abre WhatsApp**")
    panel_whatsapp_solo_chat(
        mensaje             = meta["mensaje_wa"],
        numero_preingresado = meta.get("numero_wa", ""),
    )

    st.divider()
    if st.button("🗑️ Limpiar / Nueva operación"):
        st.session_state.pdf_listo = None
        st.session_state.pdf_meta  = None
        st.rerun()