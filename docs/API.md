# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. In production, implement JWT or API key authentication.

---

## Documents API

### Upload Document
Upload a PDF fund performance document for processing.

**Endpoint:** `POST /api/documents/upload`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@/path/to/document.pdf" \
  -F "fund_id=1"
```

**Response:**
```json
{
  "document_id": 1,
  "task_id": null,
  "status": "pending",
  "message": "Document uploaded successfully. Processing started."
}
```

### Get Document Status
Check the parsing status of an uploaded document.

**Endpoint:** `GET /api/documents/{document_id}/status`

**Response:**
```json
{
  "document_id": 1,
  "status": "completed",
  "progress": null,
  "error_message": null
}
```

**Status Values:**
- `pending`: Waiting to be processed
- `processing`: Currently being parsed
- `completed`: Successfully processed
- `failed`: Processing failed

### List Documents
Get all uploaded documents.

**Endpoint:** `GET /api/documents/`

**Query Parameters:**
- `fund_id` (optional): Filter by fund ID
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "fund_id": 1,
    "file_name": "fund_report_2024.pdf",
    "file_path": "/app/uploads/20241006_120000_fund_report_2024.pdf",
    "upload_date": "2024-10-06T12:00:00",
    "parsing_status": "completed",
    "error_message": null
  }
]
```

### Delete Document
Delete an uploaded document.

**Endpoint:** `DELETE /api/documents/{document_id}`

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

---

## Funds API

### List Funds
Get all funds with their metrics.

**Endpoint:** `GET /api/funds/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Tech Growth Fund I",
    "gp_name": "Example Capital",
    "fund_type": "Venture Capital",
    "vintage_year": 2020,
    "created_at": "2024-10-06T12:00:00",
    "metrics": {
      "dpi": 0.7368,
      "irr": 15.25,
      "tvpi": null,
      "rvpi": null,
      "pic": 950000.00,
      "total_distributions": 700000.00,
      "nav": null
    }
  }
]
```

### Create Fund
Create a new fund.

**Endpoint:** `POST /api/funds/`

**Request:**
```json
{
  "name": "Tech Growth Fund I",
  "gp_name": "Example Capital",
  "fund_type": "Venture Capital",
  "vintage_year": 2020
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Tech Growth Fund I",
  "gp_name": "Example Capital",
  "fund_type": "Venture Capital",
  "vintage_year": 2020,
  "created_at": "2024-10-06T12:00:00"
}
```

### Get Fund Details
Get detailed information about a specific fund.

**Endpoint:** `GET /api/funds/{fund_id}`

**Response:**
```json
{
  "id": 1,
  "name": "Tech Growth Fund I",
  "gp_name": "Example Capital",
  "fund_type": "Venture Capital",
  "vintage_year": 2020,
  "created_at": "2024-10-06T12:00:00",
  "metrics": {
    "dpi": 0.7368,
    "irr": 15.25,
    "pic": 950000.00,
    "total_distributions": 700000.00
  }
}
```

### Get Fund Transactions
Get transactions for a specific fund.

**Endpoint:** `GET /api/funds/{fund_id}/transactions`

**Query Parameters:**
- `transaction_type` (required): One of `capital_calls`, `distributions`, `adjustments`
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "fund_id": 1,
      "call_date": "2024-04-30",
      "call_type": "Investment",
      "amount": 384710.00,
      "description": "Q2 2024 Capital Call",
      "created_at": "2024-10-06T12:00:00"
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 1
}
```

### Get Fund Metrics
Get calculated metrics for a fund.

**Endpoint:** `GET /api/funds/{fund_id}/metrics`

**Response:**
```json
{
  "dpi": 0.7368,
  "irr": 15.25,
  "tvpi": null,
  "rvpi": null,
  "pic": 950000.00,
  "total_distributions": 700000.00,
  "nav": null
}
```

---

## Chat API

### Query
Send a question and get an AI-generated answer.

**Endpoint:** `POST /api/chat/query`

**Request:**
```json
{
  "query": "What is the current DPI of this fund?",
  "fund_id": 1,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "answer": "The current DPI (Distribution to Paid-In) of this fund is **0.74x**. This means that for every dollar of capital paid in by LPs, $0.74 has been distributed back. The fund has not yet returned all invested capital to LPs.",
  "sources": [
    {
      "content": "DPI = Cumulative Distributions / Paid-In Capital...",
      "metadata": {
        "document_id": 1,
        "fund_id": 1,
        "page_number": 1
      },
      "score": 0.89
    }
  ],
  "metrics": {
    "dpi": 0.7368,
    "pic": 950000.00,
    "total_distributions": 700000.00
  },
  "processing_time": 2.34
}
```

### Create Conversation
Create a new conversation session.

**Endpoint:** `POST /api/chat/conversations`

**Request:**
```json
{
  "fund_id": 1
}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "fund_id": 1,
  "messages": [],
  "created_at": "2024-10-06T12:00:00",
  "updated_at": "2024-10-06T12:00:00"
}
```

### Get Conversation
Retrieve conversation history.

**Endpoint:** `GET /api/chat/conversations/{conversation_id}`

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "fund_id": 1,
  "messages": [
    {
      "role": "user",
      "content": "What is the current DPI?",
      "timestamp": "2024-10-06T12:00:00"
    },
    {
      "role": "assistant",
      "content": "The current DPI is 0.74x...",
      "timestamp": "2024-10-06T12:00:02"
    }
  ],
  "created_at": "2024-10-06T12:00:00",
  "updated_at": "2024-10-06T12:00:02"
}
```

---

## Metrics API

### Get Fund Metrics with Breakdown
Get detailed metrics calculation with breakdown.

**Endpoint:** `GET /api/metrics/funds/{fund_id}/metrics`

**Query Parameters:**
- `metric` (optional): Specific metric to calculate (`dpi`, `irr`, `pic`, or `all`)

**Response (with specific metric):**
```json
{
  "fund_id": 1,
  "fund_name": "Tech Growth Fund I",
  "metric_name": "DPI",
  "value": 0.7368,
  "breakdown": {
    "metric": "DPI",
    "formula": "Cumulative Distributions / Paid-In Capital",
    "pic": 950000.00,
    "total_distributions": 700000.00,
    "result": 0.7368,
    "explanation": "DPI = 700000.00 / 950000.00 = 0.7368"
  }
}
```

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

---

## Testing with cURL

### Upload a document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@./files/sample_fund_report.pdf"
```

### Ask a question
```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current DPI?",
    "fund_id": 1
  }'
```

### Get fund metrics
```bash
curl "http://localhost:8000/api/funds/1/metrics"
```
