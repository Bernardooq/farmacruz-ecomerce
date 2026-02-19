"""
API Helpers - Utilidades para comunicación con el backend API.
"""

import requests


def login(backend_url, username, password):
    """Hace login y retorna el token"""
    try:
        response = requests.post(
            f"{backend_url}/auth/login/sync",
            data={"username": username, "password": password},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None


def verificar_imagen_existe(producto_id, images_folder, cdn_url):
    """
    Verifica si existe la imagen del producto.
    Retorna la URL del CDN si existe, None si no existe.
    """
    from pathlib import Path
    imagen_path = Path(images_folder) / f"{producto_id}.webp"
    if imagen_path.exists():
        return f"{cdn_url}/{producto_id}.webp"
    return None
