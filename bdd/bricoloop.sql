-- BricoLoop : schéma + données de démo
-- 3 tables : utilisateur, outil, location
-- Compatible SQLite / PostgreSQL / MySQL (types simples)

DROP TABLE IF EXISTS location;
DROP TABLE IF EXISTS outil;
DROP TABLE IF EXISTS utilisateur;

-- Un seul type d'utilisateur : il peut être propriétaire ET emprunteur
CREATE TABLE utilisateur (
  id        INTEGER PRIMARY KEY,
  firstName VARCHAR(60)  NOT NULL,
  district  VARCHAR(60)  NOT NULL      -- quartier
);

CREATE TABLE outil (
  id          INTEGER PRIMARY KEY,
  ownerId     INTEGER      NOT NULL,   -- propriétaire
  name        VARCHAR(60)  NOT NULL CHECK (LENGTH(name) BETWEEN 2 AND 60),
  category    VARCHAR(20)  NOT NULL CHECK (category IN
              ('Perçage','Jardinage','Peinture','Nettoyage','Mesure','Autre')),
  description VARCHAR(300),
  status      VARCHAR(20)  NOT NULL DEFAULT 'available'
              CHECK (status IN ('available','lent','unavailable')),
  FOREIGN KEY (ownerId) REFERENCES utilisateur(id)
);

CREATE TABLE location (
  id         INTEGER PRIMARY KEY,
  toolId     INTEGER     NOT NULL,
  borrowerId INTEGER     NOT NULL,     -- emprunteur
  startDate  DATE        NOT NULL,     -- AAAA-MM-JJ
  endDate    DATE        NOT NULL,
  status     VARCHAR(20) NOT NULL DEFAULT 'pending'
             CHECK (status IN ('pending','accepted','refused','returned')),
  CHECK (endDate >= startDate),
  FOREIGN KEY (toolId)     REFERENCES outil(id),
  FOREIGN KEY (borrowerId) REFERENCES utilisateur(id)
);

-- Données de démo : 4 voisins
INSERT INTO utilisateur (id, firstName, district) VALUES
  (1, 'Rida',  'Centre'),
  (2, 'Marc',  'Gare'),
  (3, 'Sarah', 'Jardins'),
  (4, 'Lucas', 'Centre');

-- 8 outils, 5 catégories
INSERT INTO outil (id, ownerId, name, category, description, status) VALUES
  (1, 1, 'Perceuse Bosch',      'Perçage',   'Perceuse à percussion 750 W',  'available'),
  (2, 1, 'Tondeuse électrique', 'Jardinage', 'Tondeuse 1200 W',              'available'),
  (3, 2, 'Rouleau de peinture', 'Peinture',  'Rouleau + bac',                'available'),
  (4, 2, 'Nettoyeur haute pression', 'Nettoyage', 'Kärcher 130 bars',        'lent'),
  (5, 3, 'Mètre laser',         'Mesure',    'Portée 40 m',                  'available'),
  (6, 3, 'Taille-haie',         'Jardinage', 'Taille-haie thermique',        'available'),
  (7, 4, 'Visseuse sans fil',   'Perçage',   NULL,                           'available'),
  (8, 4, 'Escabeau 5 marches',  'Autre',     'Aluminium',                    'unavailable');

-- Quelques locations d'exemple
INSERT INTO location (id, toolId, borrowerId, startDate, endDate, status) VALUES
  (1, 4, 1, '2026-10-10', '2026-10-15', 'accepted'),   -- outil 4 prêté
  (2, 1, 2, '2026-10-20', '2026-10-22', 'pending'),
  (3, 6, 1, '2026-09-01', '2026-09-03', 'returned');
