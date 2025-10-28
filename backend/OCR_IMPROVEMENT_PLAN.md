# Plan de Mejora para Procesamiento OCR y Extracción de Texto

## Análisis de la Implementación Actual

### Componentes Existentes

1. **preprocessing.py**: Preprocesamiento de imágenes con múltiples técnicas
2. **extraction.py**: Extracción de texto usando Tesseract OCR
3. **intelligent_extraction.py**: Extracción inteligente con fallbacks y limpieza
4. **ocr_config.py**: Perfiles configurables por tipo de documento

### Fortalezas Actuales

✅ Múltiples técnicas de preprocesamiento (deskew, denoise, CLAHE, adaptive threshold)
✅ Perfiles optimizados por tipo de documento
✅ Manejo de errores con fallbacks
✅ Detección automática de idioma
✅ Sistema de confianza OCR
✅ Limpieza de artefactos OCR

### Debilidades Identificadas

❌ **No hay reintento adaptativo en caso de bajo confidence**
❌ **Falta de múltiples estrategias de binarización**
❌ **No se valida la calidad de la imagen antes de procesar**
❌ **Limitado manejo de imágenes con problemas de iluminación**
❌ **No hay detección de texto orientado/rotado**
❌ **Falta de cache para evitar reprocesamiento**
❌ **No se detecta ni corrige blur/desenfoque**
❌ **Ausencia de detección de regiones de texto (text detection)**
❌ **No hay combinación de resultados de múltiples intentos**

---

## Plan de Mejoras

### 🎯 Fase 1: Validación y Análisis Previo (PRE-PROCESSING)

#### 1.1 Detección de Calidad de Imagen
**Problema**: Se procesan imágenes sin verificar si son aptas para OCR
**Solución**: Implementar verificación de calidad antes del procesamiento

```python
# Nuevo módulo: app/services/image_quality.py

def assess_image_quality(image_path: str) -> dict:
    """
    Analiza la calidad de la imagen y sugiere mejoras.
    
    Returns:
        {
            'blur_score': float,  # 0-100, >50 es aceptable
            'brightness': float,  # 0-255, 100-150 es óptimo
            'contrast': float,    # 0-100
            'resolution': tuple,  # (width, height)
            'is_acceptable': bool,
            'recommendations': list[str]
        }
    """
    image = cv2.imread(image_path)
    
    # Detección de blur usando Laplacian
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Análisis de brillo
    brightness = np.mean(gray)
    
    # Análisis de contraste
    contrast = gray.std()
    
    # Verificar resolución mínima
    h, w = gray.shape
    resolution_ok = h >= 300 and w >= 300
    
    # Evaluar si es procesable
    is_acceptable = (
        blur_score > 100 and  # No muy borrosa
        50 < brightness < 200 and  # Ni muy oscura ni muy clara
        contrast > 30 and  # Contraste suficiente
        resolution_ok
    )
    
    # Generar recomendaciones
    recommendations = []
    if blur_score <= 100:
        recommendations.append("Image is too blurry - request better quality")
    if brightness <= 50:
        recommendations.append("Image too dark - increase brightness")
    if brightness >= 200:
        recommendations.append("Image overexposed - reduce brightness")
    if contrast <= 30:
        recommendations.append("Low contrast - enhance image")
    if not resolution_ok:
        recommendations.append("Resolution too low - use higher resolution")
    
    return {
        'blur_score': float(blur_score),
        'brightness': float(brightness),
        'contrast': float(contrast),
        'resolution': (w, h),
        'is_acceptable': is_acceptable,
        'recommendations': recommendations
    }
```

#### 1.2 Auto-corrección de Problemas Comunes
**Problema**: No se corrigen automáticamente problemas detectables
**Solución**: Pipeline de corrección automática

