from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent_template import (
    ConsentTemplate,
    ConsentTemplateVersion,
    ConsentTemplateVersionProcedure,
    ConsentTemplateVersionSite,
    ConsentTemplateVersionSpecialty,
)
def consent_template_version_hash(
    session: Session,
    template: ConsentTemplate,
    version: ConsentTemplateVersion,
    used_variables: list[str],
) -> str:
    site_ids = sorted(str(value) for value in session.scalars(
        select(ConsentTemplateVersionSite.site_id).where(ConsentTemplateVersionSite.version_id == version.id)
    ))
    procedure_ids = sorted(str(value) for value in session.scalars(
        select(ConsentTemplateVersionProcedure.procedure_catalog_id).where(ConsentTemplateVersionProcedure.version_id == version.id)
    ))
    specialties = sorted(
        (
            {"code": code, "name": name}
            for code, name in session.execute(
                select(ConsentTemplateVersionSpecialty.specialty_code, ConsentTemplateVersionSpecialty.specialty_name)
                .where(ConsentTemplateVersionSpecialty.version_id == version.id)
            )
        ),
        key=lambda item: item["code"],
    )
    payload = {
        "template": {
            "code": template.code,
            "document_kind": template.document_kind,
            "country_code": template.country_code,
            "language_code": template.language_code,
        },
        "version": {
            "number": version.version_number,
            "title": version.title,
            "content": version.content,
            "content_format": version.content_format,
            "scope_type": version.scope_type,
            "priority": version.priority,
            "variables": sorted(used_variables),
            "site_ids": site_ids,
            "procedure_ids": procedure_ids,
            "specialties": specialties,
        },
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
