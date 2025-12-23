FROM postgres:15-alpine

# Solo copiar el archivo de inicialización v2
COPY db_init_v2.sql /docker-entrypoint-initdb.d/01-init.sql