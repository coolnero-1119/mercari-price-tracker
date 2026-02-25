from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[schemas.ItemOut])
def list_items(keyword_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    return crud.get_items(db, keyword_id=keyword_id)


@router.get("/by-keyword/{keyword_id}", response_model=List[schemas.ItemOut])
def items_by_keyword(keyword_id: int, db: Session = Depends(get_db)):
    return crud.get_items(db, keyword_id=keyword_id)


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    return item
