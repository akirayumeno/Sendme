# 核心业务逻辑函数，用于单元测试

def format_file_size(bytes: int) -> str:
	"""
	格式化文件大小 (Bytes, KB, MB, GB)。
	"""
	if bytes < 0:
		return "Invalid Size"
	if bytes == 0:
		return "0 Bytes"

	k = 1024
	sizes = ["Bytes", "KB", "MB", "GB", "TB"]

	i = 0
	while bytes >= k and i < len(sizes) - 1:
		bytes /= k
		i += 1

	# 始终保留一位小数
	return f"{bytes:.1f} {sizes[i]}"


def validate_message_length(content: str) -> bool:
	"""
	验证消息内容的长度是否在 1 到 5000 个字符之间。
	"""
	length = len(content.strip())
	return 1 <= length <= 5000


# 这是一个模拟的时间戳格式化函数，用于演示
# 假设它返回一个 ISO 格式字符串
def format_timestamp(date_str: str) -> str:
	"""
	将日期字符串格式化为标准 ISO 格式 (例如: 2024-00-00T00:00:00)。
	"""
	try:
		from datetime import datetime
		dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
		return dt.isoformat()
	except ValueError:
		return "Invalid Date"
