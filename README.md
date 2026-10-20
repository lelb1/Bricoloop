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

## US-03 : détail d'un outil — identifiant inconnu

`GET /api/tools/{id}` renvoie `404` si aucun outil ne possède cet identifiant,
y compris un identifiant absent entre deux identifiants existants.
Corps de la réponse : `{"detail":"Outil introuvable"}`.
Un identifiant non entier reste une erreur de format `422`.
La réponse `404` est documentée dans Swagger (`/docs`).

## US-03 : contenu de la fiche outil

`GET /api/tools/4` renvoie par exemple :

```json
{
  "id": 4,
  "ownerId": 2,
  "name": "Nettoyeur haute pression",
  "category": "Nettoyage",
  "description": "Kärcher 130 bars",
  "status": "lent",
  "owner": {"id": 2, "firstName": "Marc", "district": "Gare"}
}
```

Le prénom et le quartier correspondent au propriétaire de l'outil demandé.
La fiche est disponible pour les trois statuts ; une description absente vaut `null`.

## Front connecté à la base

Lancer FastAPI sur le port 8000, puis depuis la racine du dépôt, dans un autre terminal :

```bash
python3 -m http.server 5500 --directory front/bricoloop
```

Ouvrir http://localhost:5500/bricoloop-catalogue.html (pas directement en fichier local).
La page charge automatiquement `GET /api/tools`, sans données statiques de secours.
« Actualiser » recharge la base ; « Voir le détail » appelle `GET /api/tools/{id}`.
Les origines localhost et 127.0.0.1 sur le port 5500 sont autorisées par CORS.

## Ajout depuis le front et état physique

Choisir son profil, puis cliquer sur « Proposer un outil ». Le formulaire envoie
`POST /api/tools` avec `X-User-Id` et recharge le catalogue après ajout.
Les profils viennent de `GET /api/users`. Le champ facultatif `etat` (300 caractères maximum)
est affiché dans le catalogue et la fiche ; les anciens outils affichent « Non renseigné ».
Pour une base existante, appliquer `API/migrations/002_outil_etat.mysql.sql` seulement
si la colonne `etat` est absente. L’état physique et le statut de disponibilité sont distincts.

## Modifier l’état physique

Sélectionner le profil du propriétaire, ouvrir la fiche de son outil, modifier
l’état dans la popup et cliquer sur « Enregistrer l’état ».
`PATCH /api/tools/{id}/etat` avec `X-User-Id` et `{"etat":"Bon état"}`
sauvegarde en base. Seul le propriétaire peut modifier (403 sinon),
identifiant inconnu : 404, champ invalide : 400 ; maximum 300 caractères.
Le champ peut être vidé (`null`) sans modifier la disponibilité.
