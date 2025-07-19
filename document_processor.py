import streamlit as st
import numpy as np
import cv2
from PIL import Image
import fitz  # PyMuPDF
import io

class DocumentProcessor:
    """Handles document upload and preprocessing"""
    
    def __init__(self):
        self.supported_image_formats = ['png', 'jpg', 'jpeg']
        self.supported_pdf_formats = ['pdf']
    
    def process_document(self, uploaded_file):
        """
        Process uploaded document and return processed image array
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            numpy.ndarray: Processed image as numpy array
        """
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension in self.supported_pdf_formats:
            return self._process_pdf(uploaded_file)
        elif file_extension in self.supported_image_formats:
            return self._process_image(uploaded_file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _process_pdf(self, pdf_file):
        """
        Process PDF file and extract first page as image
        
        Args:
            pdf_file: Uploaded PDF file
            
        Returns:
            numpy.ndarray: First page as image array
        """
        try:
            # Read PDF bytes
            pdf_bytes = pdf_file.read()
            
            # Open PDF document
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if len(pdf_document) == 0:
                raise ValueError("PDF file is empty or corrupted")
            
            # Get first page
            first_page = pdf_document[0]
            
            # Convert page to image
            # Get page dimensions and set appropriate zoom
            page_rect = first_page.rect
            zoom = min(1920 / page_rect.width, 1080 / page_rect.height, 2.0)
            mat = fitz.Matrix(zoom, zoom)
            
            pix = first_page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(pil_image)
            
            pdf_document.close()
            
            return img_array
            
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def _process_image(self, image_file):
        """
        Process image file
        
        Args:
            image_file: Uploaded image file
            
        Returns:
            numpy.ndarray: Processed image array
        """
        try:
            # Read image using PIL
            pil_image = Image.open(image_file)
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(pil_image)
            
            # Resize if image is too large
            height, width = img_array.shape[:2]
            max_dimension = 1920
            
            if max(height, width) > max_dimension:
                if height > width:
                    new_height = max_dimension
                    new_width = int(width * max_dimension / height)
                else:
                    new_width = max_dimension
                    new_height = int(height * max_dimension / width)
                
                img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return img_array
            
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
    
    def enhance_image_for_detection(self, img_array):
        """
        Enhance image for better symbol detection
        
        Args:
            img_array: Input image as numpy array
            
        Returns:
            numpy.ndarray: Enhanced image
        """
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive threshold
        enhanced = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return enhanced
