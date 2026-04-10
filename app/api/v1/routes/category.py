from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from typing import Optional
from app.services.category_service import CategoryService
from app.schemas.category_schema import CategoryCreate, CategoryUpdate
from app.core.dependencies import get_current_user, require_roles
import shutil
import os
import uuid

router = APIRouter(prefix="/categories", tags=["Categories"])

UPLOAD_DIR = "static/uploads/categories"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/")
async def create_category(
    name: str = Form(...),
    description: str = Form(""),
    parent_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user=Depends(require_roles(["admin"]))
):
    image_url = ""
    
    if file:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"{UPLOAD_DIR}/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        image_url = f"/static/uploads/categories/{filename}"

    data = {
        "name": name,
        "description": description,
        "parent_id": parent_id,
        "image_url": image_url
    }

    return await CategoryService.create_category(data, user["user_id"])


@router.get("/")
async def get_categories(
    include_inactive: bool = Query(False),
    user=Depends(get_current_user)
):
    return await CategoryService.get_all_categories(include_inactive)


@router.get("/tree")
async def get_category_tree(user=Depends(get_current_user)):
    """Get categories with nested subcategories"""
    return await CategoryService.get_categories_with_subcategories()


@router.get("/{category_id}")
async def get_category(category_id: str, user=Depends(get_current_user)):
    return await CategoryService.get_category(category_id)


@router.get("/{category_id}/subcategories")
async def get_subcategories(category_id: str, user=Depends(get_current_user)):
    return await CategoryService.get_subcategories(category_id)


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user=Depends(require_roles(["admin"]))
):
    data = {}
    
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if parent_id:
        data["parent_id"] = parent_id
    if status:
        data["status"] = status

    if file:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = f"{UPLOAD_DIR}/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        data["image_url"] = f"/static/uploads/categories/{filename}"

    return await CategoryService.update_category(category_id, data, user["user_id"])


@router.delete("/{category_id}")
async def delete_category(
    category_id: str, 
    user=Depends(require_roles(["admin"]))
):
    return await CategoryService.delete_category(category_id)