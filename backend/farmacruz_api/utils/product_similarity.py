"""
Utilidad para encontrar productos similares basados en componentes activos.

Extrae componentes de descripcion_2 y calcula similitud entre productos.
"""

import re
import unicodedata
from typing import Set, List, Tuple

# Palabras a ignorar (formas farmacéuticas, conectores, unidades)
STOPWORDS = {
    # Conectores
    "CON", "Y", "DE", "LA", "EL", "LOS", "LAS", "EN", "A", "UN", "UNA",
    "DEL", "PARA", "POR", "SIN", "SOBRE",
    
    # Formas farmacéuticas
    "TABS", "TAB", "TABLETAS", "TABLETA", "CAPSULAS", "CAPSULA", "CAP", "CAPS",
    "SOL", "SOLUCION", "SUSPENSION", "SUSP", "JARABE", "AMPOLLETA", "AMP",
    "INYECTABLE", "INY", "CREMA", "GEL", "UNGÜENTO", "UNGUENTO", "POMADA",
    "GOTAS", "SPRAY", "AEROSOL", "POLVO", "GRANULADO", "SUPOSITORIO",
    
    # Unidades y medidas
    "MG", "G", "GR", "GRAMOS", "ML", "L", "LITRO", "LITROS", "MCG", "UI",
    "MU", "MM", "CM", "KG", "MILIGRAMOS", "MILILITROS",
    
    # Cantidades comunes
    "C", "FCO", "FRASCO", "CAJA", "ENV", "ENVASE", "BLISTER",
    
    # Vías de administración  
    "ORAL", "TOPICA", "TOPICO", "OFTALMICO", "OFTALMICA", "OTICO", "NASAL",
    "RECTAL", "VAGINAL", "SUBLINGUAL", "BUCAL", "PARENTERAL",
    
    # Otros
    "LAB", "LABORATORIO", "LABORATORIOS", "MR", "SR", "XR", "LP",
    "CONTIENE", "NO", "SABOR", "INFANTIL", "PEDIATRICO", "ADULTO",
    "AZUCAR", "SIN", "LIBRE"
}


def normalize_text(text: str) -> str:
    """
    Normaliza texto: uppercase, sin acentos, sin caracteres especiales.
    """
    if not text:
        return ""
    
    # Remover acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Uppercase
    text = text.upper()
    
    # Remover caracteres especiales menos espacios y comas
    text = re.sub(r'[^A-Z0-9\s,]', ' ', text)
    
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_active_components(descripcion_2: str) -> Set[str]:
    """
    Extrae componentes activos de descripcion_2.
    
    Proceso:
    1. Normalizar texto
    2. Dividir por comas y espacios
    3. Filtrar stopwords
    4. Filtrar números solos
    5. Retornar set de componentes únicos
    
    Ejemplo:
    "AMANTADINA, CLORFENAMINA, PARACETAMOL 0.05/0.02/300G 60ML"
    → {"AMANTADINA", "CLORFENAMINA", "PARACETAMOL"}
    """
    if not descripcion_2:
        return set()
    
    # Normalizar
    text = normalize_text(descripcion_2)
    
    # Dividir por comas primero
    parts = text.split(',')
    
    # Luego dividir cada parte por espacios
    tokens = []
    for part in parts:
        tokens.extend(part.split())
    
    # Filtrar stopwords y tokens muy cortos/numéricos
    components = set()
    for token in tokens:
        # Ignorar tokens muy cortos (< 3 caracteres)
        if len(token) < 3:
            continue
        
        # Ignorar números puros
        if token.isdigit():
            continue
        
        # Ignorar tokens que son solo números con punto/slash
        if re.match(r'^[\d./]+$', token):
            continue
        
        # Ignorar stopwords
        if token in STOPWORDS:
            continue
        
        # Agregar componente
        components.add(token)
    
    return components


def calculate_similarity_score(components_a: Set[str], components_b: Set[str]) -> float:
    """
    Calcula score de similitud entre dos conjuntos de componentes.
    
    Usa Jaccard similarity: |A ∩ B| / |A ∪ B|
    
    Retorna:
    - 0.0: Sin componentes en común
    - 1.0: Exactamente los mismos componentes
    - 0.5: 50% de componentes en común
    """
    if not components_a or not components_b:
        return 0.0
    
    intersection = components_a & components_b
    union = components_a | components_b
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def find_similar_products_indices(
    target_components: Set[str],
    all_products_components: List[Tuple[str, Set[str]]],
    min_similarity: float = 0.3,
    limit: int = 5
) -> List[Tuple[str, float]]:
    """
    Encuentra productos similares basados en componentes.
    
    Args:
        target_components: Componentes del producto objetivo
        all_products_components: Lista de (product_id, componentes)
        min_similarity: Umbral mínimo de similitud (default 0.3 = 30%)
        limit: Máximo número de resultados
    
    Returns:
        Lista de (product_id, similarity_score) ordenados por score descendente
    """
    if not target_components:
        return []
    
    # Calcular scores para todos los productos
    similarities = []
    for product_id, components in all_products_components:
        score = calculate_similarity_score(target_components, components)
        if score >= min_similarity:
            similarities.append((product_id, score))
    
    # Ordenar por score descendente
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Retornar top N
    return similarities[:limit]
