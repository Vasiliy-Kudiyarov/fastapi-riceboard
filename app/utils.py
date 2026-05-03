def compute_rice(reach: float, impact: float, confidence: float, effort: float) -> float:
    """RICE = Reach × Impact × (Confidence / 100) / Effort."""
    return (reach * impact * confidence / 100) / effort
