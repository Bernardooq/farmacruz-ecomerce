#!/usr/bin/env python3
"""
Compresor de Imágenes a WebP - COMPRESIÓN ADAPTATIVA
=====================================================

Convierte imágenes JPG/PNG a WebP con compresión ADAPTATIVA:
- Imágenes GRANDES (>100KB): Comprime MUY agresivamente hasta <50KB
- Imágenes normales: Compresión estándar

OPTIMIZACIONES:
1. Redimensiona imágenes grandes progresivamente
2. Reduce calidad iterativamente hasta alcanzar objetivo
3. Convierte todo a RGB para mejor compresión
"""

from pathlib import Path
from PIL import Image
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Carpeta con imágenes originales
# SOURCE_FOLDER = Path("/Users/bernardoorozco/Downloads/Imagenes")
SOURCE_FOLDER= Path("C:\\Users\\berna\\Downloads\\Imagenes")
# Carpeta destino para WebP comprimidos
# OUTPUT_FOLDER = Path("/Users/bernardoorozco/Downloads/CompressedImg")
OUTPUT_FOLDER = Path("C:\\Users\\berna\\Downloads\\CompressedImg")

# Calidad de compresión WebP inicial (0-100)
WEBP_QUALITY = 70

# Dimensiones máximas iniciales
MAX_DIMENSION = 1200

# OBJETIVO: Todas las imágenes < 50KB
TARGET_SIZE_KB = 50

# Formatos de imagen soportados
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}

# ============================================================================
# FUNCIONES
# ============================================================================

def crear_carpeta_destino():
    """Crea la carpeta de salida si no existe"""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    print(f"✅ Carpeta destino: {OUTPUT_FOLDER}")


def obtener_tamaño_mb(ruta):
    """Retorna el tamaño del archivo en MB"""
    return os.path.getsize(ruta) / (1024 * 1024)


def obtener_tamaño_kb(ruta):
    """Retorna el tamaño del archivo en KB"""
    return os.path.getsize(ruta) / 1024


def comprimir_a_webp_adaptativo(imagen_path):
    """
    Convierte una imagen a WebP con compresión ADAPTATIVA
    - Imágenes grandes: comprime más agresivamente hasta <50KB
    - Imágenes normales: compresión estándar
    Retorna (exito: bool, tamaño_original_mb, tamaño_final_mb)
    """
    try:
        # Nombre del archivo sin extensión
        nombre_base = imagen_path.stem
        webp_path = OUTPUT_FOLDER / f"{nombre_base}.webp"
        
        # Si ya existe, saltar
        if webp_path.exists():
            print(f"⏭️  Ya existe: {nombre_base}.webp")
            return False, 0, 0
        
        # Abrir imagen
        with Image.open(imagen_path) as img:
            # Tamaño original
            tamaño_original_mb = obtener_tamaño_mb(imagen_path)
            ancho_original, alto_original = img.size
            
            # Convertir a RGB primero
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # ============================================================
            # COMPRESIÓN ADAPTATIVA CON OBJETIVO <50KB
            # ============================================================
            current_dimension = MAX_DIMENSION
            current_quality = WEBP_QUALITY
            intento = 0
            max_intentos = 6
            
            while intento < max_intentos:
                # Crear copia de la imagen para este intento
                img_procesada = img.copy()
                redimensionado = False
                
                # Redimensionar si excede la dimensión actual
                if max(img_procesada.size) > current_dimension:
                    if img_procesada.width > img_procesada.height:
                        nuevo_ancho = current_dimension
                        nuevo_alto = int((current_dimension / img_procesada.width) * img_procesada.height)
                    else:
                        nuevo_alto = current_dimension
                        nuevo_ancho = int((current_dimension / img_procesada.height) * img_procesada.width)
                    
                    img_procesada = img_procesada.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
                    redimensionado = True
                
                # Guardar con calidad actual
                img_procesada.save(
                    webp_path,
                    'WEBP',
                    quality=current_quality,
                    method=6
                )
                
                # Verificar tamaño resultante
                tamaño_final_kb = obtener_tamaño_kb(webp_path)
                
                # ¿Alcanzamos el objetivo?
                if tamaño_final_kb <= TARGET_SIZE_KB:
                    tamaño_final_mb = obtener_tamaño_mb(webp_path)
                    reduccion = ((tamaño_original_mb - tamaño_final_mb) / tamaño_original_mb) * 100
                    
                    # Mostrar resultado exitoso
                    if tamaño_original_mb >= 0.1:
                        print(f"✅ {nombre_base}: {tamaño_original_mb:.2f}MB → {tamaño_final_kb:.1f}KB ({reduccion:.0f}%)", end="")
                    else:
                        orig_kb = obtener_tamaño_kb(imagen_path)
                        print(f"✅ {nombre_base}: {orig_kb:.1f}KB → {tamaño_final_kb:.1f}KB ({reduccion:.0f}%)", end="")
                    
                    # Mostrar optimizaciones aplicadas
                    if redimensionado or intento > 0:
                        extras = []
                        if redimensionado:
                            extras.append(f"{img_procesada.width}x{img_procesada.height}")
                        if intento > 0:
                            extras.append(f"q:{current_quality}")
                        print(f" [{', '.join(extras)}]")
                    else:
                        print()
                    
                    return True, tamaño_original_mb, tamaño_final_mb
                
                # No alcanzamos el objetivo, siguiente intento
                intento += 1
                
                # ESTRATEGIA DE COMPRESIÓN PROGRESIVA:
                # Intentos 1-2: Reducir calidad
                # Intentos 3+: Reducir dimensiones además de calidad
                if intento <= 2:
                    current_quality = max(45, current_quality - 12)
                else:
                    current_dimension = int(current_dimension * 0.80)  # 80% de la dimensión anterior
                    current_quality = max(45, current_quality - 8)
            
            # Si después de todos los intentos aún excede, aceptar el mejor resultado
            tamaño_final_mb = obtener_tamaño_mb(webp_path)
            tamaño_final_kb = obtener_tamaño_kb(webp_path)
            reduccion = ((tamaño_original_mb - tamaño_final_mb) / tamaño_original_mb) * 100
            
            print(f"⚠️  {nombre_base}: {tamaño_original_mb:.2f}MB → {tamaño_final_kb:.1f}KB ({reduccion:.0f}%) [excede {TARGET_SIZE_KB}KB]")
            
            return True, tamaño_original_mb, tamaño_final_mb
            
    except Exception as e:
        print(f"❌ Error con {imagen_path.name}: {e}")
        return False, 0, 0