```python
# Añadir a preprocessing.py

def auto_correct_image(image: np.ndarray, quality_info: dict) -> np.ndarray:
    """
    Aplica correcciones automáticas basadas en análisis de calidad.
    """
    corrected = image.copy()
    
    # Corregir brillo bajo
    if quality_info['brightness'] < 80:
        corrected = cv2.convertScaleAbs(corrected, alpha=1.2, beta=30)
    
    # Corregir brillo alto
    elif quality_info['brightness'] > 180:
        corrected = cv2.convertScaleAbs(corrected, alpha=0.8, beta=-20)
    
    # Mejorar contraste bajo
    if quality_info['contrast'] < 40:
        lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        corrected = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    
    # Aplicar sharpening si hay blur moderado
    if 100 < quality_info['blur_score'] < 300:
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        corrected = cv2.filter2D(corrected, -1, kernel)
    
    return corrected
```

---

### 🎯 Fase 2: Mejoras en Preprocesamiento (PROCESSING)

#### 2.1 Múltiples Estrategias de Binarización
**Problema**: Solo se usa adaptive thresholding
**Solución**: Implementar múltiples técnicas y elegir la mejor

```python
# Añadir a preprocessing.py

def multi_binarization(gray_image: np.ndarray) -> list[tuple[np.ndarray, str]]:
    """
    Genera múltiples versiones binarizadas de la imagen.
    
    Returns:
        Lista de tuplas (imagen_binarizada, nombre_método)
    """
    results = []
    
    # 1. Adaptive Gaussian (actual)
    adaptive_gaussian = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 5
    )
    results.append((adaptive_gaussian, "adaptive_gaussian"))
    
    # 2. Adaptive Mean
    adaptive_mean = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 15, 5
    )
    results.append((adaptive_mean, "adaptive_mean"))
    
    # 3. Otsu's Binarization
    _, otsu = cv2.threshold(
        gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    results.append((otsu, "otsu"))
    
    # 4. Sauvola Binarization (mejor para documentos con sombras)
    try:
        from skimage.filters import threshold_sauvola
        window_size = 25
        thresh_sauvola = threshold_sauvola(gray_image, window_size=window_size)
        sauvola = (gray_image > thresh_sauvola).astype(np.uint8) * 255
        results.append((sauvola, "sauvola"))
    except ImportError:
        pass
    
    # 5. Niblack Binarization
    try:
        from skimage.filters import threshold_niblack
        window_size = 25
        thresh_niblack = threshold_niblack(gray_image, window_size=window_size, k=0.8)
        niblack = (gray_image > thresh_niblack).astype(np.uint8) * 255
        results.append((niblack, "niblack"))
    except ImportError:
        pass
    
    return results
```

#### 2.2 Detección y Corrección de Orientación Avanzada
**Problema**: Solo se corrige skew simple
**Solución**: Detectar texto en múltiples orientaciones

```python
# Añadir a preprocessing.py

def detect_text_orientation(image: np.ndarray) -> int:
    """
    Detecta la orientación del texto (0, 90, 180, 270 grados).
    
    Returns:
        Ángulo de rotación necesario (0, 90, 180, 270)
    """
    try:
        from pytesseract import image_to_osd
        from PIL import Image
        
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        osd = image_to_osd(pil_image, output_type=pytesseract.Output.DICT)
        rotation = osd.get('rotate', 0)
        
        return rotation
    except Exception:
        # Fallback: usar análisis de bordes
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:20]:
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            # Agrupar ángulos y elegir el más común
            angle_median = np.median(angles)
            
            # Redondear a 0, 90, 180, 270
            if -45 <= angle_median < 45:
                return 0
            elif 45 <= angle_median < 135:
                return 90
            elif 135 <= angle_median or angle_median < -135:
                return 180
            else:
                return 270
        
        return 0

def rotate_image_to_correct_orientation(image: np.ndarray) -> np.ndarray:
    """Rota la imagen a la orientación correcta."""
    rotation = detect_text_orientation(image)
    
    if rotation == 0:
        return image
    
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    rotation_matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)
    
    if rotation in [90, 270]:
        # Ajustar dimensiones para 90/270 grados
        rotated = cv2.warpAffine(
            image, rotation_matrix, (h, w),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    else:
        rotated = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    
    return rotated
```

#### 2.3 Detección de Regiones de Texto (Text Detection)
**Problema**: Se procesa toda la imagen, incluyendo áreas sin texto
**Solución**: Detectar y extraer solo regiones con texto

