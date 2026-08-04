from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth
from app.models.firmware import FirmwarePackage

router = APIRouter(prefix="/acs/firmwares", tags=["firmwares"])


def _store_root() -> Path:
    root = Path(get_settings().firmware_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


@router.get("")
def list_firmwares(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("acs.firmwares")
    rows = db.query(FirmwarePackage).order_by(FirmwarePackage.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "id": str(r.id),
                "filename": r.filename,
                "product_class": r.product_class,
                "version": r.version,
                "size_bytes": r.size_bytes,
                "sha256": r.sha256,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


@router.post("")
async def upload_firmware(
    product_class: str = Form(...),
    version: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("acs.firmwares-upload")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    digest = hashlib.sha256(data).hexdigest()
    fid = uuid.uuid4()
    safe_name = Path(file.filename or "firmware.bin").name
    dest = _store_root() / f"{fid}_{safe_name}"
    dest.write_bytes(data)
    row = FirmwarePackage(
        id=fid,
        filename=safe_name,
        product_class=product_class.strip(),
        version=(version or "").strip(),
        size_bytes=len(data),
        sha256=digest,
        stored_path=str(dest),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": str(row.id), "sha256": row.sha256, "size_bytes": row.size_bytes}


@router.delete("/{firmware_id}")
def delete_firmware(
    firmware_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("acs.firmwares-delete")
    row = db.query(FirmwarePackage).filter(FirmwarePackage.id == firmware_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Firmware não encontrado")
    path = Path(row.stored_path)
    if path.is_file():
        path.unlink(missing_ok=True)
    db.delete(row)
    db.commit()
    return {"ok": True}
