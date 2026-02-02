# API Testing Guide

This document provides curl commands and examples for testing the Post CRUD API.

## Base URL
```
http://localhost:5000/api/posts
```

## Endpoints

### 1. Create a Post (with image upload)

```bash
curl -X POST http://localhost:5000/api/posts \
  -F "userName=Amanda Johnson" \
  -F "userHandle=@mandaj" \
  -F "userImage=https://i.pravatar.cc/150?u=3" \
  -F "isVerified=true" \
  -F "likes=120" \
  -F "postImage=@/path/to/your/image.jpg"
```

**Response:**
```json
{
  "id": 1,
  "userName": "Amanda Johnson",
  "userHandle": "@mandaj",
  "userImage": "https://i.pravatar.cc/150?u=3",
  "isVerified": true,
  "postImage": "uploads/abc123def456.jpg",
  "likes": 120,
  "createdAt": "2026-02-02T03:45:09.123456"
}
```

### 2. Get All Posts (with pagination)

```bash
# Get first page (default: 10 items per page)
curl -X GET http://localhost:5000/api/posts

# Get specific page with custom per_page
curl -X GET "http://localhost:5000/api/posts?page=2&per_page=5"
```

**Response:**
```json
{
  "posts": [
    {
      "id": 1,
      "userName": "Amanda Johnson",
      "userHandle": "@mandaj",
      "userImage": "https://i.pravatar.cc/150?u=3",
      "isVerified": true,
      "postImage": "uploads/abc123def456.jpg",
      "likes": 120,
      "createdAt": "2026-02-02T03:45:09.123456"
    }
  ],
  "has_next": false,
  "has_prev": false,
  "total": 1,
  "pages": 1
}
```

### 3. Get a Single Post

```bash
curl -X GET http://localhost:5000/api/posts/1
```

**Response:**
```json
{
  "id": 1,
  "userName": "Amanda Johnson",
  "userHandle": "@mandaj",
  "userImage": "https://i.pravatar.cc/150?u=3",
  "isVerified": true,
  "postImage": "uploads/abc123def456.jpg",
  "likes": 120,
  "createdAt": "2026-02-02T03:45:09.123456"
}
```

### 4. Delete a Post

```bash
curl -X DELETE http://localhost:5000/api/posts/1
```

**Response:**
```json
{
  "message": "Post deleted successfully"
}
```

### 5. Access Uploaded Image

```bash
# Direct URL in browser or curl
curl -X GET http://localhost:5000/api/posts/uploads/abc123def456.jpg --output downloaded_image.jpg
```

## Testing with a Sample Image

If you don't have an image handy, you can download one first:

```bash
# Download a sample image
curl -o sample_post.jpg https://picsum.photos/500/500

# Then use it in the create post request
curl -X POST http://localhost:5000/api/posts \
  -F "userName=Amanda Johnson" \
  -F "userHandle=@mandaj" \
  -F "userImage=https://i.pravatar.cc/150?u=3" \
  -F "isVerified=true" \
  -F "likes=120" \
  -F "postImage=@sample_post.jpg"
```

## Common Error Responses

### 400 Bad Request
```json
{
  "error": "userName and userHandle are required"
}
```

### 404 Not Found
```json
{
  "error": "404 Not Found: The requested URL was not found on the server."
}
```

### 500 Internal Server Error
```json
{
  "error": "Error message details"
}
```

## Notes

- Maximum file upload size: 16MB
- Supported image formats: PNG, JPG, JPEG, GIF, WEBP
- Images are stored in `app/static/uploads/` directory
- The `postImage` field in the response contains the relative path to access the image
