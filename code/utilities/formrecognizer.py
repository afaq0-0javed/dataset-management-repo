# from azure.core.credentials import AzureKeyCredential
# from azure.ai.formrecognizer import DocumentAnalysisClient
import os
from dotenv import load_dotenv
import requests
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import streamlit as st
import threading
import math

class AzureFormRecognizerClient:
    def __init__(self, form_recognizer_endpoint: str = None, form_recognizer_key: str = None):

        load_dotenv()

        self.pages_per_embeddings = int(os.getenv('PAGES_PER_EMBEDDINGS', 2))
        self.section_to_exclude = ['footnote', 'pageHeader', 'pageFooter', 'pageNumber']

        self.form_recognizer_endpoint : str = form_recognizer_endpoint if form_recognizer_endpoint else os.getenv('FORM_RECOGNIZER_ENDPOINT')
        self.form_recognizer_key : str = form_recognizer_key if form_recognizer_key else os.getenv('FORM_RECOGNIZER_KEY')

    def extract_text(self, content, start, end, response, i):
    
        length = end - start
        
        results = []
        
        page_number = start
        
        while page_number < end:
            
            page = content[page_number]

            # Convert the page to an image (you may need to adjust resolution)
            image = page.get_pixmap()
            image_data = image.samples  # Get the image data

            # Convert the image data to a PIL Image
            pil_image = Image.frombytes("RGB", [image.width, image.height], image_data)

            # Perform OCR on the image
            page_text = pytesseract.image_to_string(pil_image)

            results.append(page_text)
            
            print(f'Page No:{page_number} - done')
            
            page_number+=1
            
        response[i] = {
            "start": start,
            "end": end,
            "pages": results
        }

    def analyze_read(self, formUrl, filename):

        text_file = []

        try:
            # Fetch the PDF file from the URL
            response = requests.get(formUrl)   
            
            if response.status_code == 200:

                st.warning(f'Generating Text File of {filename}')
                
                threads = []

                pdf_stream = BytesIO(response.content)

                pdf_document = fitz.open(stream=pdf_stream)

                pages_count = len(pdf_document) 

                results = [None] * math.ceil(pages_count/50)

                i = 0
                index = 0

                while pages_count > 0:
                    if pages_count > 50:
                        threads.append(threading.Thread(target=self.extract_text, args=(pdf_document, i, i+50, results, index)))
                        i += 50
                        pages_count -= 50
                    else:
                        threads.append(threading.Thread(target=self.extract_text, args=(pdf_document, i, i+pages_count, results, index)))
                        pages_count = 0
                    index+=1

                for thread in threads:
                    thread.start()

                for thread in threads:
                    thread.join()

                pdf_document.close()

                for result in results:
                    for page in result['pages']:
                        text_file.append(page)

            else:
                text_file.append('')
                print(f"Failed to fetch PDF from URL. Status code: {response.status_code}")

        except Exception as e:
            text_file.append('')
            st.write(f"{str(e)}")
            print(f"An error occurred: {str(e)}")

        return text_file
