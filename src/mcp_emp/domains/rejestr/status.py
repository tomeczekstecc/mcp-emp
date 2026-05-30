"""Rejestr status — Polish status identifiers, lifecycle order, alias map.

English input aliases accepted on mutating tools; Polish identifiers always
returned in model output alongside `status_explained` English gloss.
"""

from enum import StrEnum


class Status(StrEnum):
    """EMP rejestr status identifiers (Polish, as returned by the API)."""

    W_EDYCJI = "W_EDYCJI"
    REALIZOWANE = "REALIZOWANE"
    DO_OCENY = "DO_OCENY"
    ZAKONCZONE = "ZAKOŃCZONE"
    ODRZUCONE = "ODRZUCONE"
    WYCOFANE = "WYCOFANE"


# English alias → canonical Polish identifier (case-insensitive key lookup)
ALIAS_MAP: dict[str, Status] = {
    "draft": Status.W_EDYCJI,
    "w_edycji": Status.W_EDYCJI,
    "in_progress": Status.REALIZOWANE,
    "realizowane": Status.REALIZOWANE,
    "pending_review": Status.DO_OCENY,
    "do_oceny": Status.DO_OCENY,
    "completed": Status.ZAKONCZONE,
    "zakonczone": Status.ZAKONCZONE,
    "zakończone": Status.ZAKONCZONE,
    "rejected": Status.ODRZUCONE,
    "odrzucone": Status.ODRZUCONE,
    "withdrawn": Status.WYCOFANE,
    "wycofane": Status.WYCOFANE,
}

STATUS_GLOSS: dict[Status, str] = {
    Status.W_EDYCJI: "draft",
    Status.REALIZOWANE: "in progress",
    Status.DO_OCENY: "pending review",
    Status.ZAKONCZONE: "completed",
    Status.ODRZUCONE: "rejected",
    Status.WYCOFANE: "withdrawn",
}


def resolve_status(value: str) -> Status | None:
    """Return the canonical Status for an English alias or Polish identifier.

    Returns None when the value is not recognised.
    """
    return ALIAS_MAP.get(value.lower().strip())
