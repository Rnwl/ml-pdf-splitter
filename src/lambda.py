import json
import fitz
import base64
import time

def extract_text_simple(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ''
    for page in doc:
        text += page.get_text()
    return text


def lambda_handler(event, context):
    start_time = time.time()
    # TODO implement
    event = json.loads(event)
    data = base64.b64decode(event['pdf_data'].encode('utf-8'))
    text = extract_text_simple(data)
    return {
        'stage' : 'test',
        'time_taken': time.time() - start_time,
        'text': text,
        'arn_version' : context.invoked_function_arn,
        'function_version' : context.function_version,
    }