```python
# Nuevo módulo: app/services/text_detection.py

def detect_text_regions(image_path: str) -> list[dict]:
    """
    Detecta regiones que contienen texto en la imagen.
    
    Returns:
        Lista de regiones: [{
            'box': (x, y, w, h),
            'confidence': float,
            'image': np.ndarray
        }]
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Método 1: EAST Text Detector (si está disponible)
    # Método 2: MSER (Maximally Stable Extremal Regions)
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)
    
    # Agrupar regiones cercanas
    text_regions = []
    for region in regions:
        x, y, w, h = cv2.boundingRect(region)
        
        # Filtrar regiones muy pequeñas o muy grandes
        if 20 < w < image.shape[1] * 0.9 and 10 < h < image.shape[0] * 0.9:
            roi = image[y:y+h, x:x+w]
            text_regions.append({
                'box': (x, y, w, h),
                'confidence': 1.0,  # Placeholder
                'image': roi
            })
    
    return text_regions

def extract_text_from_regions(image_path: str, config: OCRConfig) -> str:
    """
    Extrae texto procesando solo las regiones detectadas.
    """
    regions = detect_text_regions(image_path)
    
    if not regions:
        # Fallback: procesar imagen completa
        return extract_text(image_path)
    
    # Ordenar regiones de arriba a abajo, izquierda a derecha
    regions.sort(key=lambda r: (r['box'][1], r['box'][0]))
    
    texts = []
    for region in regions:
        # Preprocesar cada región individualmente
        roi = region['image']
        # ... aplicar preprocesamiento
        # ... extraer texto
        region_text = pytesseract.image_to_string(roi, config=config.get_tesseract_config())
        if region_text.strip():
            texts.append(region_text.strip())
    
    return '\n'.join(texts)
```

---

### 🎯 Fase 3: Estrategias de Extracción Resiliente (POST-PROCESSING)

#### 3.1 Sistema de Múltiples Intentos con Votación
**Problema**: Solo se hace un intento (o pocos fallbacks)
**Solución**: Ejecutar múltiples estrategias y combinar resultados

```python
# Añadir a intelligent_extraction.py

def extract_with_multiple_strategies(
    filepath: str,
    document_type: DocumentType | None = None
) -> tuple[str, dict]:
    """
    Extrae texto usando múltiples estrategias y combina resultados.
    
    Estrategias:
    1. Preprocesamiento estándar + OCR estándar
    2. Múltiples binarizaciones + mejor resultado
    3. Detección de regiones + OCR por región
    4. Diferentes PSM modes
    5. Con/sin corrección de orientación
    """
    from app.services.image_quality import assess_image_quality, auto_correct_image
    
    results = []
    
    # Evaluar calidad inicial
    quality_info = assess_image_quality(filepath)
    
    # Estrategia 1: Pipeline estándar
    try:
        text1, conf1 = extract_with_fallback(filepath, document_type)
        results.append({
            'text': text1,
            'confidence': conf1,
            'strategy': 'standard',
            'score': conf1.get('original_confidence', {}).get('average_confidence', 0)
        })
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
    
    # Estrategia 2: Con auto-corrección
    if not quality_info['is_acceptable']:
        try:
            image = cv2.imread(filepath)
            corrected = auto_correct_image(image, quality_info)
            
            temp_path = filepath.replace('.', '_autocorrected.')
            cv2.imwrite(temp_path, corrected)
            
            text2, conf2 = extract_with_fallback(temp_path, document_type)
            results.append({
                'text': text2,
                'confidence': conf2,
                'strategy': 'auto_corrected',
                'score': conf2.get('original_confidence', {}).get('average_confidence', 0) * 1.1
            })
            
            os.unlink(temp_path)
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
    
    # Estrategia 3: Con detección de orientación
    try:
        image = cv2.imread(filepath)
        rotated = rotate_image_to_correct_orientation(image)
        
        temp_path = filepath.replace('.', '_rotated.')
        cv2.imwrite(temp_path, rotated)
        
        text3, conf3 = extract_with_fallback(temp_path, document_type)
        results.append({
            'text': text3,
            'confidence': conf3,
            'strategy': 'orientation_corrected',
            'score': conf3.get('original_confidence', {}).get('average_confidence', 0) * 1.05
        })
        
        os.unlink(temp_path)
    except Exception as e:
        print(f"Strategy 3 failed: {e}")
    
    # Elegir mejor resultado
    if not results:
        raise ValueError("All extraction strategies failed")
    
    best_result = max(results, key=lambda x: (x['score'], len(x['text'])))
    
    metadata = {
        'strategies_tried': len(results),
        'best_strategy': best_result['strategy'],
        'all_scores': {r['strategy']: r['score'] for r in results},
        'quality_assessment': quality_info
    }
    
    return best_result['text'], metadata
```

