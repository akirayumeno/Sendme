# SendMe API Documentation

Base URL: `http://localhost:8000/api/v1`

Authentication:
- Bearer token for message APIs
- Header: `Authorization: Bearer <access_token>`

## 1. Auth APIs

### 1.1 Request Registration OTP

`POST /auth/request-otp`

Request:
```json
{
  "email": "user@example.com",
  "username": "user_01",
  "password": "StrongPass123"
}
```

Success:
- `200 OK`
```json
{
  "message": "Verification code sent."
}
```

Common errors:
- `409 Conflict`: username/email already exists
- `429 Too Many Requests`: OTP cooldown/rate limit
- `423 Locked`: OTP locked after too many attempts
- `503 Service Unavailable`: email delivery failed

### 1.2 Register With OTP

`POST /auth/register-with-otp`

Request:
```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

Success:
- `200 OK`
```json
{
  "message": "User registered successfully."
}
```

Common errors:
- `400 Bad Request`: invalid/expired OTP
- `423 Locked`: OTP locked

### 1.3 Login

`POST /auth/login`  
Content-Type: `application/x-www-form-urlencoded`

Request form:
- `username`
- `password`

Success:
- `200 OK`
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

Error:
- `401 Unauthorized`

### 1.4 Refresh Access Token

`POST /auth/refresh`

Request:
```json
{
  "refresh_token": "<jwt>"
}
```

Success:
- `200 OK`
```json
{
  "access_token": "<new_jwt>",
  "token_type": "bearer"
}
```

Error:
- `401 Unauthorized`

## 2. Message APIs

## 2.1 Send Text Message

`POST /messages/text`

Request:
```json
{
  "content": "hello from desktop",
  "device": "desktop"
}
```

Success:
- `200 OK`
```json
{
  "id": 12,
  "type": "text",
  "status": "SENT",
  "content": "hello from desktop",
  "fileName": null,
  "fileType": null,
  "filePath": null,
  "fileSize": null,
  "progress": null,
  "error": null,
  "created_at": "2026-03-08T10:00:00.000000Z",
  "updated_at": "2026-03-08T10:00:00.000000Z",
  "device": "desktop",
  "copied": false,
  "imageUrl": null
}
```

Errors:
- `401 Unauthorized`
- `422 Unprocessable Entity` (invalid payload)

### 2.2 Get Message History

`GET /messages/history?page=1`

Success:
- `200 OK` array of `MessageResponse`

Errors:
- `401 Unauthorized`

### 2.3 Upload File/Image

`POST /messages/upload`  
Content-Type: `multipart/form-data`

Form fields:
- `file`: binary
- `device`: `desktop` | `phone` (optional, default `desktop`)

Success:
- `200 OK` returns `MessageResponse` (`type=file` or `type=image`)

Errors:
- `400 Bad Request`: missing filename / upload aborted / invalid path / permission
- `403 Forbidden`: quota exceeded
- `401 Unauthorized`

### 2.4 Download File

`GET /messages/{message_id}/download`

Success:
- `200 OK` binary file stream

Errors:
- `401 Unauthorized`
- `404 Not Found`

### 2.5 View File (Image Preview)

`GET /messages/{message_id}/view`

Success:
- `200 OK` image stream

Errors:
- `401 Unauthorized`
- `404 Not Found`
- `415 Unsupported Media Type` (non-image message)

### 2.6 Delete Message

`DELETE /messages/{message_id}`

Success:
- `200 OK`
```json
{
  "status": "success",
  "message": "Message deleted"
}
```

Errors:
- `401 Unauthorized`
- `403 Forbidden` (owner mismatch)
- `404 Not Found`

## 3. Realtime API (WebSocket)

### 3.1 Message Event Stream

`WS /ws/messages?token=<access_token>`

Behavior:
- Connection is authenticated by access token query param.
- Server emits JSON events when current user messages change.
- Client should call `GET /messages/history` on event to sync full state.

Example server payload:
```json
{
  "event": "message.updated",
  "message_id": 123
}
```

or

```json
{
  "event": "message.deleted",
  "message_id": 123
}
```

Close cases:
- `1008`: missing/invalid token
- network disconnect: client should reconnect and fallback to polling

## 4. MessageResponse Fields

- `id`: integer message id
- `type`: `text` | `image` | `file`
- `status`: `SENT` | `PROCESSING` | `FAILED` | `EXPIRED`
- `content`: text message body
- `fileName`: original filename
- `fileType`: MIME type
- `filePath`: internal stored relative path
- `fileSize`: formatted size string (response model computed field)
- `created_at`, `updated_at`: UTC timestamps
- `device`: `desktop` | `phone`
- `imageUrl`: generated for image messages

## 5. Testing APIs Quickly

- Swagger: `http://0.0.0.0:8000/docs`
- For protected endpoints:
  1. Call `/auth/login`
  2. Copy `access_token`
  3. Click `Authorize` in Swagger with `Bearer <token>`
