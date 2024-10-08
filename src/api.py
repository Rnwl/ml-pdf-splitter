import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from io import BytesIO
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    from pdf2text import extract_text_api, split_pdf_bytes
    from utils import load_variable
    from timed_logger import TimedLogger
except:
    from src.pdf2text import extract_text_api, split_pdf_bytes
    from src.utils import load_variable
    from src.timed_logger import TimedLogger


load_dotenv()  # Load environment variables from .env file

pdf_splitter_app = FastAPI()

timed_logger = TimedLogger(filename="logs/pdf_splitter.log")
PDF2TEXT_API_KEY = load_variable("PDF2TEXT_API_KEY", logger=timed_logger)
PDF2TXT_LAMBDA_URL = load_variable("PDF2TXT_LAMBDA_URL", logger=timed_logger)
CHUNK_SIZE = 10  # Number of pages per chunk

@pdf_splitter_app.get("/status")
@pdf_splitter_app.get("/")
async def status_check():
    """
    Simple endpoint to check if the service is running.

    Returns:
        JSONResponse: A simple "OK" status message.
    """
    timed_logger.info("Healthcheck Status request received.")
    return JSONResponse(content={"status": "OK"})


@pdf_splitter_app.get("/lambda_status")
async def lambda_status_check():
    """
    Endpoint to check the status of the service.

    Returns:
        JSONResponse: The status of the service and its dependencies.
    """
    try:
        # Check if we can access the PDF extraction API
        def load_pdf_as_bytes(file_path):
            with open(file_path, 'rb') as file:
                return file.read()

        # Usage example
        pdf_path = 'data/lorem_ipsum.pdf'
        pdf_bytes = load_pdf_as_bytes(pdf_path)
        test_pdf = BytesIO(pdf_bytes)
        test_response = await extract_text_api(test_pdf, PDF2TEXT_API_KEY, PDF2TXT_LAMBDA_URL)
        timed_logger.info("Lambda Healthcheck Status request received.")
        return JSONResponse(content={
            "status": "ok",
            "message": "Service is running and can access the PDF extraction API",
            "pdf_extraction_api": "accessible",
            "test_response": test_response
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Service is running but cannot access the PDF extraction API",
                "pdf_extraction_api": "inaccessible",
                "error": str(e)
            }
        )

@pdf_splitter_app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)) -> JSONResponse:
    """
    Endpoint to extract text from a PDF file using the PDF extraction API.

    Args:
        file (UploadFile): The uploaded PDF file.

    Returns:
        JSONResponse: The extracted text results.
    """
    timed_logger.info(f"Received request to extract text from file: {file.filename}")
    
    if not file.filename.lower().endswith('.pdf'):
        timed_logger.warning(f"Rejected non-PDF file: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        contents = await file.read()
        pdf_bytes = BytesIO(contents)
        timed_logger.info(f"Successfully read file: {file.filename}")

        # Split the PDF into chunks
        chunks = list(split_pdf_bytes(pdf_bytes, CHUNK_SIZE))
        timed_logger.info(f"Split PDF into {len(chunks)} chunks")

        # Process each chunk concurrently
        timed_logger.info("Starting concurrent processing of chunks")
        tasks = [
            extract_text_api(BytesIO(chunk), PDF2TEXT_API_KEY, PDF2TXT_LAMBDA_URL)
            for chunk in chunks
        ]
        results = await asyncio.gather(*tasks)
        timed_logger.info("Finished processing all chunks")

        # Combine results from all chunks
        combined_results = combine_results(results)
        timed_logger.info("Combined results from all chunks")

        return JSONResponse(content=combined_results)

    except Exception as e:
        timed_logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def combine_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine results from multiple API calls into a single result.

    Args:
        results (List[Dict[str, Any]]): List of results from each API call.

    Returns:
        Dict[str, Any]: Combined results.
    """
    combined = {
        "metadata": results[0].get("metadata", {}),
        "text": "",
        "page_count": sum(result.get("page_count", 0) for result in results),
    }

    for result in results:
        combined["text"] += result.get("text", "")

    timed_logger.info(f"Combined results: {len(results)} chunks, {combined['page_count']} pages")
    return combined

if __name__ == "__main__":
    import uvicorn
    timed_logger.info("Starting FastAPI server")
    uvicorn.run(pdf_splitter_app, host="0.0.0.0", port=8000)
