-- À appliquer seulement si la colonne etat est absente.
ALTER TABLE outil ADD COLUMN etat VARCHAR(300) NULL;