#### 3.2 Sistema de Cache para Evitar Reprocesamiento
**Problema**: Se reprocesa la misma imagen múltiples veces
**Solución**: Implementar cache basado en hash

```python
# Nuevo módulo: app/services/ocr_cache.py

import hashlib
import json
from pathlib import Path
from typing import Optional

CACHE_DIR = Path("./cache/ocr")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_file_hash(filepath: str) -> str:
    """Calcula hash SHA256 del archivo."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_cache_key(filepath: str, config_dict: dict) -> str:
    """Genera clave de cache basada en archivo y configuración."""
    file_hash = get_file_hash(filepath)
    config_str = json.dumps(config_dict, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()
    return f"{file_hash}_{config_hash}"

def get_cached_result(filepath: str, config: dict) -> Optional[dict]:
    """Recupera resultado en cache si existe."""
    cache_key = get_cache_key(filepath, config)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def cache_result(filepath: str, config: dict, result: dict) -> None:
    """Guarda resultado en cache."""
    cache_key = get_cache_key(filepath, config)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(result, f)
    except Exception as e:
        print(f"Failed to cache result: {e}")

def clear_old_cache(days: int = 7) -> None:
    """Limpia cache antiguo."""
    import time
    current_time = time.time()
    max_age = days * 86400
    
    for cache_file in CACHE_DIR.glob("*.json"):
        if current_time - cache_file.stat().st_mtime > max_age:
            cache_file.unlink()
```

#### 3.3 Post-procesamiento Inteligente con Corrección de Errores
**Problema**: No se corrigen errores comunes de OCR
**Solución**: Implementar corrección basada en contexto

```python
# Añadir a intelligent_extraction.py

def post_process_ocr_text(text: str, document_type: DocumentType) -> str:
    """
    Aplica correcciones inteligentes al texto extraído.
    """
    if not text:
        return text
    
    # Correcciones generales
    text = correct_common_ocr_errors(text)
    
    # Correcciones específicas por tipo de documento
    if document_type in [DocumentType.RECEIPT, DocumentType.INVOICE]:
        text = correct_financial_text(text)
    
    return text

def correct_common_ocr_errors(text: str) -> str:
    """Corrige errores comunes de OCR."""
    corrections = {
        # Números confundidos con letras
        r'\bO(?=\d)': '0',  # O seguida de número -> 0
        r'(?<=\d)O\b': '0',  # O después de número -> 0
        r'\bl(?=\d)': '1',  # l minúscula antes de número -> 1
        r'(?<=\d)l\b': '1',  # l después de número -> 1
        r'\bS(?=\d)': '5',  # S antes de número -> 5
        
        # Caracteres comunes mal reconocidos
        r'\|(?=\s|$)': 'I',  # Pipe al final -> I
        r'\]': ')',
        r'\[': '(',
        
        # Espacios extra alrededor de puntuación
        r'\s+([.,;:!?])': r'\1',
        r'([.,;:!?])\s{2,}': r'\1 ',
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    return text

def correct_financial_text(text: str) -> str:
    """Corrige errores en texto financiero (montos, fechas)."""
    # Corregir símbolos de moneda
    text = re.sub(r'\bS\s*/', r'$', text)  # S/ -> $
    text = re.sub(r'(?<!\d)\$\s+(?=\d)', r'$', text)  # $ 100 -> $100
    
    # Corregir separadores decimales
    text = re.sub(r'(\d+)[,.](\d{2})\b', r'\1.\2', text)  # Normalizar decimales
    
    # Corregir fechas comunes (01/O1/2024 -> 01/01/2024)
    text = re.sub(r'(\d{2})/O(\d)', r'\1/0\2', text)
    text = re.sub(r'(\d{2})/(\d)O/', r'\1/\20/', text)
    
    return text
```

