#!/usr/bin/env python3
"""
Analizador de Tamaño de Archivos
=================================

Lista todos los archivos de una carpeta con su tamaño,
ordenados de mayor a menor.

"""

from pathlib import Path
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Carpeta a analizar
FOLDER_TO_ANALYZE = Path("/Users/bernardoorozco/Downloads/CompressedImg")

# Mostrar solo ciertos tipos de archivo (dejar vacío para todos)
# Ejemplo: {'.webp', '.jpg', '.png'} o {} para todos
FILE_EXTENSIONS = {'.webp', '.jpg', '.jpeg'}  # Solo WebP, cambia a {} para ver todos

# ============================================================================
# FUNCIONES
# ============================================================================

def formatear_tamaño(bytes_size):
    """Convierte bytes a formato legible (KB, MB, GB)"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def obtener_archivos_con_tamaño(carpeta, extensiones=None):
    """
    Retorna lista de tuplas (archivo_path, tamaño_bytes, nombre)
    ordenada de mayor a menor tamaño
    """
    archivos = []
    
    for archivo in carpeta.rglob('*'):
        if archivo.is_file():
            # Filtrar por extensión si se especificó
            if extensiones and archivo.suffix.lower() not in extensiones:
                continue
            
            try:
                tamaño = archivo.stat().st_size
                archivos.append((archivo, tamaño, archivo.name))
            except OSError:
                # Ignorar archivos que no se pueden acceder
                continue
    
    # Ordenar de mayor a menor tamaño
    archivos.sort(key=lambda x: x[1], reverse=True)
    
    return archivos


def main():
    """Función principal"""
    print("="*80)
    print("📊 Analizador de Tamaño de Archivos")
    print("="*80)
    print()
    
    # Verificar que existe la carpeta
    if not FOLDER_TO_ANALYZE.exists():
        print(f"❌ Error: No existe la carpeta {FOLDER_TO_ANALYZE}")
        return
    
    print(f"📁 Carpeta: {FOLDER_TO_ANALYZE}")
    if FILE_EXTENSIONS:
        print(f"🔍 Filtro: {', '.join(FILE_EXTENSIONS)}")
    else:
        print(f"🔍 Filtro: Todos los archivos")
    print()
    
    # Obtener archivos
    print("⏳ Analizando archivos...")
    archivos = obtener_archivos_con_tamaño(FOLDER_TO_ANALYZE, FILE_EXTENSIONS)
    
    if not archivos:
        print("⚠️  No se encontraron archivos")
        return
    
    # Calcular totales
    tamaño_total = sum(tamaño for _, tamaño, _ in archivos)
    
    print()
    print("="*80)
    print(f"{'NOMBRE':<50} {'TAMAÑO':>15} {'% DEL TOTAL':>10}")
    print("="*80)
    
    # Mostrar archivos
    for archivo_path, tamaño, nombre in archivos:
        tamaño_formateado = formatear_tamaño(tamaño)
        porcentaje = (tamaño / tamaño_total) * 100 if tamaño_total > 0 else 0
        
        # Truncar nombre si es muy largo
        nombre_display = nombre if len(nombre) <= 48 else nombre[:45] + "..."
        
        print(f"{nombre_display:<50} {tamaño_formateado:>15} {porcentaje:>9.1f}%")
    
    # Resumen
    print("="*80)
    print(f"📊 RESUMEN")
    print(f"   Total de archivos: {len(archivos)}")
    print(f"   Tamaño total: {formatear_tamaño(tamaño_total)}")
    
    if len(archivos) > 0:
        promedio = tamaño_total / len(archivos)
        print(f"   Tamaño promedio: {formatear_tamaño(promedio)}")
        
        # Archivo más grande y más pequeño
        mas_grande = archivos[0]
        mas_pequeño = archivos[-1]
        print(f"   Más grande: {mas_grande[2]} ({formatear_tamaño(mas_grande[1])})")
        print(f"   Más pequeño: {mas_pequeño[2]} ({formatear_tamaño(mas_pequeño[1])})")
    
    print("="*80)


if __name__ == "__main__":
    main()
