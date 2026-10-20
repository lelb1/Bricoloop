-- BricoLoop : création des 3 tables
-- Un seul type d'utilisateur, qui joue 2 rôles dans une location :
--   id_proprietaire = celui qui loue son outil
--   id_locataire    = celui qui emprunte l'outil

CREATE TABLE utilisateur (
  id      INTEGER PRIMARY KEY,
  prenom  VARCHAR(60) NOT NULL,
  quartier VARCHAR(60) NOT NULL
);

CREATE TABLE outil (
  id              INTEGER PRIMARY KEY,
  id_proprietaire INTEGER     NOT NULL,
  nom             VARCHAR(60) NOT NULL,
  categorie       VARCHAR(20) NOT NULL CHECK (categorie IN
                  ('Perçage','Jardinage','Peinture','Nettoyage','Mesure','Autre')),
  description     VARCHAR(300),
  statut          VARCHAR(20) NOT NULL DEFAULT 'disponible'
                  CHECK (statut IN ('disponible','prete','indisponible')),
  FOREIGN KEY (id_proprietaire) REFERENCES utilisateur(id)
);

CREATE TABLE location (
  id              INTEGER PRIMARY KEY,
  id_outil        INTEGER     NOT NULL,
  id_proprietaire INTEGER     NOT NULL,
  id_locataire    INTEGER     NOT NULL,
  date_debut      DATE        NOT NULL,
  date_fin        DATE        NOT NULL,
  statut          VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                  CHECK (statut IN ('en_attente','acceptee','refusee','rendue')),
  CHECK (date_fin >= date_debut),
  CHECK (id_proprietaire <> id_locataire),
  FOREIGN KEY (id_outil)        REFERENCES outil(id),
  FOREIGN KEY (id_proprietaire) REFERENCES utilisateur(id),
  FOREIGN KEY (id_locataire)    REFERENCES utilisateur(id)
);
