import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile

class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, filename: str, user_id: str) -> str:
        """Save a file and return its path/URL."""
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Delete a file given its path."""
        pass

class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir

    async def save(self, file: UploadFile, filename: str, user_id: str) -> str:
        user_dir = os.path.join(self.base_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    def delete(self, file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False
