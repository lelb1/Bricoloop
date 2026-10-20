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

## US-04 : demander un emprunt

Dans la fiche d'un outil disponible, choisir un profil différent du propriétaire,
puis les dates de début et de fin et cliquer sur « Envoyer la demande ».
`POST /api/tools/{id}/loans` avec `X-User-Id` et
`{"startDate":"2026-12-01","endDate":"2026-12-03"}` crée une location `pending` (201).
Les dates passées (jour courant en Europe/Paris), une fin antérieure au début,
un outil non disponible et son propre outil sont refusés en 400.
Une journée unique est autorisée. Plusieurs demandes pending peuvent coexister ;
la demande ne change pas la disponibilité. Outil inconnu : 404.
Si le schéma a été importé directement sous MySQL, activer la génération des identifiants
avec `API/migrations/003_location_auto_increment.mysql.sql`.

## US-05 : accepter ou refuser une demande

Choisir son profil puis consulter « Demandes reçues pour mes outils ».
Les boutons Accepter et Refuser sont affichés pour les demandes en attente.
`GET /api/loans/received` avec `X-User-Id` liste uniquement les demandes reçues par
le propriétaire courant, avec l’outil, l’emprunteur, les dates et le statut.
`PATCH /api/loans/{id}` avec `{"status":"accepted"}` ou `{"status":"refused"}` :
- seul le propriétaire peut répondre (403 sinon) ;
- accepter passe la location à `accepted` et l’outil à `lent`, dans la même transaction ;
- refuser passe la location à `refused` sans modifier l’outil ;
- toute nouvelle réponse à une demande déjà traitée renvoie 409 ;
- une demande inconnue renvoie 404, une décision invalide 400.

Les lignes sont verrouillées pendant la décision sur MySQL pour éviter deux
réponses concurrentes à la même demande. Les chevauchements sont contrôlés par US-06.

## US-06 : aucun prêt accepté ne se chevauche

Les périodes incluent les deux dates : un prêt du 10 au 15 bloque les demandes
qui touchent ces jours, mais autorise un début le 16.
La création d'une demande et son acceptation vérifient les prêts `accepted` du même
outil ; un chevauchement renvoie 409 sans modifier la demande ni l'outil.
Les demandes `pending`, `refused`, `returned` ne bloquent pas les dates.
Un outil `lent` avec un prêt accepté peut recevoir une demande sur une période libre ;
un outil `unavailable` reste indisponible. Les dates passées restent interdites.
Le front propose donc les dates pour les outils disponibles ou prêtés.
Les opérations verrouillent d'abord l'outil puis les locations dans une transaction,
pour empêcher deux acceptations concurrentes de prêts qui se chevauchent sous MySQL.

## US-07 : déclarer le retour

Dans « Demandes reçues pour mes outils », le propriétaire clique sur « Déclarer le retour »
pour un prêt accepté. `PATCH /api/loans/{id}/return` avec `X-User-Id` (sans corps)
passe le prêt à `returned` et l’outil à `available` dans la même transaction.
Autre utilisateur : 403 ; prêt inconnu : 404 ; prêt non accepté ou déjà rendu : 409.
Les verrous suivent le même ordre que les acceptations (outil, puis location).
Un prêt rendu ne bloque plus les demandes sur ses anciennes dates.

## US-08 : mes emprunts

`GET /api/loans/mine` avec `X-User-Id` retourne uniquement les demandes et prêts
de cet utilisateur, triés par date de début croissante. Le front les affiche dans
« Mes emprunts » avec le nom de l’outil, les dates et le statut.

## US-09 : parcours web intégré

FastAPI sert aussi le site : ouvrir http://localhost:8000/ après avoir lancé l'API.
Un seul serveur suffit ; le port 5500 reste utilisable. Le parcours est : choisir
un profil → catalogue → fiche → dates → demande, avec erreurs API affichées en clair.
Le JavaScript du site est dans `front/bricoloop/catalogue.js`.
Tests du front : `cd front/bricoloop && npm install && npm run check`.

## US-10 : filtre catégorie

`GET /api/tools?category=Jardinage` filtre en base et conserve les disponibles en premier.
Catégorie inconnue : 400. Le sélecteur du site appelle ce filtre API.
