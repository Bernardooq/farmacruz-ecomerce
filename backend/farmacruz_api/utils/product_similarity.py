"""
Utilidad para encontrar productos similares basados en componentes activos.

Extrae componentes de descripcion_2 y calcula similitud entre productos.
"""

import re
import unicodedata
from typing import Set, List, Tuple
import itertools
from sqlalchemy.orm import Session
from sqlalchemy import insert
import sys
import os

# Permitir ejecucion directa del script resolviendo el path del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.base import Product, ProductRecommendation

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



def bulk_update_recommendations(db: Session):
    try:
        print("--- INICIANDO MOTOR DE RECOMENDACIONES POR CATEGORÍA ---")
        
        # 1. Extraer productos incluyendo el category_id
        print("Obteniendo productos de la base de datos...")
        products = db.query(Product).filter(
            Product.is_active == True,
            Product.descripcion_2.isnot(None)
        ).all()
        
        if not products:
            print("No hay productos para procesar.")
            return

        # 2. Agrupar productos por categoría en un diccionario
        # { category_id: [lista_de_productos_procesados] }
        print(f"Agrupando y pre-procesando {len(products)} productos...")
        categories_map = {}
        
        for p in products:
            components = extract_active_components(p.descripcion_2)
            if not components:
                continue
                
            cat_id = p.category_id
            if cat_id not in categories_map:
                categories_map[cat_id] = []
                
            categories_map[cat_id].append({
                "id": p.product_id,
                "components": components
            })

        # 3. Calcular similitudes SOLO dentro de cada categoría
        print("Calculando similitudes intra-categoría...")
        candidates_map = {}

        for cat_id, cat_products in categories_map.items():
            # Inicializar mapa de candidatos para cada producto en esta categoría
            for p in cat_products:
                candidates_map[p['id']] = []
            
            # Si solo hay un producto en la categoría, no hay nada que comparar
            if len(cat_products) < 2:
                continue

            # Comparamos parejas solo dentro de esta categoría específica
            for a, b in itertools.combinations(cat_products, 2):
                score = calculate_similarity_score(a['components'], b['components'])
                
                if score >= 0.3:
                    candidates_map[a['id']].append({"id": b['id'], "score": score})
                    candidates_map[b['id']].append({"id": a['id'], "score": score})

        # 4. Preparar lista final (Top 5 por producto)
        print("Filtrando el Top 5 por producto...")
        final_recs_to_insert = []
        
        for product_id, recs in candidates_map.items():
            if not recs:
                continue
            # Ordenamos por score y tomamos 5
            top_5 = sorted(recs, key=lambda x: x['score'], reverse=True)[:5]
            
            for r in top_5:
                final_recs_to_insert.append({
                    "product_id": product_id,
                    "recommended_product_id": r['id'],
                    "score": round(r['score'], 2),
                    "recommendation_type": "intersection/union"
                })

        # 5. Limpiar e insertar
        print(f"Insertando {len(final_recs_to_insert)} recomendaciones...")
        db.query(ProductRecommendation).delete()
        
        if final_recs_to_insert:
            db.execute(insert(ProductRecommendation), final_recs_to_insert)
            db.commit()
            print("--- PROCESO COMPLETADO EXITOSAMENTE ---")
        else:
            print("No se generaron recomendaciones.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    from db.session import SessionLocal
    db = SessionLocal()
    bulk_update_recommendations(db)