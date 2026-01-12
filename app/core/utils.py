# General-purpose helper functions.
def format_file_size(byte_count: int) -> str:
	"""Format bytes to human-readable string"""
	if byte_count <= 0: return "0 Bytes"
	units = ["Bytes", "KB", "MB", "GB", "TB"]
	import math
	i = int(math.floor(math.log(byte_count, 1024)))
	size = round(byte_count / math.pow(1024, i), 2)
	return f"{size} {units[i]}"
