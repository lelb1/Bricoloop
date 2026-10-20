from datetime import date

from app.models import Tool, User


def seed_users() -> list[User]:
    return [
        User(id=1, firstName="Rida", district="Centre"),
        User(id=2, firstName="Marc", district="Gare"),
        User(id=3, firstName="Sarah", district="Jardins"),
        User(id=4, firstName="Lucas", district="Centre"),
    ]


def seed_tools() -> list[Tool]:
    rows = [
        (1, 1, "Perceuse Bosch", "Perçage", "Perceuse à percussion 750 W", "available"),
        (2, 1, "Tondeuse électrique", "Jardinage", "Tondeuse 1200 W", "available"),
        (3, 2, "Rouleau de peinture", "Peinture", "Rouleau + bac", "available"),
        (4, 2, "Nettoyeur haute pression", "Nettoyage", "Kärcher 130 bars", "lent"),
        (5, 3, "Mètre laser", "Mesure", "Portée 40 m", "available"),
        (6, 3, "Taille-haie", "Jardinage", "Taille-haie thermique", "available"),
        (7, 4, "Visseuse sans fil", "Perçage", None, "available"),
        (8, 4, "Escabeau 5 marches", "Autre", "Aluminium", "unavailable"),
    ]
    return [
        Tool(id=i, ownerId=o, name=n, category=c, description=d, status=s)
        for i, o, n, c, d, s in rows
    ]


def seed_locations() -> list[dict]:
    rows = [
        (1, 4, 1, "2026-10-10", "2026-10-15", "accepted"),
        (2, 1, 2, "2026-10-20", "2026-10-22", "pending"),
        (3, 6, 1, "2026-09-01", "2026-09-03", "returned"),
    ]
    return [
        dict(
            id=i,
            toolId=t,
            borrowerId=b,
            startDate=date.fromisoformat(start),
            endDate=date.fromisoformat(end),
            status=status,
        )
        for i, t, b, start, end, status in rows
    ]