def main():
    """Función principal"""
    print("="*70)
    print("🖼️  Compresor ADAPTATIVO de Imágenes a WebP")
    print(f"   Objetivo: <{TARGET_SIZE_KB}KB por imagen")
    print("="*70)
    print()
    
    # Verificar que existe la carpeta origen
    if not SOURCE_FOLDER.exists():
        print(f"❌ Error: No existe la carpeta {SOURCE_FOLDER}")
        return
    
    # Crear carpeta destino
    crear_carpeta_destino()
    print()
    
    # Obtener todas las imágenes
    imagenes = []
    for ext in SUPPORTED_FORMATS:
        imagenes.extend(SOURCE_FOLDER.glob(f"*{ext}"))
        imagenes.extend(SOURCE_FOLDER.glob(f"*{ext.upper()}"))
    
    if not imagenes:
        print(f"⚠️  No se encontraron imágenes en {SOURCE_FOLDER}")
        return
    
    print(f"📁 Encontradas {len(imagenes)} imágenes")
    print()
    
    # Comprimir cada imagen
    exitos = 0
    tamaño_total_original = 0
    tamaño_total_final = 0
    imagenes_bajo_objetivo = 0
    
    for imagen in sorted(imagenes):
        exito, orig, final = comprimir_a_webp_adaptativo(imagen)
        if exito:
            exitos += 1
            tamaño_total_original += orig
            tamaño_total_final += final
            
            # Verificar si está bajo el objetivo
            webp_path = OUTPUT_FOLDER / f"{imagen.stem}.webp"
            if webp_path.exists() and obtener_tamaño_kb(webp_path) <= TARGET_SIZE_KB:
                imagenes_bajo_objetivo += 1
    
    # Resumen
    print()
    print("="*70)
    print(f"✅ Compresión completada")
    print(f"   Procesadas: {exitos}/{len(imagenes)} imágenes")
    if exitos > 0:
        print(f"   Bajo objetivo (<{TARGET_SIZE_KB}KB): {imagenes_bajo_objetivo}/{exitos} ({imagenes_bajo_objetivo*100/exitos:.0f}%)")
        print(f"   Tamaño original total: {tamaño_total_original:.2f} MB")
        print(f"   Tamaño final total: {tamaño_total_final:.2f} MB")
        reduccion_total = ((tamaño_total_original - tamaño_total_final) / tamaño_total_original) * 100
        print(f"   Reducción total: {reduccion_total:.1f}%")
        print(f"   Ahorro: {tamaño_total_original - tamaño_total_final:.2f} MB")
    print("="*70)


if __name__ == "__main__":
    main()
