# utils/colors.py
from utils.constants import FORCE_THRESHOLDS, FORCE_COLORS

def get_color_for_force(force):
    if force < FORCE_THRESHOLDS["LOW"]:
        return FORCE_COLORS["LOW"]
    if force < FORCE_THRESHOLDS["MEDIUM"]:
        return FORCE_COLORS["MEDIUM"]
    return FORCE_COLORS["HIGH"]
