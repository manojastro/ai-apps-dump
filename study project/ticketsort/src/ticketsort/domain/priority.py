"""ITIL priority matrix — code decides, never the LLM."""

from ticketsort.domain.models import Priority

_MATRIX: dict[tuple[int, int], Priority] = {
    (1, 1): Priority.P1,
    (1, 2): Priority.P2,
    (1, 3): Priority.P3,
    (2, 1): Priority.P2,
    (2, 2): Priority.P3,
    (2, 3): Priority.P4,
    (3, 1): Priority.P3,
    (3, 2): Priority.P4,
    (3, 3): Priority.P5,
}


def compute_priority(impact: int, urgency: int) -> Priority:
    """Map impact x urgency (1=high) to P1-P5.

    Standard 3x3 ITIL matrix you know from service desk:
      1x1=P1, 1x2=P2, 1x3=P3,
      2x1=P2, 2x2=P3, 2x3=P4,
      3x1=P3, 3x2=P4, 3x3=P5.
    Raise ValueError for values outside 1-3.
    """
    try:
        return _MATRIX[(impact, urgency)]
    except KeyError:
        raise ValueError(f"impact and urgency must be 1-3, got {impact},{urgency}") from None
