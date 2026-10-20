from app.models import Tool, User


def seed_users() -> list[User]:
    return [
        User(id=1, firstName="Bilal", district="Centre"),
        User(id=2, firstName="Sarah", district="Gare"),
        User(id=3, firstName="Amine", district="Nord"),
        User(id=4, firstName="Lina", district="Sud"),
    ]


def seed_tools() -> list[Tool]:
    rows = [
        (1, 1, "Perceuse", "Perçage", "Perceuse avec forets", "lent"),
        (2, 2, "Taille-haie", "Jardinage", "Taille-haie électrique", "available"),
        (3, 3, "Rouleau", "Peinture", "Rouleau pour les murs", "available"),
        (4, 4, "Nettoyeur", "Nettoyage", "Nettoyeur haute pression", "unavailable"),
        (5, 1, "Niveau", "Mesure", "Niveau à bulle", "available"),
        (6, 2, "Ponceuse", "Autre", "Ponceuse avec abrasifs", "available"),
        (7, 3, "Visseuse", "Perçage", "Visseuse sans fil", "lent"),
        (8, 4, "Sécateur", "Jardinage", "Sécateur manuel", "available"),
    ]
    return [
        Tool(id=i, ownerId=o, name=n, category=c, description=d, status=s)
        for i, o, n, c, d, s in rows
    ]
