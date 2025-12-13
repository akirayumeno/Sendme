# ----------------------------------------------------------------------
# 1.Base Exception
# ----------------------------------------------------------------------
from fastapi import HTTPException
from starlette import status

# Authentication failure exception
CREDENTIALS_EXCEPTION = HTTPException(
	status_code = status.HTTP_401_UNAUTHORIZED,
	detail = "Could not validate credentials",
	headers = {"WWW-Authenticate":"Basic"},
)

# Capacity check failed exception
CAPACITY_EXCEEDED_EXCEPTION = HTTPException(
	status_code = status.HTTP_403_FORBIDDEN,
	detail = "Upload failed: Storage capacity is full. Please delete some messages.",
	headers = {"WWW-Authenticate":"Basic"},
)
