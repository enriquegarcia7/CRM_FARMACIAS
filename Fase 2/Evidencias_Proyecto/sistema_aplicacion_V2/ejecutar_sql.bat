@echo off
echo Copiando archivo SQL al contenedor...
docker cp database_schema.sql smartpharm_db:/tmp/database_schema.sql

echo.
echo Ejecutando script SQL en PostgreSQL...
docker exec smartpharm_db psql -U smartpharm_user -d smartpharm_db -f /tmp/database_schema.sql

echo.
echo Verificando tablas creadas...
docker exec smartpharm_db psql -U smartpharm_user -d smartpharm_db -c "\dt"

echo.
echo Proceso completado!
pause
