import hashlib
import os
import re
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
            if not data.rstrip().endswith(b"%%EOF") or b"startxref" not in data or b"/Type /Page" not in data:
                raise ValueError("incomplete PDF structure")
            tail = data.rsplit(b"startxref", 1)[1].splitlines()
            offsets = [line.strip() for line in tail if line.strip() and line.strip() != b"%%EOF"]
            if not offsets or not offsets[0].isdigit() or int(offsets[0]) >= len(data):
                raise ValueError("invalid PDF xref offset")
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
        query = query.where(ClinicalFile.is_active.is_(True))
    item = session.scalar(query)
    if item is None:
        raise ClinicalFileError("Archivo no encontrado.", 404)
    return item


def _audit(session: Session, context: AuthContext, metadata: RequestMetadata, item: ClinicalFile, action: str, detail: dict, result: str = "SUCCESS") -> None:
    session.add(AuditEvent(company_id=context.user.company_id, user_id=context.user.id, session_id=context.auth_session.id, entity="clinical_file", entity_id=item.id, action=action, result=result, detail=detail, ip_address=metadata.ip_address, user_agent=metadata.user_agent))


async def upload_file(session: Session, context: AuthContext, patient_id: UUID, upload: UploadFile, file_type: str, category: str, description: str | None, treatment_id: UUID | None, appointment_id: UUID | None, idempotency_key: UUID, metadata: RequestMetadata) -> ClinicalFileResponse:
    _patient(session, context, patient_id)
    existing = session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.idempotency_key == idempotency_key))
    if existing:
        if existing.patient_id != patient_id:
            raise ClinicalFileError("La clave de idempotencia pertenece a otra solicitud.", 409)
        return _response(existing)
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
    item_id = uuid4()
    storage_key = f"company_{context.user.company_id}/patients/patient_{patient_id}/{file_type.lower()}/{item_id}{EXTENSIONS[mime]}"
    path = resolve_storage_key(storage_key)
    _private_directory(path.parent)
    temporary = path.with_suffix(path.suffix + ".uploading")
    try:
        temporary.write_bytes(data)
        temporary.chmod(0o600)
        temporary.replace(path)
        path.chmod(0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        path.unlink(missing_ok=True)
        raise ClinicalFileError("No fue posible almacenar el archivo.", 507)
    item = ClinicalFile(id=item_id, company_id=context.user.company_id, patient_id=patient_id, treatment_id=treatment_id, appointment_id=appointment_id, file_type=file_type, category=category, original_name=safe_original_name(upload.filename), storage_key=storage_key, idempotency_key=idempotency_key, mime_type=mime, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), description=(description or "").strip() or None, uploaded_at=datetime.now(timezone.utc), uploaded_by=context.user.id, is_active=True)
    session.add(item)
    _audit(session, context, metadata, item, "CLINICAL_FILE_UPLOADED", {"patient_id": str(patient_id), "file_type": file_type, "category": category, "size_bytes": len(data), "sha256": item.sha256})
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        path.unlink(missing_ok=True)
        existing = session.scalar(select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.idempotency_key == idempotency_key))
        if existing and existing.patient_id == patient_id:
            return _response(existing)
        raise ClinicalFileError("No fue posible reconciliar la carga.", 409)
    except Exception:
        session.rollback()
        path.unlink(missing_ok=True)
        raise
    return _response(item)


def list_files(session: Session, context: AuthContext, patient_id: UUID, file_type: str | None = None, category: str | None = None) -> ClinicalFileListResponse:
    _patient(session, context, patient_id)
    query = select(ClinicalFile).where(ClinicalFile.company_id == context.user.company_id, ClinicalFile.patient_id == patient_id, ClinicalFile.is_active.is_(True))
    if file_type:
        query = query.where(ClinicalFile.file_type == file_type.upper())
    if category:
        query = query.where(ClinicalFile.category == category.upper())
    items = list(session.scalars(query.order_by(ClinicalFile.uploaded_at.desc())))
    return ClinicalFileListResponse(items=[_response(item) for item in items], total=len(items))


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
