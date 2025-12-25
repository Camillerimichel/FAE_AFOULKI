from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["Documents"])
templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------------
#            ROUTES HTML — PROTÉGÉES SESSION
# --------------------------------------------------------

@router.get("/html")
def liste_documents_html(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/auth/login")

    data = db.query(Document).all()
    return templates.TemplateResponse(
        "documents/list.html",
        {"request": request, "documents": data}
    )


@router.get("/html/{document_id}")
def detail_document_html(document_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/auth/login")

    doc = db.query(Document).filter(Document.id_document == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    return templates.TemplateResponse(
        "documents/detail.html",
        {"request": request, "document": doc}
    )


# --------------------------------------------------------
#                      API CRUD JSON
# --------------------------------------------------------

@router.get("/", response_model=list[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id_document == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return doc


@router.post("/", response_model=DocumentResponse)
def create_document(data: DocumentCreate, db: Session = Depends(get_db)):
    nouveau = Document(**data.dict())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, data: DocumentCreate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id_document == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    for key, value in data.dict().items():
        setattr(doc, key, value)

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id_document == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    db.delete(doc)
    db.commit()
    return {"message": "Document supprimé"}
