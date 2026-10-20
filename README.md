# BricoLoop

API de prêt d'outils entre voisins, réalisée avec Python et FastAPI.

## Installation et lancement

Python 3.10 ou supérieur.

```bash
cd API
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Copier .env.example vers .env et régler la connexion MySQL
python -m app.init_db
python -m uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Vérifications

```bash
python -m ruff check . --output-format concise

python -m pytest -q
```

Contrôle complet : `python -m ruff check . && python -m pytest -q`.

## Équipe et suivi Scrum

Membres, rotation PO/SM, stories validées et numéros des PR : à compléter par l'équipe.
Lien de la vidéo : à ajouter au rendu.

## Base BricoLoop

Le backend FastAPI est dans `API/`, indépendant du projet Java/Spring.
Connexion MySQL configurée dans `API/.env` (hors Git).
Tables : `utilisateur`, `outil`, `location`, avec les contraintes du schéma fourni.
L'initialisation ajoute 4 utilisateurs, 8 outils et 3 locations si les tables sont vides.
Elle ne supprime aucune table et conserve les données existantes.
Les anciennes tables `users` et `tools`, si présentes, ne sont plus utilisées.
Une base déjà créée doit avoir le schéma fourni : `create_all` ne modifie pas les colonnes existantes.

Routes : `GET /api/tools`, `GET /api/tools/{id}`, `GET /health`.
Le détail inclut `owner.firstName` et `owner.district` ; `description` peut être `null`.
Les routes des locations ne font pas partie des US-01 et US-03.
Les tests se lancent depuis `API/` et utilisent SQLite, sans modifier MySQL.

## US-02 : proposer un outil

`POST /api/tools` avec l'en-tête `X-User-Id` d'un utilisateur existant.
Le serveur attribue le propriétaire et le statut `available`, puis renvoie `201`.
Nom obligatoire (2 à 60 caractères après suppression des espaces aux extrémités),
catégorie autorisée, description facultative (300 caractères maximum).
Une erreur renvoie `400` avec le champ concerné ; propriétaire, statut et identifiant
ne doivent pas être envoyés dans le corps. Les autres routes conservent leurs codes.

```bash
curl -X POST http://127.0.0.1:8000/api/tools \
  -H 'Content-Type: application/json' -H 'X-User-Id: 2' \
  -d '{"name":"Marteau","category":"Autre","description":"Manche bois"}'
```

Les tables créées par `python -m app.init_db` génèrent automatiquement les identifiants.
Si vous avez importé `bdd/bricoloop.sql` directement sous MySQL/MariaDB, appliquez
`API/migrations/001_outil_auto_increment.mysql.sql` pour activer cette génération.
Cette migration conserve les données.
