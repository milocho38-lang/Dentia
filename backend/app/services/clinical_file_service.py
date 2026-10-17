import hashlib
import json
import os
import re
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

from fastapi import UploadFile
from PIL import Image
import pymupdf
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agenda import Appointment, Patient
from app.models.audit_event import AuditEvent
from app.models.clinical_file import ClinicalFile
from app.models.treatment import Treatment
from app.schemas.clinical_file_schema import ClinicalFileListResponse, ClinicalFileResponse
from app.services.auth_service import AuthContext, RequestMetadata

FILE_TYPES = {"RADIOGRAPH", "EXAM", "PHOTOGRAPH", "DOCUMENT", "OTHER"}
CATEGORIES = {"INITIAL", "EVOLUTION", "FINAL", "LEGAL", "LABORATORY", "GENERAL"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}
MAX_SIZE = int(os.getenv("CLINICAL_FILE_MAX_BYTES", str(25 * 1024 * 1024)))
MAX_IMAGE_PIXELS = 80_000_000


class ClinicalFileError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _root() -> Path:
    configured = os.getenv("CLINICAL_FILE_STORAGE_DIR")
    return Path(configured).resolve() if configured else (Path(settings.branding_storage_dir).resolve().parent / "clinical_files")


def resolve_storage_key(storage_key: str) -> Path:
    root = _root()
    candidate = (root / storage_key).resolve()
    if root != candidate and root not in candidate.parents:
        raise ClinicalFileError("Ruta de archivo inválida.", 400)
    return candidate


def detect_mime(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_structure(data: bytes, mime: str) -> None:
    try:
        if mime == "application/pdf":
            with pymupdf.open(stream=data, filetype="pdf") as document:
                if document.needs_pass or document.page_count < 1 or document.page_count > 1000:
                    raise ValueError("invalid or unsupported PDF")
                for index in range(document.page_count):
                    page = document.load_page(index)
                    if page.rect.width <= 0 or page.rect.height <= 0:
                        raise ValueError("invalid PDF page")
            return
        with Image.open(BytesIO(data)) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("image dimensions exceed limit")
            expected = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[mime]
            if image.format != expected:
                raise ValueError("format mismatch")
            image.verify()
    except Exception as exc:
        raise ClinicalFileError("El archivo está truncado, dañado o no tiene una estructura válida.", 415) from exc


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    current, root = path, _root()
    while current == root or root in current.parents:
        current.chmod(0o700)
        if current == root:
            break
        current = current.parent


def _promote_pending_file(data: bytes, path: Path, expected_sha256: str) -> None:
    temporary = path.with_suffix(".uploading")
    if temporary.is_file():
        valid_pending = temporary.stat().st_size == len(data) and hashlib.sha256(temporary.read_bytes()).hexdigest() == expected_sha256
        if not valid_pending:
            raise ClinicalFileError("El temporal pendiente no coincide con la solicitud registrada.", 409)
    else:
        temporary.write_bytes(data)
        temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)


def safe_original_name(name: str | None) -> str:
    value = Path((name or "archivo").replace("\\", "/")).name.strip()
    value = re.sub(r"[\x00-\x1f\x7f]", "", value)
    return value[:300] or "archivo"


def _response(item: ClinicalFile) -> ClinicalFileResponse:
    return ClinicalFileResponse(id=item.id, patient_id=item.patient_id, treatment_id=item.treatment_id, appointment_id=item.appointment_id, file_type=item.file_type, category=item.category, original_name=item.original_name, mime_type=item.mime_type, size_bytes=item.size_bytes, sha256=item.sha256, description=item.description, uploaded_at=item.uploaded_at, uploaded_by=item.uploaded_by)


def _patient(session: Session, context: AuthContext, patient_id: UUID) -> Patient:
    item = session.scalar(select(Patient).where(Patient.id == patient_id, Patient.company_id == context.user.company_id, Patient.is_active.is_(True)))
    if item is None:
        raise ClinicalFileError("Paciente no encontrado.", 404)
    return item


