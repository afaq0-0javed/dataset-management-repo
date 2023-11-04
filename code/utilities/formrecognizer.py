# from azure.core.credentials import AzureKeyCredential
# from azure.ai.formrecognizer import DocumentAnalysisClient
import os
from dotenv import load_dotenv
import PyPDF2
import requests
from io import BytesIO

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
                # Create a PDF reader object
                pdf_bytes = BytesIO(response.content)
                pdf_reader = PyPDF2.PdfFileReader(pdf_bytes)

                # Initialize an empty string to store the extracted text
                text = ""

                # Iterate through each page in the PDF
                for page_num in range(pdf_reader.getNumPages()):
                    page = pdf_reader.getPage(page_num)
                    text = page.extractText()
                    if len(results) < page_num + 1:
                        results.append('')
                        
                    results[page_num] = text

            else:
                print(f"Failed to fetch PDF from URL. Status code: {response.status_code}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
        return results

        # document_analysis_client = DocumentAnalysisClient(
        #     endpoint=self.form_recognizer_endpoint, credential=AzureKeyCredential(self.form_recognizer_key)
        # )
        
        # poller = document_analysis_client.begin_analyze_document_from_url(
        #         "prebuilt-layout", formUrl)
        # layout = poller.result()

        # results = []
        # page_result = ''
        # for p in layout.paragraphs:
        #     page_number = p.bounding_regions[0].page_number
        #     output_file_id = int((page_number - 1 ) / self.pages_per_embeddings)

        #     if len(results) < output_file_id + 1:
        #         results.append('')

        #     if p.role not in self.section_to_exclude:
        #         results[output_file_id] += f"{p.content}\n"

        # for t in layout.tables:
        #     page_number = t.bounding_regions[0].page_number
        #     output_file_id = int((page_number - 1 ) / self.pages_per_embeddings)
            
        #     if len(results) < output_file_id + 1:
        #         results.append('')
        #     previous_cell_row=0
        #     rowcontent='| '
        #     tablecontent = ''
        #     for c in t.cells:
        #         if c.row_index == previous_cell_row:
        #             rowcontent +=  c.content + " | "
        #         else:
        #             tablecontent += rowcontent + "\n"
        #             rowcontent='|'
        #             rowcontent += c.content + " | "
        #             previous_cell_row += 1
        #     results[output_file_id] += f"{tablecontent}|"

        # return results
