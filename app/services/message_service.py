import os

import aiofiles  # 推荐使用异步文件操作


class MessageService:
	async def handle_file_upload(self, user_id: int, file: UploadFile):
		temp_path = f"/tmp/{file.filename}"

		try:
			# 1. 开始写入文件
			async with aiofiles.open(temp_path, 'wb') as f:
				while chunk := await file.read(1024 * 1024):  # 每次读取 1MB
					await f.write(chunk)

			# 2. 如果运行到这里，说明上传完整，执行 DB 记录
			return await self.message_repo.create_file_message(user_id, temp_path)

		except Exception as e:
			# 3. 如果中间用户点 "X"，连接断开，这里会捕获到异常
			print(f"Upload interrupted for user {user_id}: {e}")
			if os.path.exists(temp_path):
				os.remove(temp_path)  # 清理没传完的碎片文件
			raise e  # 继续抛出，让 FastAPI 处理剩下的事
