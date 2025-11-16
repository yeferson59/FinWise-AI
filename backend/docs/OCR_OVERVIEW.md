# FinWise-AI OCR Overview

Este documento centraliza toda la información sobre el sistema OCR de FinWise-AI: arquitectura, endpoints, configuración, mejoras, soporte multilenguaje, troubleshooting y roadmap.

## 1. Descripción General
El sistema OCR permite extraer texto de imágenes y PDFs (recibos, facturas, formularios, etc.) en inglés y español, con preprocesamiento inteligente, perfiles optimizados y métricas de calidad.

## 2. Arquitectura y Flujo de Procesamiento
- **Flujo principal:**
  1. El usuario sube un archivo (imagen/PDF).
  2. El archivo se guarda en almacenamiento local o S3.
  3. Se descarga/localiza para procesamiento.
  4. Se preprocesa la imagen (escalado, deskew, denoise, contraste, etc.).
  5. Se ejecuta OCR (Tesseract, EasyOCR, PaddleOCR, DocTR).
  6. Se sube la imagen preprocesada a S3 (si aplica).
  7. Se limpian los archivos temporales.
  8. Se retorna el texto extraído y metadatos.

- **Diagramas:**
  - Flujos completos para almacenamiento local y S3.
  - Manejo de archivos temporales y limpieza automática.

## 3. Endpoints y Ejemplos de Uso
- **Principales endpoints:**
  - `POST /api/v1/files/extract-text` (básico, multilenguaje)
  - `POST /api/v1/files/extract-text-with-confidence` (con métricas de calidad)
  - `POST /api/v1/files/extract-text-intelligent` (estrategias de fallback y validación)
  - `GET /api/v1/files/document-types` (perfiles de documento)
  - `GET /api/v1/files/supported-languages` (idiomas soportados)

- **Ejemplo Python:**
```python
import requests
with open('recibo.jpg', 'rb') as f:
    response = requests.post('http://localhost:8000/api/v1/files/extract-text', files={'file': f}, params={'document_type': 'receipt'})
    print(response.json()['raw_text'])
```

- **Ejemplo cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/extract-text?document_type=receipt" -F "file=@recibo.jpg"
curl "http://localhost:8000/api/v1/files/supported-languages"
```

## 4. Configuración y Perfiles de Documento
- **Perfiles disponibles:** receipt, invoice, document, form, screenshot, photo, general, handwritten.
- **Configuración avanzada:**
  - PSM (Page Segmentation Mode)
  - OEM (OCR Engine Mode)
  - PreprocessingConfig (escalado, deskew, denoise, CLAHE, etc.)
- **Multilenguaje:**
  - `eng`, `spa`, `eng+spa` (por defecto)
  - Whitelist de caracteres para español

## 5. Mejoras Técnicas Implementadas
- Preprocesamiento inteligente (escalado, deskew, CLAHE, denoise)
- Configuración avanzada de Tesseract (`--oem 3 --psm 6 -c preserve_interword_spaces=1`)
- Perfiles optimizados por tipo de documento
- Estrategias de fallback y validación de calidad
- Limpieza automática de archivos temporales
- Integración completa con S3/local
- Respuestas API enriquecidas (preprocessed_file_id, calidad, confianza)

## 6. Soporte Multilenguaje y Calidad
- Extracción bilingüe por defecto (inglés/español)
- Detección automática de idioma en el texto extraído
- Métricas de confianza y calidad (average, min, max, low confidence words)
- Limpieza y normalización de texto
- Recomendaciones de calidad en la respuesta

## 7. Troubleshooting y Tips
- **Problemas comunes:**
  - Baja confianza: mejorar calidad de imagen, usar perfil adecuado
  - Caracteres españoles no reconocidos: verificar instalación de `tesseract-ocr-spa`
  - Archivos temporales no limpiados: revisar logs y configuración
  - Preprocessed_file_id no aparece: verificar configuración S3
- **Tips:**
  - Usar imágenes de mínimo 1000px de alto y buena iluminación
  - Elegir el perfil de documento correcto
  - Revisar la imagen preprocesada para debugging

## 8. Testing y Validación
- Pruebas unitarias e integración en `tests/test_ocr_workflow.py` y `test_multilang_ocr.py`
- Validación de limpieza, calidad, integración S3/local
- Ejecución: `python test_multilang_ocr.py`

## 9. Historial de Mejoras y Roadmap
- **Fase 1:** Calidad de imagen, auto-corrección, caché, post-procesamiento de errores, endpoints de calidad y caché.
- **Fase 2:** Múltiples estrategias de binarización, detección y corrección de orientación, extracción multi-estrategia con votación, endpoint avanzado.
- **Fase 3:** Detección de regiones de texto, procesamiento paralelo, procesamiento incremental para imágenes grandes, endpoint optimizado.
- **Changelog:** Mejoras de velocidad (hasta 95% más rápido con caché), precisión (hasta 98%), manejo de imágenes grandes, compatibilidad total.
- **Próximos pasos:** Soporte para más idiomas, reconocimiento de manuscritos, detección automática de tipo de documento, GPU acceleration, layout analysis, ML-based post-correction.

---
**Este documento reemplaza y centraliza toda la documentación OCR previa. Para detalles específicos, consulta las secciones correspondientes o abre un issue. Última actualización: Noviembre 16, 2025.**
