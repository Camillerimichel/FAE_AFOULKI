from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.typedocument import TypeDocument
from app.schemas.typedocument import TypeDocumentCreate, TypeDocumentResponse

router = APIRouter(prefix="/typesdocuments", tags=["Types de documents"])


@router.get("/", response_model=list[TypeDocumentResponse])
def get_types_documents(db: Session = Depends(get_db)):
    return db.query(TypeDocument).all()


@router.get("/{type_id}", response_model=TypeDocumentResponse)
def get_type_document(type_id: int, db: Session = Depends(get_db)):
    record = db.query(TypeDocument).filter(TypeDocument.id_type == type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Type de document introuvable")
    return record


@router.post("/", response_model=TypeDocumentResponse)
def create_type_document(data: TypeDocumentCreate, db: Session = Depends(get_db)):
    record = TypeDocument(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{type_id}", response_model=TypeDocumentResponse)
def update_type_document(type_id: int, data: TypeDocumentCreate, db: Session = Depends(get_db)):
    record = db.query(TypeDocument).filter(TypeDocument.id_type == type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Type de document introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{type_id}")
def delete_type_document(type_id: int, db: Session = Depends(get_db)):
    record = db.query(TypeDocument).filter(TypeDocument.id_type == type_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Type de document introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Type de document supprimé"}
