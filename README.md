# ML PDF Splitter App

This app is now designed to be deployed onto Azure cloud services via Azure Container Apps. The related PDF extraction Azure function must be deployed onto Azure functions.

The splitter app divides PDF files into chunks and makes multiple calls in parallel to the Azure function for rapid decoding of large pdf files into text.

## Environment Variables

The following variables must be provided to the container:

- `PDF2TXT_FUNCTION_URL` – URL of the Azure Function that performs PDF to text conversion.
- `PDF_SPLITTER_API_KEY` – API key expected by the splitter endpoints.
- `ENABLE_FILE_LOGS` – Set to `true` to also write logs to files inside the container.

You can place these in an `.env` file or pass them directly to the container.

## Building and Running Locally

```bash
docker build -t ml-pdf-splitter .
docker run -p 5006:5006 --env-file .env ml-pdf-splitter
```

The compose file can also be used:

```bash
docker compose up --build
```

Logs will be written to stdout/stderr and, if `ENABLE_FILE_LOGS=true`, also to `./logs`.

## Deploying to Azure Container Apps

1. Build and push the container image to a registry accessible by Azure (e.g. Azure Container Registry).
2. Create an Azure Container App and configure the environment variables listed above.
3. Expose port `5006` on the container app.
4. Deploy the related PDF extraction Azure Function and ensure the URL is set in `PDF2TXT_FUNCTION_URL`.

### Testing with Example Data

Sample PDFs are provided in the `data/` directory. These files are excluded from the Docker image by default via `.dockerignore`. Mount the directory when running locally if you wish to test with the examples:

```bash
docker run -p 5006:5006 --env-file .env -v $(pwd)/data:/usr/src/app/data ml-pdf-splitter
```
