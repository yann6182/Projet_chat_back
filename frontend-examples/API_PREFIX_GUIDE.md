# API Route Changes Guide - Adding the /api Prefix

## Recent Changes

We've updated the API routes in the backend to consistently use an `/api` prefix for all endpoints. This change ensures a more standard structure and helps separate API routes from other routes (like frontend serving).

### Changes Made:

1. **Main router configuration in `main.py`**:
   ```python
   app.include_router(users.router, prefix="/api")
   app.include_router(chat.router, prefix="/api")
   app.include_router(documents.router, prefix="/api")
   app.include_router(knowledge_base.router, prefix="/api")
   app.include_router(auth.router, prefix="/api")
   app.include_router(file_chat.router, prefix="/api")
   app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
   ```

2. **Frontend API calls updated** to include the `/api` prefix:
   - Authentication endpoints: `/api/auth/login`, `/api/auth/check-admin`
   - User endpoints: `/api/users/me`
   - Admin endpoints: `/api/admin/list-sources`, `/api/admin/upload-source`, etc.

## Common Errors After This Change

You might encounter errors like:
- `GET http://localhost:8000/auth/check-admin 404 (Not Found)`
- `GET http://localhost:8000/admin/list-sources 404 (Not Found)`
- `POST http://localhost:8000/admin/upload-documents 404 (Not Found)`

## Fixing Your Frontend

### 1. Update API URLs

Change all your API calls to include the `/api` prefix:

From:
```javascript
axios.get(`${apiUrl}/auth/check-admin`);
```

To:
```javascript
axios.get(`${apiUrl}/api/auth/check-admin`);
```

### 2. Check for Custom Endpoints

The error `GET http://localhost:8000/api/admin/documents` suggests your frontend is trying to access an endpoint that doesn't exist in our API.

Our actual endpoints are:
- `/api/admin/list-sources` (to list documents)
- `/api/admin/upload-source` (to upload documents)

Make sure your frontend uses these exact paths.

### 3. Create API Service File

Consider creating a service file to centralize all API calls:

```javascript
// api.service.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const ApiService = {
  // Auth
  login: (email, password) => 
    axios.post(`${API_URL}/api/auth/login`, { email, password }),
  
  checkAdmin: (token) => 
    axios.get(`${API_URL}/api/auth/check-admin`, {
      headers: { Authorization: `Bearer ${token}` },
      withCredentials: true
    }),
  
  // Admin Document Management
  listDocuments: (token) => 
    axios.get(`${API_URL}/api/admin/list-sources`, {
      headers: { Authorization: `Bearer ${token}` }
    }),
  
  uploadDocument: (formData, token, onProgress) => 
    axios.post(`${API_URL}/api/admin/upload-source`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    }),
  
  deleteDocument: (filename, token) => 
    axios.delete(`${API_URL}/api/admin/delete-source/${filename}`, {
      headers: { Authorization: `Bearer ${token}` }
    }),
  
  reindexDocuments: (token) => 
    axios.post(`${API_URL}/api/admin/reindex-sources`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
};
```

Then use it in your components:

```javascript
import { ApiService } from './api.service';

// In your component
const fetchDocuments = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await ApiService.listDocuments(token);
    setDocuments(response.data);
  } catch (error) {
    console.error('Error fetching documents:', error);
  }
};
```

## Testing Your Changes

You can use the `test_api_endpoints.py` script to verify that all API endpoints are working correctly:

```
python scripts/test_api_endpoints.py --email admin@example.com --password your_password
```

This script will test the most common endpoints and verify they return the expected responses.
