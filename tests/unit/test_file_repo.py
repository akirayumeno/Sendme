import pytest

from app.storage.exceptions import FileWriteError, RepositoryError
from app.storage.file_repo import FileRepo


# Mocking a file stream (async generator)
async def mock_file_stream(chunks):
	for chunk in chunks:
		yield chunk


@pytest.fixture
def file_repo(tmp_path):
	"""
	Initialize FileRepo using pytest's temporary directory.
	This ensures no real files are created in your project folder.
	"""
	return FileRepo(upload_dir = tmp_path)


@pytest.mark.asyncio
class TestFileRepo:

	async def test_save_success(self, file_repo):
		"""Test saving a file successfully to the temp directory."""
		filename = "test_file.txt"
		content = [b"Hello ", b"World"]

		# Act
		bytes_written = await file_repo.save(mock_file_stream(content), filename)

		# Assert
		assert bytes_written == 11
		temp_file = file_repo.temp_dir / filename
		assert temp_file.exists()
		assert temp_file.read_bytes() == b"Hello World"

	async def test_save_and_move_to_final(self, file_repo):
		"""Test the full workflow: Save to temp then move to final."""
		filename = "photo.jpg"
		final_dest = "uploads/user_1/photo.jpg"

		# 1. Save to temp
		await file_repo.save(mock_file_stream([b"fake-image-data"]), filename)

		# 2. Move to final
		relative_path = await file_repo.move_to_final(filename, final_dest)

		# Assert
		assert relative_path == final_dest
		assert not (file_repo.temp_dir / filename).exists()
		assert (file_repo.upload_dir / final_dest).exists()

	async def test_save_failure_cleanup(self, file_repo):
		"""Test that a partial file is deleted if an error occurs during streaming."""
		filename = "broken_upload.dat"

		async def broken_stream():
			yield b"partial data"
			raise IOError("Connection lost")

		# Act & Assert
		with pytest.raises(FileWriteError):
			await file_repo.save(broken_stream(), filename)

		# Verify cleanup: The partial file should NOT exist
		assert not (file_repo.temp_dir / filename).exists()

	async def test_delete_file(self, file_repo):
		"""Test manual deletion of a file."""
		filename = "delete_me.txt"
		file_path = file_repo.upload_dir / filename
		file_path.write_bytes(b"data")

		# Act
		success = await file_repo.delete(filename)

		# Assert
		assert success is True
		assert not file_path.exists()

	async def test_delete_temp_file(self, file_repo):
		"""Test specific helper for deleting temp files (The 'X' button logic)."""
		filename = "temp_to_cancel.txt"
		(file_repo.temp_dir / filename).write_bytes(b"temporary")

		# Act
		success = await file_repo.delete_temp(filename)

		# Assert
		assert success is True
		assert not (file_repo.temp_dir / filename).exists()

	async def test_move_file_not_found(self, file_repo):
		"""Test that moving a non-existent temp file raises an error."""
		with pytest.raises(RepositoryError) as exc_info:
			await file_repo.move_to_final("non_existent.txt", "final.txt")

		assert "Atomic move failed" in str(exc_info.value)
