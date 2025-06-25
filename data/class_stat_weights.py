CLASS_STAT_WEIGHTS = {
    "Harcos": {
        "statok": {
            "Erő": (13, 18),
            "Állóképesség": (9, 18),
            "Gyorsaság": (8, 18),
            "Ügyesség": (8, 18),
            "Karizma": (8, 18),
            "Egészség": (11, 20),
            "Intelligencia": (3, 18),
            "Akaraterő": (8, 18),
            "Asztrál": (3, 18),
            "Érzékelés": (8, 18),
        },
        "dupla_dobas": ["Karizma", "Intelligencia", "Asztrál"]
    },
    "Gladiátor": {
        "statok": {
            "Erő": (13, 18),
            "Állóképesség": (13, 18),
            "Gyorsaság": (8, 18),
            "Ügyesség": (8, 18),
            "Karizma": (8, 18),
            "Egészség": (11, 20),
            "Intelligencia": (3, 18),
            "Akaraterő": (3, 18),
            "Asztrál": (3, 18),
            "Érzékelés": (8, 18),
        },
        "dupla_dobas": []
    },
    "Fejvadász": {
        "statok": {
            "Erő": (8, 18),
            "Állóképesség": (13, 18),
            "Gyorsaság": (13, 18),
            "Ügyesség": (9, 18),
            "Karizma": (3, 18),
            "Egészség": (11, 20),
            "Intelligencia": (3, 18),
            "Akaraterő": (9, 18),
            "Asztrál": (8, 18),
            "Érzékelés": (13, 18),
        },
        "dupla_dobas": ["Intelligencia"]
    },
    "Lovag": {
        "statok": {
            "Erő": (13, 18),
            "Állóképesség": (9, 18),
            "Gyorsaság": (3, 18),
            "Ügyesség": (3, 18),
            "Karizma": (8, 18),
            "Egészség": (11, 20),
            "Intelligencia": (8, 18),
            "Akaraterő": (9, 18),
            "Asztrál": (3, 18),
            "Érzékelés": (8, 18),
        },
        "dupla_dobas": ["Gyorsaság", "Ügyesség", "Asztrál"]
    },
    "Amazon": {
        "statok": {
            "Erő": (8, 18),
            "Állóképesség": (8, 18),
            "Gyorsaság": (9, 18),
            "Ügyesség": (9, 18),
            "Karizma": (9, 18),
            "Egészség": (8, 18),
            "Intelligencia": (3, 18),
            "Akaraterő": (8, 18),
            "Asztrál": (3, 18),
            "Érzékelés": (9, 18),
        },
        "dupla_dobas": ["Intelligencia", "Asztrál"]
    },
    "Barbár": {
        "statok": {
            "Erő": (15, 20),
            "Állóképesség": (15, 20),
            "Gyorsaság": (9, 18),
            "Ügyesség": (8, 18),
            "Karizma": (3, 18),
            "Egészség": (11, 20),
            "Intelligencia": (3, 18),
            "Akaraterő": (8, 18),
            "Asztrál": (2, 17),
            "Érzékelés": (9, 18),
        },
        "dupla_dobas": ["Karizma"]
    },
    "Bajvívó": {
        "statok": {
            "Erő": (8, 18),
            "Állóképesség": (3, 18),
            "Gyorsaság": (9, 18),
            "Ügyesség": (9, 18),
            "Karizma": (3, 18),
            "Egészség": (3, 18),
            "Intelligencia": (3, 18),
            "Akaraterő": (3, 18),
            "Asztrál": (13, 18),
            "Érzékelés": (9, 18),
        },
        "dupla_dobas": ["Állóképesség", "Karizma", "Intelligencia"]
    },
    "Varázsló": {
        "statok": {
            "Erő": (6, 12),
            "Állóképesség": (6, 12),
            "Gyorsaság": (8, 14),
            "Ügyesség": (10, 16),
            "Karizma": (10, 16),
            "Egészség": (8, 14),
            "Intelligencia": (14, 18),
            "Akaraterő": (14, 18),
            "Asztrál": (14, 18),
            "Érzékelés": (10, 16),
        },
        "dupla_dobas": ["Intelligencia", "Asztrál"]
    },
    # stb.
}

UPGRADABLE_STATS = {
    "Harcos": ["Erő", "Állóképesség", "Ügyesség", "Gyorsaság"],
    "Gladiátor": ["Erő", "Állóképesség", "Ügyesség", "Gyorsaság"],
    "Fejvadász": ["Állóképesség", "Gyorsaság"],
    "Varázsló": ["Intelligencia", "Asztrál"],
    "Tolvaj": ["Gyorsaság", "Ügyesség", "Érzékelés"]
}