"""
Skill Editor Constants and Mappings
Contains all constant values used in the skill editor
"""

# Skill categories
CATEGORIES = {
    "Harci képzettségek": ["Közkeletű", "Szakértő", "Titkos"],
    "Szociális képzettségek": ["Általános", "Nemesi", "Polgári", "Póri", "Művész"],
    "Alvilági képzettségek": ["Álcázó", "Kommunikációs", "Pénzszerző", "Harci", "Behatoló", "Ellenálló"],
    "Túlélő képzettségek": ["Vadonjáró", "Atlétikai"],
    "Elméleti képzettségek": ["Közkeletű", "Szakértő", "Titkos elméleti", "Titkos szervezeti"],
    "Helyfoglaló képzettségek": ["Harci képzettségek", "Szociális képzettségek", "Alvilági képzettségek", 
                                  "Túlélő képzettségek", "Elméleti képzettségek"]
}

# Acquisition method mappings
ACQ_METHOD_MAP = {1: "Gyakorlás", 2: "Tapasztalás", 3: "Tanulás"}
ACQ_METHOD_MAP_REV = {v: k for k, v in ACQ_METHOD_MAP.items()}

# Acquisition difficulty mappings
ACQ_DIFF_MAP = {1: "Egyszerű", 2: "Könnyű", 3: "Közepes", 4: "Nehéz", 5: "Szinte lehetetlen"}
ACQ_DIFF_MAP_REV = {v: k for k, v in ACQ_DIFF_MAP.items()}

# Type mappings
TYPE_MAP = {1: "szint", 2: "%"}
TYPE_MAP_REV = {v: k for k, v in TYPE_MAP.items()}
