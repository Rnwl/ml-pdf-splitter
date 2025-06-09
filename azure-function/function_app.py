import azure.functions as func
import logging
import fitz
import base64
import time
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="pdf_extraction")
def pdf_extraction(req: func.HttpRequest) -> func.HttpResponse:
    start_time = time.time()
    logging.info('PDF extraction started')
    try:
        logging.info('PDF2TXT function processed a request.')
        pdf_data = req.params.get('pdf_data')
        
        if not pdf_data:
            try:
                req_body = req.get_json()
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"ValueError": "No PDF data provided - 1"}),
                    status_code=400,
                    mimetype="application/json"
                )
            else:
                pdf_data = req_body.get('pdf_data')

        if not pdf_data:
            return func.HttpResponse(
                json.dumps({"Error": "No PDF data provided - 2"}),
                status_code=400,
                mimetype="application/json"
            )

        try:
            data = base64.b64decode(pdf_data.encode('utf-8'))
        except Exception as e:
            return func.HttpResponse(
                json.dumps({"Error": "Invalid base64 encoding"}),
                status_code=400,
                mimetype="application/json"
            )

        text = extract_text_simple(data)
        response = {
            'stage': 'test',
            'time_taken': time.time() - start_time,
            'text': text,
        }
        logging.info(f'PDF extraction completed in {time.time() - start_time:.2f} seconds')
        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f'PDF extraction failed: {str(e)}', exc_info=True)
        return func.HttpResponse(
            json.dumps({"Error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

def extract_text_simple(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        text = ''
        for page in doc:
            text += page.get_text()
        return text
    finally:
        doc.close()  # Ensure the document is closed