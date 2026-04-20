FROM postgres:15-alpine

# Solo copiar el archivo de inicialización
COPY db_init.sql /docker-entrypoint-initdb.d/01-init.sql