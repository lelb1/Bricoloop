# BricoLoop

API de prêt d'outils entre voisins, réalisée avec Python et FastAPI.

Le code, les tests et la configuration du backend se trouvent dans `API/`.

## Installation et lancement

Python 3.10 ou supérieur.

```bash
cd API
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Adapter les paramètres MySQL dans .env, puis :
python -m app.init_db
python -m uvicorn app.main:app --reload
```

Documentation interactive : http://127.0.0.1:8000/docs

## Vérifications

Depuis le dossier `API`, avec l’environnement virtuel activé :

```bash
python -m ruff check . --output-format concise
python -m pytest -q
```

Contrôle complet : `python -m ruff check . && python -m pytest -q`.

## Équipe et suivi Scrum

Membres, rotation PO/SM, stories validées et numéros des PR : à compléter par l'équipe.
Lien de la vidéo : à ajouter au rendu.

## US-01 et US-03 : catalogue et détail

- `GET /api/tools` : liste JSON, outils `available` en premier ; `[]` si vide.
- `GET /api/tools/{id}` : détail avec `owner.firstName` et `owner.district`.
- Identifiant inconnu : `404` et `{"detail": "Outil introuvable"}`.
- Identifiant non entier : `422` (validation FastAPI).
- `GET /health` : vérification du démarrage.

Les statuts sont `available`, `lent`, `unavailable`.
Les données sont persistées dans MySQL (ou MariaDB), dans la base `bricoloop`.
`python -m app.init_db` crée la base, les tables `users` et `tools`, et ajoute
4 voisins et 8 outils dans 6 catégories uniquement si les deux tables sont vides.
Relancer cette commande conserve les données existantes.
Les changements futurs du schéma nécessiteront des migrations ; `create_all`
ne modifie pas les colonnes des tables existantes.

```bash
curl http://127.0.0.1:8000/api/tools
curl http://127.0.0.1:8000/api/tools/1
curl http://127.0.0.1:8000/api/tools/999
```

Ces stories sont implémentées et testées sur la branche `feature/US-01-03-api`.
Leur statut Done reste soumis à la review de la PR et à la validation du PO.

Référence des tests : https://fastapi.tiangolo.com/tutorial/testing/

## Connexion MySQL

Le serveur doit être lancé avant l'initialisation et le démarrage de l'API.
Configuration dans `API/.env` (ignoré par Git), modèle dans `API/.env.example` :

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_USER=root` pour le développement local
- `DB_PASSWORD=` à renseigner selon votre installation
- `DB_NAME=bricoloop`

Le compte utilisé pour l'initialisation doit pouvoir créer la base et les tables.
Les routes utilisent SQLAlchemy et PyMySQL. Le catalogue est trié en SQL ; le détail
charge le propriétaire depuis la relation `tools.ownerId → users.id`.
`GET /health` vérifie la connexion SQL ; une panne SQL renvoie `503`, sans identifiants.
Les tests automatiques utilisent une base SQLite isolée, sans modifier MySQL.

Documentation du pilote : https://docs.sqlalchemy.org/en/20/dialects/mysql.html#pymysql
