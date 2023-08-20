from fastapi import APIRouter, Depends
from app.feature.generate import generate_resolution_clova, generate_image
from app.core.security import get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session
router = APIRouter(prefix="/generate")
