"""Signer policy helpers for C019A.4 electronic consent flows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agenda import Patient, PatientResponsible
from app.models.consent_template import ConsentInstance, ConsentResponsibleAdult, ConsentTemplateVersion, ConsentLibraryDocument, ConsentLibraryVersion
from app.services.patient_service import calculate_age

PATIENT_SELF = "PATIENT_SELF"
PATIENT_OR_RESPONSIBLE_ADULT = "PATIENT_OR_RESPONSIBLE_ADULT"
RESPONSIBLE_ADULT_REQUIRED = "RESPONSIBLE_ADULT_REQUIRED"
NO_PATIENT_SIGNATURE = "NO_PATIENT_SIGNATURE"
SPECIAL_WORKFLOW = "SPECIAL_WORKFLOW"
RESPONSIBLE_ADULT = "RESPONSIBLE_ADULT"

ELECTRONIC_CONSENT_SIGNER_POLICIES = {PATIENT_SELF, PATIENT_OR_RESPONSIBLE_ADULT, RESPONSIBLE_ADULT_REQUIRED}
NON_STANDARD_SIGNER_POLICIES = {NO_PATIENT_SIGNATURE, SPECIAL_WORKFLOW}
VALID_SIGNER_ACTORS = {PATIENT_SELF, RESPONSIBLE_ADULT}

LEGACY_SIGNER_POLICY_MAP = {
    "ADULT_SELF": PATIENT_SELF,
    "ADULT_OR_REPRESENTATIVE": PATIENT_OR_RESPONSIBLE_ADULT,
    "REPRESENTATIVE_REQUIRED": RESPONSIBLE_ADULT_REQUIRED,
    "NO_SIGNATURE_REQUIRED": NO_PATIENT_SIGNATURE,
    "ADMINISTRATIVE_RECORD": NO_PATIENT_SIGNATURE,
    "NO_SIGNATURE": NO_PATIENT_SIGNATURE,
    "FUTURE_WORKFLOW": SPECIAL_WORKFLOW,
}

RESPONSIBLE_RELATIONSHIPS = {
    "MOTHER",
    "FATHER",
    "SIBLING",
    "GRANDPARENT",
    "AUNT_UNCLE",
    "COUSIN",
    "CAREGIVER",
    "NEIGHBOR",
    "LEGAL_REPRESENTATIVE",
    "OTHER",
}

MINOR_PARTICIPATION_OPTIONS = {
    "INFORMED_AND_AGREED",
    "INFORMED_NO_OBJECTION",
    "COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION",
    "NOT_APPLICABLE",
    "OTHER",
}

RELATIONSHIP_LABELS = {
    "MOTHER": "Madre",
    "FATHER": "Padre",
    "SIBLING": "Hermano/a",
    "GRANDPARENT": "Abuelo/a",
    "AUNT_UNCLE": "Tío/a",
    "COUSIN": "Primo/a",
    "CAREGIVER": "Cuidador/a",
    "NEIGHBOR": "Vecino/a",
    "LEGAL_REPRESENTATIVE": "Representante legal",
    "OTHER": "Otro",
}

MINOR_PARTICIPATION_LABELS = {
    "INFORMED_AND_AGREED": "Informado y de acuerdo",
    "INFORMED_NO_OBJECTION": "Informado, sin manifestar oposición",
    "COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION": "No fue posible obtener manifestación por edad o condición",
    "NOT_APPLICABLE": "No aplica",
    "OTHER": "Otro",
}


def responsible_relationship_label(value: str | None, other: str | None = None) -> str | None:
    """Return a patient-facing label while preserving the canonical enum elsewhere."""
    if not value:
        return None
    label = RELATIONSHIP_LABELS.get(value, "Relación no especificada")
    clean_other = _clean(other)
    if value == "OTHER" and clean_other:
        return f"{label}: {clean_other}"
    return label


def minor_participation_label(value: str | None, observation: str | None = None) -> str | None:
    """Return the sealed minor-participation choice in human-readable Spanish."""
    if not value:
        return None
    label = MINOR_PARTICIPATION_LABELS.get(value, "Participación no especificada")
    clean_observation = _clean(observation)
    if value == "OTHER" and clean_observation:
        return f"{label}: {clean_observation}"
    return label


@dataclass(frozen=True)
class SignerSnapshot:
    actor_type: str
    policy: str
    full_name: str
    document_type: str | None
    document_number: str | None
    email: str
    phone: str | None
    relationship_type: str | None = None
    relationship_other: str | None = None
    responsible_adult_id: UUID | None = None
    minor_participation_status: str | None = None
    minor_participation_observation: str | None = None

    @property
    def recipient_masked(self) -> str:
        local, domain = self.email.split("@", 1)
        return f"{local[:1]}***@{domain}"

    @property
    def relationship_label(self) -> str | None:
        return responsible_relationship_label(self.relationship_type, self.relationship_other)


def canonical_signer_policy(value: str | None) -> str:
    value = (value or PATIENT_SELF).strip().upper()
    return LEGACY_SIGNER_POLICY_MAP.get(value, value)


def signer_policy_from_library_version(session: Session, version: ConsentTemplateVersion | None) -> str:
    if version is None or not version.source_library_version_id:
        return PATIENT_SELF
    library_version = session.get(ConsentLibraryVersion, version.source_library_version_id)
    if not library_version:
        return PATIENT_SELF
    signer_policy: str | None = None
    for note in library_version.transformation_notes or []:
        if isinstance(note, str) and note.startswith("signer_compatibility="):
            signer_policy = canonical_signer_policy(note.split("=", 1)[1])
        if isinstance(note, dict):
            raw = note.get("signer_compatibility") or note.get("flow_classification")
            if raw:
                signer_policy = canonical_signer_policy(raw)
    if signer_policy:
        return signer_policy
    document = session.get(ConsentLibraryDocument, library_version.library_document_id)
    return canonical_signer_policy(document.signer_scope if document else None)


def _clean(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _patient_full_name(patient: Patient) -> str:
    return f"{patient.first_names} {patient.last_names}".strip()


def resolve_signer_snapshot(session: Session, *, company_id: UUID, patient: Patient, payload_context: Any, policy: str, actor_type: str | None, verified_by_user_id: UUID | None) -> SignerSnapshot:
    policy = canonical_signer_policy(policy)
    if policy in NON_STANDARD_SIGNER_POLICIES:
        raise ValueError("Este documento no hace parte del flujo estándar de consentimiento electrónico.")
    local_today = date.today()
    age = calculate_age(patient.birth_date, local_today)
    is_minor = age is not None and age < 18
    actor = (actor_type or "").strip().upper() or (RESPONSIBLE_ADULT if (policy == RESPONSIBLE_ADULT_REQUIRED or is_minor) else PATIENT_SELF)
    if actor not in VALID_SIGNER_ACTORS:
        raise ValueError("El tipo de firmante no es válido.")
    if policy == PATIENT_SELF and actor != PATIENT_SELF:
        raise ValueError("Esta plantilla solo permite firma del paciente adulto en nombre propio.")
    if policy == RESPONSIBLE_ADULT_REQUIRED and actor != RESPONSIBLE_ADULT:
        raise ValueError("Esta plantilla requiere firma de adulto responsable.")
    if is_minor and actor != RESPONSIBLE_ADULT:
        raise ValueError("Los pacientes menores de edad requieren firma de adulto responsable.")
    if actor == PATIENT_SELF:
        email = _clean(patient.email)
        if not email or "@" not in email:
            raise ValueError("El paciente no tiene un correo válido para firmar electrónicamente.")
        return SignerSnapshot(
            actor_type=PATIENT_SELF,
            policy=policy,
            full_name=_patient_full_name(patient),
            document_type=patient.document_type,
            document_number=patient.document,
            email=email,
            phone=patient.mobile or patient.alternate_phone,
            minor_participation_status="NOT_APPLICABLE",
        )
    responsible_payload = getattr(payload_context, "responsible_adult", None)
    if responsible_payload is None:
        raise ValueError("Debes seleccionar o registrar un adulto responsable antes de preparar el consentimiento.")
    relationship_type = (responsible_payload.relationship_type or "").strip().upper()
    if relationship_type not in RESPONSIBLE_RELATIONSHIPS:
        raise ValueError("El parentesco o relación del adulto responsable no es válido.")
    relationship_other = _clean(responsible_payload.relationship_other)
    if relationship_type == "OTHER" and not relationship_other:
        raise ValueError("Cuando la relación es Otro debes describirla.")
    if relationship_type != "OTHER":
        relationship_other = None
    source_responsible: PatientResponsible | None = None
    if responsible_payload.patient_responsible_id:
        source_responsible = session.scalar(
            select(PatientResponsible).where(
                PatientResponsible.id == responsible_payload.patient_responsible_id,
                PatientResponsible.company_id == company_id,
                PatientResponsible.patient_id == patient.id,
                PatientResponsible.is_active.is_(True),
            )
        )
        if source_responsible is None:
            raise ValueError("El adulto responsable seleccionado no corresponde al paciente.")
    full_name = _clean(responsible_payload.full_name) or (source_responsible.name if source_responsible else None)
    document_type = _clean(responsible_payload.document_type) or (source_responsible.document_type if source_responsible else None)
    document_number = _clean(responsible_payload.document_number) or (source_responsible.document if source_responsible else None)
    email = _clean(responsible_payload.email) or (source_responsible.email if source_responsible else None)
    phone = _clean(responsible_payload.phone) or (source_responsible.mobile if source_responsible else None)
    if not full_name or not document_type or not document_number or not email or "@" not in email or not phone:
        raise ValueError("El adulto responsable debe tener nombre, documento, correo y teléfono.")
    if not getattr(responsible_payload, "identity_verified", False):
        raise ValueError("La clínica debe confirmar la identidad del adulto responsable antes de sellar el consentimiento.")
    minor_status = (getattr(payload_context, "minor_participation_status", None) or "NOT_APPLICABLE").strip().upper()
    if is_minor and minor_status == "NOT_APPLICABLE":
        minor_status = "COULD_NOT_EXPRESS_DUE_TO_AGE_OR_CONDITION"
    if minor_status not in MINOR_PARTICIPATION_OPTIONS:
        raise ValueError("La participación del menor no es válida.")
    minor_observation = _clean(getattr(payload_context, "minor_participation_observation", None))
    if minor_status == "OTHER" and not minor_observation:
        raise ValueError("Describe la participación del menor cuando seleccionas Otro.")
    return SignerSnapshot(
        actor_type=RESPONSIBLE_ADULT,
        policy=policy,
        full_name=full_name,
        document_type=document_type,
        document_number=document_number,
        email=email,
        phone=phone,
        relationship_type=relationship_type,
        relationship_other=relationship_other,
        responsible_adult_id=source_responsible.id if source_responsible else None,
        minor_participation_status=minor_status,
        minor_participation_observation=minor_observation,
    )


def signer_snapshot_from_instance(instance: ConsentInstance) -> SignerSnapshot:
    actor = canonical_signer_policy(getattr(instance, "signer_actor_type", None))
    if actor == PATIENT_SELF:
        return SignerSnapshot(
            actor_type=PATIENT_SELF,
            policy=canonical_signer_policy(getattr(instance, "signer_policy", None)),
            full_name=instance.signer_full_name_snapshot or ((instance.context_snapshot or {}).get("patient") or {}).get("full_name") or "Paciente",
            document_type=instance.signer_document_type_snapshot,
            document_number=instance.signer_document_number_snapshot,
            email=instance.signer_email_snapshot or "",
            phone=instance.signer_phone_snapshot,
            minor_participation_status=instance.minor_participation_status,
            minor_participation_observation=instance.minor_participation_observation,
        )
    return SignerSnapshot(
        actor_type=RESPONSIBLE_ADULT,
        policy=canonical_signer_policy(getattr(instance, "signer_policy", None)),
        full_name=instance.signer_full_name_snapshot or "Adulto responsable",
        document_type=instance.signer_document_type_snapshot,
        document_number=instance.signer_document_number_snapshot,
        email=instance.signer_email_snapshot or "",
        phone=instance.signer_phone_snapshot,
        relationship_type=instance.signer_relationship_type_snapshot,
        relationship_other=instance.signer_relationship_other_snapshot,
        minor_participation_status=instance.minor_participation_status,
        minor_participation_observation=instance.minor_participation_observation,
    )


def apply_signer_snapshot(instance: ConsentInstance, signer: SignerSnapshot) -> None:
    now = datetime.now(timezone.utc)
    instance.signer_policy = signer.policy
    instance.signer_actor_type = signer.actor_type
    instance.signer_full_name_snapshot = signer.full_name
    instance.signer_document_type_snapshot = signer.document_type
    instance.signer_document_number_snapshot = signer.document_number
    instance.signer_email_snapshot = signer.email
    instance.signer_phone_snapshot = signer.phone
    instance.signer_relationship_type_snapshot = signer.relationship_type
    instance.signer_relationship_other_snapshot = signer.relationship_other
    instance.minor_participation_status = signer.minor_participation_status
    instance.minor_participation_observation = signer.minor_participation_observation
    instance.signer_selected_at = now
