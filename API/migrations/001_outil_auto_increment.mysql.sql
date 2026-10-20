-- Seulement si outil a été créée avec bdd/bricoloop.sql sous MySQL/MariaDB.
-- Conserve les identifiants et les données existantes.
ALTER TABLE outil MODIFY COLUMN id INTEGER NOT NULL AUTO_INCREMENT;
