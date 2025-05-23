# PDF Splitter API Contract

This document describes how developers can interact with the PDF Splitter API. The service accepts PDF uploads, splits the files into manageable chunks and calls an external extraction API to generate text.

## Authentication

All endpoints require an API key provided in the `X-API-Key` header. Requests without a valid key will receive `403 Forbidden` responses.

## Endpoints

### `GET /status`
Returns a simple status object indicating the service is running. The root path `/` behaves the same way.

**Response**
```json
{ "status": "OK" }
```

### `GET /function_status`
Checks if the service can reach the underlying text extraction function.

- **200 OK** – the function is reachable.
- **503 Service Unavailable** – the function is unreachable.

### `POST /extract_text/`
Uploads a PDF file and returns the combined text extracted from all pages.

- **Content-Type:** `multipart/form-data`
- **Field:** `file` – PDF file to process

**Successful response**
```json
{
  "metadata": {"...": "..."},
  "text": "full text from the PDF",
  "page_count": 42
}
```

### Example Request
```bash
curl -X POST http://localhost:5006/extract_text/ \
  -H "X-API-Key: YOUR_API_KEY" \
  -F file=@your_document.pdf
```

For full schema details see [`openapi.yaml`](openapi.yaml).
