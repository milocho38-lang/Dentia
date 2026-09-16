from __future__ import annotations


STRUCTURED_ONLY_NOTE = "Evolución ortodóncica estructurada."


def visible_orthodontic_evolution_notes(value: str | None) -> str | None:
    return None if value == STRUCTURED_ONLY_NOTE else value


def compose_orthodontic_evolution_text(
    performed_summary: str | None,
    notes: str | None,
) -> str | None:
    """Present legacy fields as one deterministic narrative without mutation."""
    parts = [
        value
        for value in (
            performed_summary,
            visible_orthodontic_evolution_notes(notes),
        )
        if value
    ]
    return "\n\n".join(parts) or None
