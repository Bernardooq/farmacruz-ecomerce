"""
Script para inicializar la base de datos
Crea las tablas y un usuario administrador por defecto
"""
from sqlalchemy import create_engine
from db.base import Base
from db.session import engine
from core.security import get_password_hash
from db.base import User, UserRole, Category
from sqlalchemy.orm import Session

def init_db():
    """Crea todas las tablas"""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas exitosamente")

def create_admin_user():
    """Crea un usuario administrador por defecto"""
    db = Session(bind=engine)
    
    try:
        # Verificar si ya existe un admin
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("✓ Usuario admin ya existe")
            return
        
        # Crear usuario admin
        admin_user = User(
            username="admin",
            email="admin@farmacruz.com",
            password_hash=get_password_hash("admin123"),
            full_name="Administrador",
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("✓ Usuario administrador creado")
        print("  Username: admin")
        print("  Password: admin123")
        print("  ⚠️  CAMBIA ESTA CONTRASEÑA EN PRODUCCIÓN")
        
    except Exception as e:
        print(f"✗ Error creando usuario admin: {e}")
        db.rollback()
    finally:
        db.close()

def create_default_categories():
    """Crea categorías por defecto"""
    db = Session(bind=engine)
    
    try:
        # Verificar si ya existen categorías
        count = db.query(Category).count()
        if count > 0:
            print("✓ Categorías ya existen")
            return
        
        categories = [
            Category(name="Medicamentos", description="Medicamentos de prescripción y venta libre"),
            Category(name="Cuidado Personal", description="Productos de higiene y cuidado personal"),
            Category(name="Vitaminas y Suplementos", description="Suplementos vitamínicos y nutricionales"),
            Category(name="Primeros Auxilios", description="Material de curación y primeros auxilios"),
            Category(name="Bebé y Mamá", description="Productos para bebés y maternidad"),
            Category(name="Dermocosméticos", description="Productos dermatológicos y cosméticos"),
            Category(name="Salud Sexual", description="Productos de salud sexual y planificación"),
            Category(name="Ortopedia", description="Productos ortopédicos y de movilidad"),
        ]
        
        for category in categories:
            db.add(category)
        
        db.commit()
        print("✓ Categorías por defecto creadas")
        
    except Exception as e:
        print(f"✗ Error creando categorías: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Inicializando Base de Datos - Farmacruz API")
    print("=" * 50)
    
    init_db()
    create_admin_user()
    create_default_categories()
    
    print("=" * 50)
    print("✓ Inicialización completada")
    print("=" * 50)