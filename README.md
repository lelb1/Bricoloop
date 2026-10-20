# BricoLoop

API de prêt d'outils entre voisins, réalisée avec Python et FastAPI.

## Installation et lancement

Python 3.10 ou supérieur.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
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

## US-01 et US-03 : catalogue et détail

- `GET /api/tools` : liste JSON, outils `available` en premier ; `[]` si vide.
- `GET /api/tools/{id}` : détail avec `owner.firstName` et `owner.district`.
- Identifiant inconnu : `404` et `{"detail": "Outil introuvable"}`.
- Identifiant non entier : `422` (validation FastAPI).
- `GET /health` : vérification du démarrage.

Les statuts sont `available`, `lent`, `unavailable`.
4 voisins et 8 outils dans 6 catégories sont chargés en mémoire par application.
Les données ne sont pas persistées ; aucun serveur de base de données n'est requis.

```bash
curl http://127.0.0.1:8000/api/tools
curl http://127.0.0.1:8000/api/tools/1
curl http://127.0.0.1:8000/api/tools/999
```

Ces stories sont implémentées et testées sur la branche `feature/US-01-03-api`.
Leur statut Done reste soumis à la review de la PR et à la validation du PO.

Référence des tests : https://fastapi.tiangolo.com/tutorial/testing/
