# 🏢 Gestión Multi-Tenant: BO Tech Solutions (RDS PostgreSQL)

Esta guía documenta cómo crear y gestionar nuevos clientes (tenants) usando **esquemas aislados** dentro del RDS compartido, evitando el uso del usuario administrativo `farmacruzdb` en el día a día.

> **Fuente de verdad de infraestructura:** consulta `DEPLOY_GUIDE.md` para EC2, Nginx, systemd y todo lo relacionado al servidor.

---

## 📋 Tabla de Contenido

1. [Conexión Administrativa al RDS](#1-conexión-administrativa-al-rds)
2. [Dar de Alta un Nuevo Cliente (Tenant)](#2-dar-de-alta-un-nuevo-cliente-tenant)
3. [Configurar el .env del Servidor del Cliente](#3-configurar-el-env-del-servidor-del-cliente)
4. [Verificar el Aislamiento](#4-verificar-el-aislamiento)
5. [Script de Inicialización de Tablas (Botón de Deploy)](#5-script-de-inicialización-de-tablas-botón-de-deploy)
6. [Limpieza o Baja de un Cliente](#6-limpieza-o-baja-de-un-cliente)
7. [Monitoreo y Mantenimiento](#7-monitoreo-y-mantenimiento)
8. [Referencia Rápida: Variables por Cliente](#8-referencia-rápida-variables-por-cliente)

---

## 1. Conexión Administrativa al RDS

Usa el usuario administrador **sólo para tareas de provisionamiento** (crear/eliminar usuarios y esquemas). **Nunca** uses este usuario en el `.env` de producción de ningún cliente.

```bash
# Desde cualquier EC2 con acceso al RDS
psql "host=b2b-platform.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
user=postgres \
dbname=postgres \
port=5432 \
sslmode=require"
```

> **Regla de oro:** `farmacruzdb` es el bisturí, solo se usa en la sala de operaciones. Cada cliente tiene su propio usuario con permisos mínimos.

---

## 2. Dar de Alta un Nuevo Cliente (Tenant)

Sustituye `CLIENTE` por el nombre corto del cliente (ej: `farmacruz`, `distribuidora_mx`, `farmacon`).

### Paso 1 — Ejecutar como administrador (`postgres`)

> [!IMPORTANT]
> **Peculiaridad de AWS RDS:** En RDS, `postgres` es un `rds_superuser`, **no** un superusuario real de PostgreSQL. Esto significa que para crear un esquema y asignárselo a otro usuario con `AUTHORIZATION`, primero debes hacer que `postgres` sea miembro de ese rol. Si omites el `GRANT` previo obtendrás `ERROR: must be member of role "user_CLIENTE"`.

```sql
-- ==============================================================
-- ONBOARDING: Nuevo Tenant
-- Reemplaza 'CLIENTE' con el slug del cliente en minúsculas
-- Ejemplo: farmacruz → user_farmacruz / schema_farmacruz
-- ==============================================================

-- 1. Crear el usuario dedicado para la aplicación del cliente
CREATE USER user_CLIENTE WITH PASSWORD 'password_SEGURO_aqui';

-- 2. ⚠️  FIX RDS: Conceder el rol al admin antes de crear el esquema.
--    En AWS RDS el usuario postgres NO es superusuario real; necesita
--    ser miembro del nuevo rol para poder usar AUTHORIZATION.
GRANT user_CLIENTE TO postgres;

-- 3. Crear el esquema como propiedad del usuario del cliente
CREATE SCHEMA schema_CLIENTE AUTHORIZATION user_CLIENTE;

-- 4. Asegurar que el público no tenga acceso (salvaguarda por tenant)
REVOKE ALL ON SCHEMA public FROM public;

-- 5. Permitir conexión a la base de datos
GRANT CONNECT ON DATABASE postgres TO user_CLIENTE;

-- 6. Darle control total únicamente sobre su propio esquema
GRANT ALL PRIVILEGES ON SCHEMA schema_CLIENTE TO user_CLIENTE;

-- 7. Permisos automáticos para objetos futuros (tablas, secuencias)
--    Sin esto, tablas creadas después del GRANT inicial no serían accesibles.
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_CLIENTE
    GRANT ALL ON TABLES TO user_CLIENTE;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_CLIENTE
    GRANT ALL ON SEQUENCES TO user_CLIENTE;

-- 8. Fijar el search_path: el usuario "ve" solo su esquema por defecto
--    → El backend NO necesita prefijos tipo "schema_CLIENTE.productos"
ALTER USER user_CLIENTE SET search_path TO schema_CLIENTE;
```

### Paso 2 — Cargar las tablas del cliente

Luego de crear el usuario, conecta **como ese usuario** y ejecuta el script de inicialización (ver [Sección 5](#5-script-de-inicialización-de-tablas-botón-de-deploy)):

```bash
psql "host=b2b-platform.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
user=user_CLIENTE \
dbname=postgres \
port=5432 \
sslmode=require" \
-f database/tenant_init.sql
```

---

## 3. Configurar el .env del Servidor del Cliente

Cada cliente tiene su propia **instancia EC2** con su propio `.env`. El backend (FastAPI) no necesita cambios de código gracias al `search_path`.

```bash
# En la EC2 del cliente:
nano ~/farmacruz-ecomerce/backend/.env
```

```ini
# ─── Conexión RDS ────────────────────────────────────────────
DATABASE_URL=postgresql://user_CLIENTE:password_SEGURO_aqui@b2b-platform.ccn22ys0s7ya.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=require

# ─── JWT ─────────────────────────────────────────────────────
# Genera uno único por cliente: openssl rand -hex 32
SECRET_KEY=genera_uno_unico_por_cliente

# ─── CORS ────────────────────────────────────────────────────
ALLOWED_ORIGINS=https://cloudfront-del-cliente.cloudfront.net,http://localhost:3000
FRONTEND_URL=https://cloudfront-del-cliente.cloudfront.net

# ─── Entorno ─────────────────────────────────────────────────
ENVIRONMENT=production
```

> **Nota:** `dbname=postgres` es correcto. La separación de datos es por **esquema** (schema), no por base de datos. El `search_path` configurado en SQL garantiza que todas las queries vayan al esquema correcto automáticamente.

---

## 4. Verificar el Aislamiento

Conecta como el nuevo usuario y confirma que solo ve su esquema:

```bash
psql "host=b2b-platform.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
user=user_CLIENTE \
dbname=postgres \
port=5432 \
sslmode=require"
```

```sql
-- ¿Qué esquema estoy viendo?
SHOW search_path;
-- Resultado esperado: schema_CLIENTE

-- ¿Veo tablas de otros clientes? (debe estar vacío o solo mostrar las del propio esquema)
SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');

-- ¿Puedo conectarme al esquema de otro cliente? (debe fallar con permission denied)
SET search_path TO schema_OTRO_CLIENTE;
SELECT * FROM productos;  -- ❌ Debe arrojar error de permisos
```

---

## 5. Script de Inicialización de Tablas (Botón de Deploy)

Crea el archivo `database/tenant_init.sql`. Este script se ejecuta **como el usuario del cliente**, por lo que las tablas se crean automáticamente en su esquema.

```bash
# En tu máquina local o en la EC2 del cliente
nano ~/farmacruz-ecomerce/database/tenant_init.sql
```

```sql
-- ==============================================================
-- tenant_init.sql — Estructura base para un nuevo cliente
-- Se ejecuta como user_CLIENTE → todo va al schema_CLIENTE
-- ==============================================================

-- Categorías de producto
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Catálogo de productos
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(100) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    price           NUMERIC(10, 2) NOT NULL DEFAULT 0,
    stock           INTEGER NOT NULL DEFAULT 0,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios internos (admins, vendedores, marketing)
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(50) NOT NULL DEFAULT 'seller',  -- admin | marketing | seller
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Grupos de ventas y marketing
CREATE TABLE IF NOT EXISTS salesgroups (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS groupsellers (
    id           SERIAL PRIMARY KEY,
    salesgroup_id INTEGER REFERENCES salesgroups(id) ON DELETE CASCADE,
    user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS groupmarketingmanagers (
    id           SERIAL PRIMARY KEY,
    salesgroup_id INTEGER REFERENCES salesgroups(id) ON DELETE CASCADE,
    user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- Clientes del negocio (compradores B2B)
CREATE TABLE IF NOT EXISTS customers (
    id           SERIAL PRIMARY KEY,
    code         VARCHAR(100) NOT NULL UNIQUE,
    name         VARCHAR(255) NOT NULL,
    is_active    BOOLEAN DEFAULT TRUE,
    salesgroup_id INTEGER REFERENCES salesgroups(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customerinfo (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    email       VARCHAR(255),
    phone       VARCHAR(50),
    address     TEXT
);

-- Listas de precios
CREATE TABLE IF NOT EXISTS pricelists (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pricelistitems (
    id            SERIAL PRIMARY KEY,
    pricelist_id  INTEGER REFERENCES pricelists(id) ON DELETE CASCADE,
    product_id    INTEGER REFERENCES products(id) ON DELETE CASCADE,
    price         NUMERIC(10, 2) NOT NULL,
    UNIQUE(pricelist_id, product_id)
);

-- Órdenes
CREATE TABLE IF NOT EXISTS orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status       VARCHAR(50) DEFAULT 'pending',  -- pending | confirmed | shipped | cancelled
    total        NUMERIC(12, 2) DEFAULT 0,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orderitems (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity   INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- Carrito temporal
CREATE TABLE IF NOT EXISTS cartcache (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity    INTEGER NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(customer_id, product_id)
);

-- Recomendaciones de producto (IA de similitud)
CREATE TABLE IF NOT EXISTS product_recommendations (
    product_id            INTEGER REFERENCES products(id) ON DELETE CASCADE,
    recommended_product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    score                 FLOAT NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, recommended_product_id)
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer   ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orderitems_order  ON orderitems(order_id);
```

---

## 6. Limpieza o Baja de un Cliente

Conecta como administrador (`farmacruzdb`) para eliminar completamente a un tenant:

```sql
-- ⚠️  IRREVERSIBLE — Hacer backup primero (ver Sección 7)

-- 1. Eliminar el esquema y TODO su contenido
DROP SCHEMA schema_CLIENTE CASCADE;

-- 2. Eliminar el usuario
DROP USER user_CLIENTE;
```

### Backup antes de dar de baja

```bash
# Desde EC2 — Respalda SOLO el esquema del cliente
pg_dump -h b2b-platform.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
        -U farmacruzdb \
        -d postgres \
        -n schema_CLIENTE \
        -F c \
        -f "backup_CLIENTE_$(date +%F).dump"

# Para restaurar después (si fuera necesario):
pg_restore -h <HOST_RDS> -U farmacruzdb -d postgres \
           -n schema_CLIENTE "backup_CLIENTE_FECHA.dump"
```

---

## 7. Monitoreo y Mantenimiento

### Ver el tamaño de cada esquema (cliente)

```sql
-- Conectado como farmacruzdb
SELECT
    schemaname                                    AS cliente,
    pg_size_pretty(
        SUM(pg_total_relation_size(schemaname || '.' || tablename))::bigint
    )                                             AS tamaño_total
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'public')
GROUP BY schemaname
ORDER BY SUM(pg_total_relation_size(schemaname || '.' || tablename)) DESC;
```

### Ver todos los usuarios y sus esquemas

```sql
SELECT usename AS usuario, usesuper AS es_admin
FROM pg_catalog.pg_user
ORDER BY usename;
```

### Número de conexiones activas por usuario

```sql
SELECT usename, count(*) AS conexiones_activas
FROM pg_stat_activity
WHERE state = 'active'
GROUP BY usename
ORDER BY conexiones_activas DESC;
```

### ¿Cuándo crecer (Scale Up)?

| Indicador                | Umbral de alerta      | Acción                                       |
| :----------------------- | :-------------------- | :-------------------------------------------- |
| **CPU RDS**        | > 80% sostenido       | Subir a `db.t3.small`                       |
| **FreeableMemory** | < 100 MB              | Subir instancia o reducir `max_connections` |
| **Storage**        | > 90% del disco       | Activar Storage Autoscaling en AWS Console    |
| **Conexiones**     | > 15–18 simultáneas | Añadir `PgBouncer` o subir instancia       |

---

## 8. Referencia Rápida: Variables por Cliente

Usa esta tabla para registrar las credenciales de cada tenant (guárdala en tu gestor de contraseñas, **no** en el repositorio):

| Slug cliente  | Usuario BD         | Esquema BD           | EC2 IP / Hostname      |
| :------------ | :----------------- | :------------------- | :--------------------- |
| `farmacruz` | `user_farmacruz` | `schema_farmacruz` | `ec2-xx-xx-xx-xx...` |
| `SIGUIENTE` | `user_SIGUIENTE` | `schema_SIGUIENTE` | `ec2-xx-xx-xx-xx...` |

> **Genera contraseñas seguras con:** `openssl rand -base64 24`
