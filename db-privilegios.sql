-- Se ejecuta tras db.sql (01-schema.sql), solo en la primera creacion de la BD.
-- Minimo privilegio: la API solo necesita DML.
REVOKE ALL PRIVILEGES ON webapps.* FROM 'udbwebaps'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON webapps.* TO 'udbwebaps'@'%';
FLUSH PRIVILEGES;
