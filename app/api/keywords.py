from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=List[schemas.KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return crud.get_keywords(db)


@router.post("", response_model=schemas.KeywordOut, status_code=201)
def create_keyword(data: schemas.KeywordCreate, db: Session = Depends(get_db)):
    return crud.create_keyword(db, data)


@router.get("/{keyword_id}", response_model=schemas.KeywordOut)
def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    kw = crud.get_keyword(db, keyword_id)
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return kw


@router.put("/{keyword_id}", response_model=schemas.KeywordOut)
def update_keyword(keyword_id: int, data: schemas.KeywordUpdate, db: Session = Depends(get_db)):
    kw = crud.update_keyword(db, keyword_id, data)
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return kw


@router.delete("/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_keyword(db, keyword_id)
    if not ok:
        raise HTTPException(status_code=404, detail="关键词不存在")
