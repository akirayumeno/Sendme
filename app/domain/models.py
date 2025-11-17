# your_project/domain/models.py
from dataclasses import dataclass
from datetime import datetime


# 使用 dataclass 是现代 Python 中定义纯净数据模型的推荐方式
@dataclass
class File:
	"""
	核心领域模型：代表业务中的一个文件实体。
	包含数据属性和业务行为。
	"""
	id: int
	user_id: int
	file_path: str
	file_size_bytes: int
	status: str
	is_deleted: bool = False
	created_at: datetime = None

	# -------------------------------------------------------------------
	# 核心职责：封装业务行为（方法）
	# -------------------------------------------------------------------

	def mark_for_deletion(self) -> None:
		"""
		业务行为：标记文件为逻辑删除。
		（这是一个业务规则，而不是数据库操作）
		"""
		self.is_deleted = True
		# 可以在这里添加日志记录等纯业务操作
		print(f"File {self.id} marked for deletion.")

	def check_download_permission(self, user_id) -> None:
		"""
		业务规则：只有状态为 READY 的文件才能被下载。
		"""
		if self.status != status.READY:
			raise FileNotReadyError(f"File ID {self.id} is not ready for download. Status: {self.status.value}")

	def check_quota_impact(self, user_current_quota: int, user_max_quota: int) -> None:
		"""
		业务规则：计算上传该文件后是否会超出用户配额。
		（纯计算逻辑，不涉及数据库查询）
		"""
		projected_quota = user_current_quota + self.file_size_bytes
		if projected_quota > user_max_quota:
			raise FileQuotaExceededError(
				f"Upload size {self.file_size_bytes} exceeds remaining quota."
			)
