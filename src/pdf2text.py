import asyncio
import base64
import logging
import traceback
from collections import defaultdict, deque
from io import BytesIO
from typing import List, AsyncGenerator, Dict, Any

import aiohttp
import fitz

try:
    from timed_logger import TimedLogger
except ModuleNotFoundError:
    from src.timed_logger import TimedLogger

WINDOW_SIZE = 10

logger = TimedLogger(filename="logs/pdf2text.log")


def split_pdf_bytes(file_bytes, window_size: int = WINDOW_SIZE):
    """
    Split a PDF file into smaller chunks of specified window size.

    Args:
        file_bytes (bytes): The PDF file as bytes.
        window_size (int): Number of pages per chunk. Defaults to WINDOW_SIZE.

    Yields:
        bytes: Chunks of the PDF file, each containing up to window_size pages.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for i in range(0, len(doc), window_size):
        new_doc = fitz.open()
        new_doc.insert_pdf(
            doc,
            from_page=i,
            to_page=min(i + window_size - 1, len(doc) - 1),
            annots=False,
            links=False,
        )
        yield new_doc.tobytes()


class PDFTextExtractionAPI:
    """
    A class to manage asynchronous API calls for PDF text extraction.

    This class handles concurrent API requests to extract text from PDF files,
    manages the workload, and processes the results of text extraction.
    """

    def __init__(self, url: str, concurrency_limit: int = 500, window_size: int = WINDOW_SIZE):
        """
        Initialize the PDFTextExtractionAPI class.

        Args:
            url (str): The URL of the PDF extraction API.
            concurrency_limit (int): Maximum number of concurrent API calls. Defaults to 500.
            window_size (int): Number of pages per PDF chunk. Defaults to WINDOW_SIZE.
        """
        self.url = url
        assert self.url is not None, "URL not set"
        self.concurrency_limit = concurrency_limit
        self.session = None
        self.pending = dict()
        self.queue = deque()
        self.part_counts = defaultdict(int)
        self.window_size = window_size

    async def _fetch(self, data):
        try:
            data = {
                "pdf_data": base64.b64encode(data).decode("utf-8"),
            }
            async with self.session.post(
                self.url, 
                json=data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    logger.error(f"HTTP Error: {e.status} - {e.message}")
                    if e.status == 413:  # Payload Too Large
                        logger.error("PDF file too large for API")
                    elif e.status == 429:  # Too Many Requests
                        logger.error("Rate limit exceeded")
                    elif e.status >= 500:  # Server errors
                        logger.error("Server error occurred")
                    return None
                
                return await response.json()
        except Exception as e:
            logger.error(f"Error in _fetch: {e}")
            logger.error(traceback.format_exc())
            return None

    async def submit_work(self, data, *args):
        if len(self.pending) < self.concurrency_limit:
            task = asyncio.create_task(self._fetch(data))
            self.pending[task] = args
        else:
            self.queue.append((data, *args))

    def schedule_work(self):
        if not self.queue:
            return
        data, *args = self.queue.popleft()
        asyncio.create_task(self.submit_work(data, *args))

    async def init_workload(self, files):
        # Queue all the work
        for pdf_id, file_data in enumerate(files):
            for part_id, pdf_part in enumerate(split_pdf_bytes(file_data)):
                await self.submit_work(pdf_part, pdf_id, part_id)
                self.part_counts[pdf_id] += 1

    async def extract_files(self, files: List[bytes]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract text from multiple PDF files concurrently.

        Args:
            files (List[bytes]): A list of PDF files as bytes.

        Yields:
            Dict[str, Any]: Extraction results for each PDF, including metadata and extracted text.
        """
        async with aiohttp.ClientSession() as session:
            self.session = session
            await self.init_workload(files)

            # Get all the text results
            text_results = defaultdict(dict)
            try:
                while self.pending:
                    done, _ = await asyncio.wait(
                        self.pending, return_when=asyncio.FIRST_COMPLETED
                    )
                    future = list(done)[0]
                    pdf_id, part_id = self.pending.pop(future)
                    result = await future
                    if result:
                        text_result = result.get("text", "")
                        self.part_counts[pdf_id] -= 1

                        self.schedule_work()

                        text_results[pdf_id][part_id] = text_result
                        if self.part_counts[pdf_id] == 0:
                            yield {
                                "stage": result["stage"],
                                "time_taken": result["time_taken"],
                                "pdf_id": pdf_id,
                                "text": "\n\n".join(
                                    [
                                        text_results[pdf_id][i]
                                        for i in range(len(text_results[pdf_id]))
                                    ]
                                ),
                            }
            finally:
                self.session = None

    async def extract(self, file: bytes) -> Dict[str, Any]:
        """
        Extract text from a single PDF file.

        Args:
            file (bytes): The PDF file as bytes.

        Returns:
            Dict[str, Any]: Extraction results, including metadata and extracted text.
        """
        async for result in self.extract_files([file]):
            return result


async def extract_text_api(
    file_bytes: BytesIO,
    pdf_extraction_url: str,
) -> Dict[str, Any]:
    """
    Extract text from a PDF using the pdf2text API (AWS Lambda).

    Args:
        file_bytes (BytesIO): BytesIO object containing the PDF file.
        pdf_extraction_url (str): URL of the API Gateway for PDF2Txt.

    Returns:
        Dict[str, Any]: Extracted text results, including metadata.
    """
    logger.info(f"Extract Text API Function. URL: {pdf_extraction_url}")
    api = PDFTextExtractionAPI(url=pdf_extraction_url)
    results = await api.extract(file_bytes)
    return results
