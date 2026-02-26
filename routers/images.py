from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models.user import User
from models.image import Image
from routers.auth import get_current_user
from services.storage import LocalStorage
from config import settings

router = APIRouter(prefix="/images", tags=["images"])
storage = LocalStorage()

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Read file content to check size, then seek back to 0
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB")
    await file.seek(0)

    # Save local file
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = await storage.save(file, filename, str(current_user.id))

    new_image = Image(
        user_id=current_user.id,
        title=title,
        description=description,
        file_path=file_path,
        storage_mode=settings.STORAGE_MODE
    )

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image

@router.get("/")
def get_images(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == current_user.id, Image.is_deleted == False).all()
    return images

@router.get("/{image_id}")
def get_image(image_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.user_id == current_user.id, Image.is_deleted == False).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.put("/{image_id}")
def update_image(
    image_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    image = db.query(Image).filter(Image.id == image_id, Image.user_id == current_user.id, Image.is_deleted == False).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if title is not None:
        image.title = title
    if description is not None:
        image.description = description
        
    db.commit()
    db.refresh(image)
    return image

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    image = db.query(Image).filter(Image.id == image_id, Image.user_id == current_user.id, Image.is_deleted == False).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image.is_deleted = True
    db.commit()
    return None