---

### 🎯 Fase 4: Optimización de Performance

#### 4.1 Procesamiento Paralelo de Estrategias
**Problema**: Las estrategias se ejecutan secuencialmente
**Solución**: Paralelizar usando asyncio/threading

```python
# Añadir a intelligent_extraction.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

async def extract_parallel_strategies(
    filepath: str,
    document_type: DocumentType | None = None
) -> tuple[str, dict]:
    """
    Ejecuta múltiples estrategias en paralelo.
    """
    strategies = [
        ('standard', lambda: extract_with_fallback(filepath, document_type)),
        ('psm_sparse', lambda: extract_with_psm_mode(filepath, PSMMode.SPARSE_TEXT)),
        ('psm_single_block', lambda: extract_with_psm_mode(filepath, PSMMode.SINGLE_BLOCK)),
    ]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, strategy_func)
            for _, strategy_func in strategies
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Procesar resultados
    valid_results = []
    for (name, _), result in zip(strategies, results):
        if not isinstance(result, Exception):
            text, metadata = result
            valid_results.append({
                'text': text,
                'metadata': metadata,
                'strategy': name,
                'score': metadata.get('original_confidence', {}).get('average_confidence', 0)
            })
    
    if not valid_results:
        raise ValueError("All strategies failed")
    
    # Elegir mejor resultado
    best = max(valid_results, key=lambda x: (x['score'], len(x['text'])))
    
    return best['text'], {
        'best_strategy': best['strategy'],
        'strategies_tried': len(strategies),
        'successful_strategies': len(valid_results)
    }
```

#### 4.2 Lazy Loading y Procesamiento Incremental
**Problema**: Se carga y procesa toda la imagen de una vez
**Solución**: Procesar por regiones cuando sea posible

```python
def process_large_image_incremental(
    filepath: str,
    tile_size: int = 1000
) -> str:
    """
    Procesa imágenes grandes por tiles para reducir memoria.
    """
    image = cv2.imread(filepath)
    h, w = image.shape[:2]
    
    # Si la imagen es pequeña, procesarla normalmente
    if h <= tile_size and w <= tile_size:
        return extract_text(filepath)
    
    texts = []
    overlap = 50  # Overlap para no perder texto en bordes
    
    for y in range(0, h, tile_size - overlap):
        for x in range(0, w, tile_size - overlap):
            # Extraer tile
            tile = image[y:min(y+tile_size, h), x:min(x+tile_size, w)]
            
            # Guardar tile temporal
            temp_path = f"/tmp/tile_{y}_{x}.png"
            cv2.imwrite(temp_path, tile)
            
            # Procesar tile
            try:
                tile_text = extract_text(temp_path)
                if tile_text.strip():
                    texts.append(tile_text.strip())
            finally:
                os.unlink(temp_path)
    
    return '\n'.join(texts)
```

---

## Implementación Propuesta - Orden de Prioridad

### 🚀 Prioridad ALTA (Impacto inmediato)

1. **Validación de calidad de imagen** (Fase 1.1)
   - Detecta problemas antes de procesar
   - Ahorra tiempo en imágenes no procesables
   - Implementación: 2-3 días

2. **Auto-corrección de problemas** (Fase 1.2)
   - Mejora automática de brillo/contraste
   - Reduce fallos por mala calidad
   - Implementación: 2-3 días

3. **Sistema de cache** (Fase 3.2)
   - Evita reprocesamiento
   - Mejora dramáticamente performance
   - Implementación: 1-2 días

4. **Post-procesamiento de errores comunes** (Fase 3.3)
   - Corrige errores típicos de OCR
   - Mejora calidad de resultados
   - Implementación: 2-3 días

### ⚡ Prioridad MEDIA (Mejora significativa)

5. **Múltiples estrategias de binarización** (Fase 2.1)
   - Mejor manejo de diferentes tipos de imágenes
   - Implementación: 3-4 días

6. **Detección y corrección de orientación** (Fase 2.2)
   - Maneja imágenes rotadas
   - Implementación: 2-3 días

7. **Sistema de múltiples intentos con votación** (Fase 3.1)
   - Combina mejores resultados
   - Implementación: 4-5 días

