"""
CRUD operations for production-optimized sync.

Processes pre-parsed JSON from FarmaCruz server.
No DBF parsing needed - EC2 only inserts to database.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import math

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from sqlalchemy import text

from db.base import Product, Category, PriceList, PriceListItem, User, Customer, CustomerInfo
from crud.crud_customer import get_password_hash
from utils.sales_group_utils import bulk_assign_customers_to_agent_groups


def process_productos_from_json(
    categorias: List[str],
    productos: List[Dict],
    db: Session
) -> Dict[str, int]:
    """
    Process pre-parsed products JSON.
    """
    fecha_sync = datetime.now(timezone.utc).isoformat()
    
    # 1. UPSERT CATEGORIAS
    print(f"Upserting {len(categorias)} categories...")
    
    # Build category map: name -> id (deterministic hash)
    cat_map = {}
    categorias_data = []
    
    for cat_name in categorias:
        cat_map[cat_name] = cat_name
        categorias_data.append({
            "name": cat_name,
            "updated_at": fecha_sync
        })
    
    if categorias_data:
        stmt = insert(Category).values(categorias_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['name'],
            set_={
                'updated_at': stmt.excluded.updated_at
            }
        )
        db.execute(stmt)
        
    # RELOAD Category Map with DB IDs (Critical: Product.category_id is Integer)
    # Since we don't know the IDs of existing categories without querying
    db_categories = db.query(Category.category_id, Category.name).filter(
        Category.name.in_(list(cat_map.keys()))
    ).all()
    
    # Update map: Name -> ID
    cat_map = {c.name: c.category_id for c in db_categories}
    print(f"Mapped {len(cat_map)} categories to IDs")
    
    # 2. UPSERT PRODUCTOS
    print(f"Upserting {len(productos)} products...")
    
    productos_cleaned = []
    for p in productos:
        # Map category name to ID
        category_id = None
        if p.get('category_name'):
            category_id = cat_map.get(p['category_name'])
        
        # Ensure values are strictly typed
        updated_prod = {
            "product_id": p["product_id"],
            "codebar": p.get("codebar"),
            "name": p["name"],
            "description": p.get("description"),      # Technical description
            "descripcion_2": p.get("descripcion_2"),  # Long description
            "unidad_medida": p.get("unidad_medida"),
            "base_price": float(p.get("base_price", 0.0)),
            "iva_percentage": float(p.get("iva_percentage", 16.0)),
            "image_url": p.get("image_url"),
            "stock_count": int(p.get("stock_count", 0)),
            "is_active": p.get("is_active", True),
            "category_id": category_id,
            "updated_at": fecha_sync
        }
        productos_cleaned.append(updated_prod)
    
    if productos_cleaned:
        # Process in chunks
        CHUNK_SIZE = 1000
        for i in range(0, len(productos_cleaned), CHUNK_SIZE):
            chunk = productos_cleaned[i:i + CHUNK_SIZE]
            
            stmt = insert(Product)
            stmt = stmt.on_conflict_do_update(
                index_elements=['product_id'],
                set_={c.name: c for c in stmt.excluded if c.name != 'product_id' and c.name != 'created_at'}
            )
            db.execute(stmt, chunk)
            
    db.commit()
    
    return {
        "creados": 0,  
        "actualizados": len(productos_cleaned),
        "errores": 0
    }


def process_listas_precios_from_json(
    listas: List[Dict],
    db: Session
) -> Dict[str, int]:
    """
    Process unique price lists (Header information).
    """
    fecha_sync = datetime.now(timezone.utc).isoformat()
    print(f"Upserting {len(listas)} price lists headers...")

    listas_data = [
        {
            "price_list_id": int(lista["price_list_id"]),
            "list_name": lista.get("list_name") or lista.get("name") or f"Lista {lista['price_list_id']}",  # Map input 'list_name' or 'name' to column 'list_name'
            "is_active": True,
            "updated_at": fecha_sync
        }
        for lista in listas
    ]
    
    if listas_data:
        stmt = insert(PriceList)
        stmt = stmt.on_conflict_do_update(
            index_elements=['price_list_id'],
            set_={c.name: c for c in stmt.excluded if c.name != 'price_list_id'}
        )
        db.execute(stmt, listas_data)
        db.commit()
    
    return {
        "creados": 0,
        "actualizados": len(listas_data),
        "errores": 0
    }


def process_items_precios_from_json(
    items: List[Dict],
    db: Session
) -> Dict[str, int]:
    """
    Process price list items (Product relations).
    Validates logical consistency between markup and final price roughly.
    """
    fecha_sync = datetime.now(timezone.utc).isoformat()
    print(f"Processing {len(items)} price list items...")
    
    
    items_data = []
    
    # Optional: Logic to verification (Just logging for now, or fixing?)
    # User said: "ve que el calculo de precio de producto mas su markup sea casi igial al precio del producto"
    # We will trust LPRECPROD (final_price) as the source of truth for the transaction price,
    # but we import LMARGEN as well.
    
    for item in items:
        items_data.append({
            "price_list_id": int(item["price_list_id"]),
            "product_id": item["product_id"],
            "markup_percentage": float(item.get("markup_percentage", 0.0)),
            "final_price": float(item.get("final_price", 0.0)),
            "updated_at": fecha_sync
        })
    
    if items_data:
        # ---------------------------------------------------------------------
        # FILTER ORPHANS: Prevent IntegrityError (Foreign Key Violation)
        # We must verify that referenced products and price lists actually exist.
        # This is CRITICAL because step 1 filters out obsolete products, but step 3
        # DBF source might still contain prices for them.
        # ---------------------------------------------------------------------
        valid_product_ids = set(flat_id for (flat_id,) in db.query(Product.product_id).all())
        valid_list_ids = set(flat_id for (flat_id,) in db.query(PriceList.price_list_id).all())
        
        original_count = len(items_data)
        items_data = [
            item for item in items_data
            if item["product_id"] in valid_product_ids and item["price_list_id"] in valid_list_ids
        ]
        filtered_count = len(items_data)
        print(f"DEBUG: Filtered {original_count - filtered_count} orphan price items (Products/Lists not found). Remaining: {filtered_count}")

        # Process in chunks
        # Passing data to db.execute() instead of values() avoids 'gkpj' error with on_conflict
        CHUNK_SIZE = 1000
        for i in range(0, len(items_data), CHUNK_SIZE):
            chunk = items_data[i:i + CHUNK_SIZE]
            
            # Define statement without values
            stmt = insert(PriceListItem)
            stmt = stmt.on_conflict_do_update(
                index_elements=['price_list_id', 'product_id'],
                set_={c.name: c for c in stmt.excluded if c.name not in ['price_list_id', 'product_id']}
            )
            # Execute with parameters
            db.execute(stmt, chunk)
            db.commit()
    

    return {
        "creados": 0,
        "actualizados": len(items_data),
        "errores": 0,
        "total_items": len(items_data) # Return actual count after filtering
    }


# ============================================================================
# SELLERS & CUSTOMERS (GZIP OPTIMIZED)
# ============================================================================

def process_sellers_from_json(
    sellers: List[Dict],
    db: Session
) -> Dict[str, int]:
    """
    Process pre-parsed Sellers JSON (Bulk Upsert).
    """
    if not sellers:
        return {"creados": 0, "actualizados": 0, "errores": 0}

    print(f"Upserting {len(sellers)} sellers...")
    fecha_sync = datetime.now(timezone.utc).isoformat()
    
    creados = 0
    actualizados = 0
    
    try:
        # 1. Identify Existing vs New
        user_ids = [int(s['user_id']) for s in sellers]
        existing_users = db.query(User.user_id).filter(User.user_id.in_(user_ids)).all()
        existing_ids = {u.user_id for u in existing_users}
        
        for s in sellers:
            if int(s['user_id']) in existing_ids:
                actualizados += 1
            else:
                creados += 1

        # 2. Optimized Password Hashing (only unique passwords)
        password_hashes = {}
        for s in sellers:
            pwd = s.get('password')
            if pwd and pwd not in password_hashes:
                password_hashes[pwd] = get_password_hash(pwd)

        # 3. Prepare Data
        sellers_data = []
        for s in sellers:
            pwd_hash = password_hashes.get(s.get('password'))
            
            sellers_data.append({
                "user_id": int(s['user_id']),
                "username": s['username'],
                "email": s.get('email') or f"{s['username']}@farmacruz.local",
                "full_name": s['full_name'] or s['username'],
                "password_hash": pwd_hash,
                "role": "seller",
                "is_active": s.get("is_active", True),
                "updated_at": fecha_sync
            })

        # 4. Bulk Upsert
        if sellers_data:
            stmt = insert(User).values(sellers_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id'],
                set_={
                    'email': stmt.excluded.email,
                    'full_name': stmt.excluded.full_name,
                    'is_active': stmt.excluded.is_active,
                    'updated_at': stmt.excluded.updated_at
                }
            )
            db.execute(stmt)
            db.commit()

        return {"creados": creados, "actualizados": actualizados, "errores": 0}

    except Exception as e:
        print(f"Error upserting sellers: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
        return {"creados": 0, "actualizados": 0, "errores": len(sellers)}


def process_customers_from_json(
    customers: List[Dict],
    db: Session
) -> Dict[str, int]:
    """
    Process pre-parsed Customers JSON (Bulk Upsert Customer + Sync Info + Groups).
    """
    if not customers:
        return {"creados": 0, "actualizados": 0, "errores": 0}

    print(f"Upserting {len(customers)} customers...")
    fecha_sync = datetime.now(timezone.utc).isoformat()
    
    creados = 0
    actualizados = 0
    
    try:
        # 1. Identify Existing
        customer_ids = [int(c['customer_id']) for c in customers]
        existing = db.query(Customer.customer_id).filter(Customer.customer_id.in_(customer_ids)).all()
        existing_ids = {c.customer_id for c in existing}
        
        for c in customers:
            if int(c['customer_id']) in existing_ids:
                actualizados += 1
            else:
                creados += 1
                
        # 2. Password Hashing
        password_hashes = {}
        for c in customers:
            pwd = c.get('password')
            if pwd and pwd not in password_hashes:
                password_hashes[pwd] = get_password_hash(pwd)

        # 3. Prepare Customer & CustomerInfo Data
        customers_data = []
        info_data = []
        
        for c in customers:
            cid = int(c['customer_id'])
            # Customer Table
            customers_data.append({
                "customer_id": cid,
                "username": c['username'],
                "email": c.get('email') or f"{c['username']}@farmacruz.local",
                "full_name": c.get('full_name') or c['username'],
                "password_hash": password_hashes.get(c.get('password')),
                "is_active": True,
                "agent_id": c.get('agent_id'), # Link to seller
                "updated_at": fecha_sync
            })
            
            # CustomerInfo Table
            info_data.append({
                "customer_id": cid,
                "business_name": c.get('business_name') or c.get('full_name'),
                "rfc": c.get('rfc'),
                "price_list_id": c.get('price_list_id'),
                "address_1": c.get('address_1'),
                "address_2": c.get('address_2'),
                "address_3": c.get('address_3'),
                "telefono_1": c.get('telefono_1'),
                "telefono_2": c.get('telefono_2')
            })

        # 4. CHUNKED EXECUTION
        CHUNK_SIZE = 1000
        total_customers = len(customers_data)
        
        for i in range(0, total_customers, CHUNK_SIZE):
            chunk_cust = customers_data[i:i + CHUNK_SIZE]
            chunk_info = info_data[i:i + CHUNK_SIZE]
            
            # A. Upsert Customer
            stmt_cust = insert(Customer).values(chunk_cust)
            stmt_cust = stmt_cust.on_conflict_do_update(
                index_elements=['customer_id'],
                set_={
                    'email': stmt_cust.excluded.email,
                    'full_name': stmt_cust.excluded.full_name,
                    'is_active': stmt_cust.excluded.is_active,
                    'agent_id': stmt_cust.excluded.agent_id,
                    'updated_at': stmt_cust.excluded.updated_at
                }
            )
            db.execute(stmt_cust)
            db.flush() # Ensure foreign keys exist

            # B. Upsert CustomerInfo
            stmt_info = insert(CustomerInfo).values(chunk_info)
            stmt_info = stmt_info.on_conflict_do_update(
                index_elements=['customer_id'],
                set_={
                    'business_name': stmt_info.excluded.business_name,
                    'rfc': stmt_info.excluded.rfc,
                    'price_list_id': stmt_info.excluded.price_list_id,
                    'address_1': stmt_info.excluded.address_1,
                    'address_2': stmt_info.excluded.address_2,
                    'address_3': stmt_info.excluded.address_3,
                    'telefono_1': stmt_info.excluded.telefono_1,
                    'telefono_2': stmt_info.excluded.telefono_2
                }
            )
            db.execute(stmt_info)
            
        # 5. Group Assignment (Reuse logic)
        customers_with_agents = [
            {'customer_id': int(c['customer_id']), 'agent_id': int(c['agent_id'])}
            for c in customers if c.get('agent_id')
        ]
        
        if customers_with_agents:
            bulk_assign_customers_to_agent_groups(db, customers_with_agents)

        db.commit()
        return {"creados": creados, "actualizados": actualizados, "errores": 0}

    except Exception as e:
        print(f"Error upserting customers: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
        return {"creados": 0, "actualizados": 0, "errores": len(customers)}