def _get(session: Session, context: AuthContext, file_id: UUID, *, active: bool = True) -> ClinicalFile:
    query = select(ClinicalFile).where(ClinicalFile.id == file_id, ClinicalFile.company_id == context.user.company_id)
    if active:
        query = query.where(ClinicalFile.is_active.is_(True), ClinicalFile.storage_status == "AVAILABLE")
    item = session.scalar(query)
    if item is None:
        raise ClinicalFileError("Archivo no encontrado.", 404)
    return item


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, item: ClinicalFile, action: str, detail: dict, result: str = "SUCCESS") -> None:
    session.add(AuditEvent(company_id=context.user.company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="clinical_file", entity_id=item.id, action=action, result=result, detail=detail, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


async def upload_file(session: Session, context: AuthContext, patient_id: UUID, upload: UploadFile, file_type: str, category: str, description: str | None, treatment_id: UUID | None, appointment_id: UUID | None, idempotency_key: UUID, metadata: RequestMetadata) -> ClinicalFileResponse:
    _patient(session, context, patient_id)
    file_type, category = file_type.upper(), category.upper()
    if file_type not in FILE_TYPES or category not in CATEGORIES:
        raise ClinicalFileError("Tipo o categoría de archivo no válido.", 422)
    if treatment_id and not session.scalar(select(Treatment.id).where(Treatment.id == treatment_id, Treatment.company_id == context.user.company_id, Treatment.patient_id == patient_id)):
        raise ClinicalFileError("Tratamiento relacionado inválido.", 422)
    if appointment_id and not session.scalar(select(Appointment.id).where(Appointment.id == appointment_id, Appointment.company_id == context.user.company_id, Appointment.patient_id == patient_id)):
        raise ClinicalFileError("Cita relacionada inválida.", 422)
    data = await upload.read(MAX_SIZE + 1)
    if not data:
        raise ClinicalFileError("El archivo está vacío.", 422)
    if len(data) > MAX_SIZE:
        raise ClinicalFileError("El archivo supera el tamaño máximo permitido.", 413)
    mime = detect_mime(data)
    if mime not in ALLOWED_MIME_TYPES:
        raise ClinicalFileError("El contenido del archivo no corresponde a un tipo permitido.", 415)
    validate_structure(data, mime)
    normalized_name = safe_original_name(upload.filename)
    normalized_description = (description or "").strip() or None
    fingerprint = hashlib.sha256(json.dumps({"patient_id": str(patient_id), "treatment_id": str(treatment_id) if treatment_id else None, "appointment_id": str(appointment_id) if appointment_id else None, "file_type": file_type, "category": category, "original_name": normalized_name, "description": normalized_description, "mime_type": mime, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    lock_name = f"clinical-file:{context.user.company_id}:{idempotency_key}"
    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:name, 0))"), {"name": lock_name})
    existing = session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.idempotency_key == idempotency_key))
    if existing:
        if existing.patient_id != patient_id or existing.request_fingerprint != fingerprint:
            raise ClinicalFileError("La clave de idempotencia ya fue usada con una solicitud diferente.", 409)
        if existing.storage_status == "AVAILABLE":
            return _response(existing)
    item_id = uuid5(NAMESPACE_URL, f"dentia-clinical-file:{context.user.company_id}:{idempotency_key}")
    storage_key = f"company_{context.user.company_id}/uploads/{item_id}"
    path = resolve_storage_key(storage_key)
    if existing is None:
        item = ClinicalFile(id=item_id, company_id=context.user.company_id, patient_id=patient_id, treatment_id=treatment_id, appointment_id=appointment_id, file_type=file_type, category=category, original_name=normalized_name, storage_key=storage_key, idempotency_key=idempotency_key, request_fingerprint=fingerprint, storage_status="PENDING", mime_type=mime, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), description=normalized_description, uploaded_at=datetime.now(timezone.utc), uploaded_by=context.user.id, is_active=True)
        session.add(item)
        _audit(session, context, metadata, item, "CLINICAL_FILE_UPLOAD_REGISTERED", {"patient_id": str(patient_id), "fingerprint": fingerprint})
        session.commit()
    else:
        item = existing
        session.commit()

    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:name, 0))"), {"name": lock_name})
    item = session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.idempotency_key == idempotency_key))
    if item is None or item.request_fingerprint != fingerprint:
        session.rollback()
        raise ClinicalFileError("No fue posible reconciliar la carga.", 409)
    if item.storage_status == "AVAILABLE":
        session.commit()
        return _response(item)
    if path.is_file() and path.stat().st_size == item.size_bytes and hashlib.sha256(path.read_bytes()).hexdigest() == item.sha256:
        item.storage_status = "AVAILABLE"
        _audit(session, context, metadata, item, "CLINICAL_FILE_UPLOAD_RECOVERED", {"patient_id": str(patient_id), "sha256": item.sha256})
        session.commit()
        return _response(item)
    _private_directory(path.parent)
    temporary = path.with_suffix(".uploading")
    try:
        _promote_pending_file(data, path, item.sha256)
    except Exception:
        temporary.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        item.storage_status = "FAILED"
        _audit(session, context, metadata, item, "CLINICAL_FILE_UPLOAD_FAILED", {"reason": "filesystem_promotion_failed"}, "FAILURE")
        session.commit()
        raise ClinicalFileError("No fue posible almacenar el archivo.", 507)
    item.storage_status = "AVAILABLE"
    _audit(session, context, metadata, item, "CLINICAL_FILE_UPLOADED", {"patient_id": str(patient_id), "file_type": file_type, "category": category, "size_bytes": len(data), "sha256": item.sha256})
    try:
        session.commit()
    except Exception:
        session.rollback()
        # The deterministic, private path is intentionally retained. A retry with the
        # same idempotency key overwrites/reconciles this single orphan candidate.
        raise
    return _response(item)


