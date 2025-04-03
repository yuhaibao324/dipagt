# API Documentation

This document describes the available API endpoints for the Multi-Agent System.

## Base URL

All API endpoints are relative to the base URL: `http://localhost:8000`

## Health Check

### GET /health_check

Check if the server is running.

**Response:**

```json
{
  "success": true,
  "message": "ok"
}
```

## LLM Endpoints

### POST /llm/chat

Send a chat request to the specified LLM.

**Request Body:**

```json
{
    "vendor": {
        "name": "string",  // "OpenAI" or "Anthropic"
        "base_url": "string"  // Optional, defaults to vendor's default URL
    },
    "llm_args": {
        "model": "string",  // e.g., "gpt-4", "claude-3-haiku-20240307"
        "temperature": number,  // Optional
        "max_tokens": number  // Optional
    },
    "messages": [
        {
            "role": "string",  // "user", "assistant", or "system"
            "content": "string"
        }
    ]
}
```

**Response:**

```json
{
    "content": "string",
    "model": "string",
    "usage": {
        "prompt_tokens": number,
        "completion_tokens": number,
        "total_tokens": number
    }
}
```

## Chat Endpoints

### POST /chat/

Process a chat message.

**Request Body:**

```json
{
  "message": "string",
  "chat_id": "string", // Optional, creates new chat if not provided
  "owner": "string" // Required, identifies the chat owner
}
```

**Response:**

```json
{
    "chat_id": "string",
    "user_message": {
        "content": "string",
        "role": "string"
    },
    "intention": {
        "type": "string",
        "confidence": number
    },
    "actions": [
        {
            "type": "string",
            "parameters": {}
        }
    ],
    "results": [
        {
            "type": "string",
            "content": {}
        }
    ]
}
```

### GET /chat/list/{owner}

Get paginated chat list for a specific owner.

**Query Parameters:**

- `page` (int, default=1): Page number (1-based)
- `page_size` (int, default=20, max=100): Number of items per page

**Response:**

```json
{
    "items": [
        {
            "id": "string",
            "title": "string",
            "description": "string",
            "status": "string",
            "message_count": number,
            "created_at": "string (ISO format)",
            "updated_at": "string (ISO format)"
        }
    ],
    "total": number,
    "page": number,
    "page_size": number,
    "total_pages": number
}
```

### GET /chat/{chat_id}/messages

Get paginated messages for a specific chat.

**Query Parameters:**

- `page` (int, default=1): Page number (1-based)
- `page_size` (int, default=20, max=100): Number of items per page

**Response:**

```json
{
    "items": [
        {
            "id": "string",
            "content": "string",
            "role": "string",
            "type": "string",
            "created_at": "string (ISO format)"
        }
    ],
    "total": number,
    "page": number,
    "page_size": number,
    "total_pages": number
}
```

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**

```json
{
  "detail": "string" // Error message
}
```

**500 Internal Server Error:**

```json
{
  "detail": "string" // Error message
}
```

## Authentication

Currently, the API does not require authentication. However, the `owner` field in chat-related endpoints is used to identify and separate different users' data.

## Rate Limiting

Rate limiting is not currently implemented.

## Notes

1. All timestamps are in ISO 8601 format
2. The LLM endpoints support both OpenAI and Anthropic models
3. Chat endpoints maintain conversation history and context
4. Pagination is 1-based (first page is 1, not 0)
