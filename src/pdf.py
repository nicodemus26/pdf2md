import fitz  # PyMuPDF
from dataclasses import dataclass
from pdfminer.layout import LTTextBox, LTImage, LTFigure
from pdfminer.high_level import extract_pages
from src.utility import check_overlap

@dataclass
class PdfRect:
    x1: float
    y1: float
    x2: float
    y2: float

@dataclass
class PdfElement:
    page_number: int
    bbox: PdfRect
    text: str
    visible: bool

class Pdf:
    def __init__(self, pdf_path):
        # Load the PDF with PyMuPDF and pdfminer
        self.doc = fitz.open(pdf_path)
        self.pdfminer_pages = list(extract_pages(pdf_path))

        self.margin = PdfRect(0.15, 0.08, 0.85, 0.92)
        self.elements = {}

        index = 0
        for page_number, pdfminer_page in enumerate(self.pdfminer_pages):
            for element in pdfminer_page:
                overlap = check_overlap(
                    element.bbox, 
                    (
                        pdfminer_page.width * self.margin.x1, 
                        pdfminer_page.height * self.margin.y1, 
                        pdfminer_page.width * self.margin.x2,
                        pdfminer_page.height * self.margin.y2
                    ))

                if isinstance(element, LTTextBox):
                    text = element.get_text()
                    text = text.replace("-\n", "")
                    text = text.replace("\n", " ")
                    text = text.strip()
                    self.elements[index] = PdfElement(page_number + 1, element.bbox, text, overlap)
                    index += 1
                elif isinstance(element, LTFigure):
                    self.elements[index] = PdfElement(page_number + 1, element.bbox, "image", overlap)
                    index += 1

    def iter_elements(self):
        """Generator method to iterate over elements safely."""
        for key in self.elements:
            yield key, self.elements[key]

    def iter_elements_page(self, page_number):
        """Generator method to iterate over elements safely."""
        for key in self.elements:
            if self.elements[key].page_number == page_number + 1:
                yield key, self.elements[key]

    def get_pixmap(self, page_number):
        return self.doc.load_page(page_number).get_pixmap()
    
    def get_page_ratio(self, page_number):
        page = self.doc[page_number]
        return page.bound().width / page.bound().height
    
    def get_page_extent(self, page_number):
        page = self.pdfminer_pages[page_number]
        return page.width, page.height
    
    def get_safe_margin(self):
        return self.margin