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

class AzureFormRecognizerClient:
    def __init__(self, form_recognizer_endpoint: str = None, form_recognizer_key: str = None):

        load_dotenv()

        self.pages_per_embeddings = int(os.getenv('PAGES_PER_EMBEDDINGS', 2))
        self.section_to_exclude = ['footnote', 'pageHeader', 'pageFooter', 'pageNumber']

        self.form_recognizer_endpoint : str = form_recognizer_endpoint if form_recognizer_endpoint else os.getenv('FORM_RECOGNIZER_ENDPOINT')
        self.form_recognizer_key : str = form_recognizer_key if form_recognizer_key else os.getenv('FORM_RECOGNIZER_KEY')

    def analyze_read(self, formUrl):

        results = []

        try:
            # Fetch the PDF file from the URL
            response = requests.get(formUrl)

            if response.status_code == 200:

                pdf_stream = BytesIO(response.content)
                
                pdf_document = fitz.open(stream=pdf_stream)

                for page_number in range(len(pdf_document)):
                    page = pdf_document[page_number]

                    # Convert the page to an image (you may need to adjust resolution)
                    image = page.get_pixmap()
                    image_data = image.samples  # Get the image data
        
                    # Convert the image data to a PIL Image
                    pil_image = Image.frombytes("RGB", [image.width, image.height], image_data)

                    # Perform OCR on the image
                    page_text = pytesseract.image_to_string(pil_image)
                    
                    results.append(page_text)

                pdf_document.close()

            else:
                print(f"Failed to fetch PDF from URL. Status code: {response.status_code}")

        except Exception as e:
            st.write(f"{str(e)}")
            print(f"An error occurred: {str(e)}")

        return results
