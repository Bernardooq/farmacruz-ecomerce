"""
Sync Functions - Módulo centralizado de utilidades para scripts de sincronización.

Este módulo provee funciones reutilizables para:
- Limpieza de datos (texto, números, teléfonos, usernames)
- Construcción de diccionarios (productos, clientes, vendedores, listas)
- Carga de datos auxiliares (DBFs, descripciones, stock)
- Helpers de API (login, verificación de imágenes)
"""

from .data_cleaning import (
    limpiar_texto,
    normalizar_texto,
    limpiar_nombre,
    limpiar_numero,
    limpiar_digitos,
    limpiar_lada,
    construir_telefono,
    crear_username
)

from .builders import (
    build_producto_dict,
    build_categoria_dict,
    build_vendedor_dict,
    build_cliente_dict,
    build_lista_precios_dict,
    build_item_lista_dict
)

from .loaders import (
    cargar_descripciones_extra,
    cargar_existencias,
    dbf_to_dataframe
)

from .api_helpers import (
    login,
    verificar_imagen_existe
)

__all__ = [
    # Data cleaning
    'limpiar_texto',
    'normalizar_texto',
    'limpiar_nombre',
    'limpiar_numero',
    'limpiar_digitos',
    'limpiar_lada',
    'construir_telefono',
    'crear_username',
    # Builders
    'build_producto_dict',
    'build_categoria_dict',
    'build_vendedor_dict',
    'build_cliente_dict',
    'build_lista_precios_dict',
    'build_item_lista_dict',
    # Loaders
    'cargar_descripciones_extra',
    'cargar_existencias',
    'dbf_to_dataframe',
    # API helpers
    'login',
    'verificar_imagen_existe',
]