### 🔧 Prioridad BAJA (Optimización avanzada)

8. **Detección de regiones de texto** (Fase 2.3)
   - Procesamiento más eficiente
   - Implementación: 5-7 días

9. **Procesamiento paralelo** (Fase 4.1)
   - Mejora velocidad
   - Implementación: 3-4 días

10. **Procesamiento incremental** (Fase 4.2)
    - Para imágenes muy grandes
    - Implementación: 3-4 días

---

## Estructura de Código Propuesta

```
app/
├── services/
│   ├── preprocessing.py           # [MODIFICAR] Añadir nuevas funciones
│   ├── extraction.py              # [MODIFICAR] Integrar cache
│   ├── intelligent_extraction.py  # [MODIFICAR] Añadir nuevas estrategias
│   ├── image_quality.py          # [NUEVO] Validación de calidad
│   ├── text_detection.py         # [NUEVO] Detección de regiones
│   ├── ocr_cache.py              # [NUEVO] Sistema de cache
│   └── ocr_corrections.py        # [NUEVO] Correcciones post-OCR
├── ocr_config/
│   └── ocr_config.py             # [MODIFICAR] Añadir nuevos perfiles
```

---

## Métricas de Éxito

### Antes de Mejoras (Baseline)
- Tiempo promedio de procesamiento: ~2-5 segundos
- Precisión OCR: 70-85% (variable según calidad)
- Tasa de error en imágenes problemáticas: ~30-40%
- Uso de CPU: Alto (reprocesamiento)

### Después de Mejoras (Objetivo)
- Tiempo promedio: <2 segundos (con cache), 3-6 segundos (sin cache)
- Precisión OCR: 85-95%
- Tasa de error: <15%
- Uso de CPU: Reducido 40% (gracias a cache)
- Resiliencia: 95% de imágenes procesables exitosamente

---

## Dependencias Adicionales Requeridas

```toml
# Añadir a pyproject.toml
[tool.poetry.dependencies]
scikit-image = "^0.22.0"  # Para Sauvola/Niblack binarization
joblib = "^1.3.2"          # Para procesamiento paralelo eficiente
pillow = "^10.0.0"         # Ya existe, pero verificar versión
```

---

## Testing Strategy

### Tests Unitarios
- Cada función de preprocesamiento individual
- Funciones de detección de calidad
- Sistema de cache

### Tests de Integración
- Pipeline completo con diferentes tipos de imágenes
- Diferentes estrategias de extracción
- Performance bajo carga

### Tests de Regresión
- Mantener accuracy actual en imágenes de buena calidad
- No degradar performance en casos exitosos

### Dataset de Prueba
1. **Imágenes perfectas**: 10 samples (receipts, invoices)
2. **Imágenes con blur**: 10 samples
3. **Imágenes oscuras/claras**: 10 samples
4. **Imágenes rotadas**: 10 samples
5. **Imágenes de baja resolución**: 10 samples
6. **Imágenes con fondo complejo**: 10 samples

---

## Notas de Implementación

### ⚠️ Consideraciones de Resiliencia

1. **Siempre tener fallback**: Cada nueva función debe tener un fallback al método anterior
2. **Timeout en operaciones**: Limitar tiempo de procesamiento (max 30 segundos)
3. **Manejo de excepciones**: Nunca dejar que una excepción rompa todo el pipeline
4. **Logging exhaustivo**: Registrar cada paso para debugging
5. **Validación de entrada**: Verificar tipos y valores antes de procesar

### 🎯 Principios de Performance

1. **Cache first**: Siempre verificar cache antes de procesar
2. **Fail fast**: Detectar problemas temprano
3. **Lazy evaluation**: No procesar hasta que sea necesario
4. **Batch processing**: Procesar múltiples archivos eficientemente
5. **Resource limits**: Limitar uso de memoria y CPU

---

## Conclusión

Este plan prioriza mejoras que maximizan la extracción de información mientras mantienen alta resiliencia y performance. La implementación en fases permite validar mejoras incrementalmente y ajustar según resultados.

**Tiempo estimado total**: 6-8 semanas (implementando todas las fases)
**Tiempo para mejoras prioritarias**: 2-3 semanas
