from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.schema import ItemSchema, ItemCreate

router = APIRouter(prefix="/items", tags=["items"])

fake_items_db = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@router.get("/", response_model=List[ItemSchema])
async def read_items():
    return fake_items_db

@router.get("/{item_id}", response_model=ItemSchema)
async def read_item(item_id: int):
    for item in fake_items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item non trouvé")

@router.post("/", response_model=ItemSchema)
async def create_item(item: ItemCreate):
    new_id = max(item["id"] for item in fake_items_db) + 1
    new_item = {"id": new_id, "name": item.name}
    fake_items_db.append(new_item)
    return new_item

