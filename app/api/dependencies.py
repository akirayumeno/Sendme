from app.services.file_service import FileService


def get_file_service() -> FileService:
	storage_repo = LocalStorageRepository()
	return FileService(storage_repo)
