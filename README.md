# Gestor Ambiental IA — Bitácora de Residuos Peligrosos

Aplicación web para generar automáticamente la **Bitácora de Residuos Peligrosos** (formato SEMARNAT México) a partir de manifiestos de entrega, transporte y recepción en PDF.

## Instalación rápida

```bash
# 1. Clonar o descargar los archivos
# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key de Gemini
#    Opción A: crear archivo .env
echo "GEMINI_API_KEY=tu_api_key_aqui" > .env

#    Opción B: ingresarla directamente en la app

# 5. Ejecutar
streamlit run app.py
```

## Obtener API Key de Gemini (GRATIS)

1. Ve a https://aistudio.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API key
4. Cópiala en el archivo `.env` o en la interfaz de la app

## Campos que se extraen automáticamente

| Campo | Fuente en el manifiesto |
|-------|------------------------|
| Consecutivo / Folio | Encabezado del manifiesto |
| Nombre del residuo | Sección 5 |
| Cantidad y unidad | Sección 5 |
| Características CRETIB | Sección 5 (letras marcadas con X) |
| Fecha de salida del almacén | Sección 7 (generador) |
| Nombre del responsable | Sección 7 (generador) |
| Transportista + No. Autorización | Secciones 8–12 |
| Destinatario + No. Autorización | Secciones 15–17 |
| Fase siguiente / Área de resguardo | Sección 15 |

> **Nota:** La "Fecha de ingreso al almacén" se ingresa manualmente ya que no está en el manifiesto.

## Notas importantes

- Los PDFs deben tener **texto seleccionable** (no imágenes escaneadas sin OCR)
- Se pueden procesar **múltiples manifiestos** en una sola sesión
- Los registros pueden **editarse manualmente** antes de generar el Excel
- El Excel generado incluye formato profesional con colores institucionales SEMARNAT
