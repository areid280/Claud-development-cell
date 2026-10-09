"""Canonical part labels shared by parsing trials and the s03_parse stage."""

from __future__ import annotations

# Fixed preview colour per canonical label (labels come from config stages.s03_parse.labels).
LABEL_COLORS = {
    "background": (0, 0, 0),
    "hair": (80, 40, 20),
    "face": (255, 200, 170),
    "skin": (240, 160, 120),
    "neck": (220, 140, 110),
    "upper_clothes": (40, 110, 220),
    "lower_clothes": (30, 70, 180),
    "dress": (200, 40, 150),
    "bodysuit": (160, 30, 120),
    "jacket": (30, 160, 220),
    "gloves": (240, 220, 30),
    "belt": (130, 80, 40),
    "collar": (80, 220, 220),
    "hat": (180, 120, 40),
    "shoes": (80, 80, 80),
    "boots": (50, 50, 50),
    "socks_stockings": (220, 100, 170),
    "bag": (100, 180, 70),
    "accessory": (250, 100, 30),
}
