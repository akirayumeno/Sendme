# SendMe

**SendMe** is a file upload and download web application built with **React** for the frontend and **FastAPI** for the backend. Users can easily upload files to the server or cloud storage and download them. The project follows a frontend-backend separation architecture and can be extended to use cloud storage such as AWS S3.

---

## Features

- Upload files to server or cloud storage  
- Download previously uploaded files  
- View list of uploaded files  
- Support for large file uploads  
- Extendable with user management and access control  

---

## Tech Stack

- **Frontend**: React, JavaScript, HTML, CSS  
- **Backend**: Python, FastAPI  
- **File Storage**: Local storage or AWS S3  
- **Development Tools**: PyCharm, Docker  
- **Version Control**: Git, GitHub  

---

## Project Structure

sendme/
├─ frontend/ # React frontend
├─ backend/ # FastAPI backend
│ └─ uploaded_files/ # Directory for uploaded files
├─ docker-compose.yml # Optional, for containerized deployment
└─ README.md


---

## Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/your-username/sendme.git
cd sendme
```
### 2. Start the backend
```
cd backend
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
### 3. Start the frontend
```
cd frontend
npm install
npm start
```