def list_files(session: Session, context: AuthContext, patient_id: UUID, file_type: str | None = None, category: str | None = None) -> ClinicalFileListResponse:
    _patient(session, context, patient_id)
    query = select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.patient_id == patient_id, ClinicalFile.is_active.is_(True), ClinicalFile.storage_status == "AVAILABLE")
    if file_type:
        query = query.where(ClinicalFile.file_type == file_type.upper())
    if category:
        query = query.where(ClinicalFile.category == category.upper())
    items = list(session.scalars(query.order_by(ClinicalFile.uploaded_at.desc())))
    return ClinicalFileListResponse(items=[_response(item) for item in items], total=len(items))


def get_by_idempotency_key(session: Session, context: AuthContext, patient_id: UUID, key: UUID) -> ClinicalFileResponse:
    _patient(session, context, patient_id)
    item = session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.patient_id == patient_id, ClinicalFile.idempotency_key == key, ClinicalFile.is_active.is_(True), ClinicalFile.storage_status == "AVAILABLE"))
    if item is None:
        raise ClinicalFileError("No existe una carga confirmada para la solicitud.", 404)
    return _response(item)


def download_file(session: Session, context: AuthContext, file_id: UUID, metadata: RequestMetadata) -> tuple[Path, ClinicalFile]:
    item = _get(session, context, file_id)
    path = resolve_storage_key(item.storage_key)
    if not path.is_file() or path.stat().st_size != item.size_bytes:
        _audit(session, context, metadata, item, "CLINICAL_FILE_INTEGRITY_FAILED", {"reason": "missing_or_size_mismatch"}, "FAILURE")
        session.commit()
        raise ClinicalFileError("El archivo no está disponible o no supera la verificación de integridad.", 410)
    if hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
        _audit(session, context, metadata, item, "CLINICAL_FILE_INTEGRITY_FAILED", {"reason": "sha256_mismatch"}, "FAILURE")
        session.commit()
        raise ClinicalFileError("El archivo no supera la verificación de integridad.", 410)
    _audit(session, context, metadata, item, "CLINICAL_FILE_DOWNLOAD_AUTHORIZED", {"patient_id": str(item.patient_id), "sha256": item.sha256})
    session.commit()
    return path, item


def deactivate_file(session: Session, context: AuthContext, file_id: UUID, reason: str, metadata: RequestMetadata) -> None:
    item = _get(session, context, file_id)
    item.is_active = False
    item.deactivated_at = datetime.now(timezone.utc)
    item.deactivated_by = context.user.id
    _audit(session, context, metadata, item, "CLINICAL_FILE_DEACTIVATED", {"patient_id": str(item.patient_id), "reason": reason.strip()})
    session.commit()
