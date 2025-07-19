import cv2
import numpy as np
from typing import Dict, List, Tuple, Any
from section_manager import SectionManager

class SymbolDetector:
    """Detects and analyzes symbols within document sections"""
    
    def __init__(self):
        self.section_manager = SectionManager()
        
        # Detection parameters
        self.min_contour_area = 50
        self.max_contour_area = 5000
        self.aspect_ratio_threshold = 0.1
        self.solidity_threshold = 0.3
    
    def detect_symbols_in_section(self, image: np.ndarray, section: Dict, 
                                min_area: int = 50, max_area: int = 5000) -> Dict:
        """
        Detect symbols within a specific section of the document
        
        Args:
            image: Input image as numpy array
            section: Section data dictionary
            min_area: Minimum symbol area threshold
            max_area: Maximum symbol area threshold
            
        Returns:
            Dict: Detection results containing symbols and metadata
        """
        # Update detection parameters
        self.min_contour_area = min_area
        self.max_contour_area = max_area
        
        # Extract ROI for the section
        roi = self.section_manager.get_section_roi(image, section)
        
        if roi.size == 0:
            return {'symbols': [], 'section_name': section['name'], 'error': 'Empty ROI'}
        
        # Preprocess ROI for symbol detection
        processed_roi = self._preprocess_image(roi)
        
        # Detect contours
        contours = self._find_contours(processed_roi)
        
        # Filter and classify symbols
        symbols = self._analyze_contours(contours, section, roi)
        
        return {
            'symbols': symbols,
            'section_name': section['name'],
            'roi_shape': roi.shape,
            'total_symbols': len(symbols),
            'section_area': section['area']
        }
    
    def _preprocess_image(self, roi: np.ndarray) -> np.ndarray:
        """
        Preprocess ROI image for better symbol detection
        
        Args:
            roi: Region of interest image
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Convert to grayscale if needed
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        else:
            gray = roi.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def _find_contours(self, binary_image: np.ndarray) -> List:
        """
        Find contours in binary image
        
        Args:
            binary_image: Binary preprocessed image
            
        Returns:
            List: List of contours found
        """
        contours, _ = cv2.findContours(
            binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        return contours
    
    def _analyze_contours(self, contours: List, section: Dict, roi: np.ndarray) -> List[Dict]:
        """
        Analyze contours and classify them as symbols
        
        Args:
            contours: List of detected contours
            section: Section data dictionary
            roi: Region of interest image
            
        Returns:
            List[Dict]: List of detected symbols with properties
        """
        symbols = []
        section_coords = section['coordinates']
        
        for i, contour in enumerate(contours):
            # Filter by area
            area = cv2.contourArea(contour)
            if area < self.min_contour_area or area > self.max_contour_area:
                continue
            
            # Calculate contour properties
            properties = self._calculate_contour_properties(contour)
            
            # Filter by shape characteristics
            if not self._is_valid_symbol(properties):
                continue
            
            # Calculate absolute coordinates in original image
            moments = cv2.moments(contour)
            if moments['m00'] != 0:
                cx = int(moments['m10'] / moments['m00']) + section_coords['x']
                cy = int(moments['m01'] / moments['m00']) + section_coords['y']
            else:
                # Fallback to bounding box center
                x, y, w, h = cv2.boundingRect(contour)
                cx = x + w // 2 + section_coords['x']
                cy = y + h // 2 + section_coords['y']
            
            # Classify symbol type based on properties
            symbol_type = self._classify_symbol(properties)
            
            symbol = {
                'id': i,
                'contour': contour.tolist(),  # Convert to list for JSON serialization
                'area': area,
                'center': (cx, cy),
                'type': symbol_type,
                'properties': properties,
                'bounding_box': cv2.boundingRect(contour),
                'section': section['name']
            }
            
            symbols.append(symbol)
        
        return symbols
    
    def _calculate_contour_properties(self, contour: np.ndarray) -> Dict:
        """
        Calculate geometric properties of a contour
        
        Args:
            contour: Input contour
            
        Returns:
            Dict: Dictionary of geometric properties
        """
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Aspect ratio
        aspect_ratio = float(w) / h if h != 0 else 0
        
        # Extent (ratio of contour area to bounding rectangle area)
        rect_area = w * h
        extent = float(area) / rect_area if rect_area != 0 else 0
        
        # Solidity (ratio of contour area to convex hull area)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area != 0 else 0
        
        # Equivalent diameter
        equiv_diameter = np.sqrt(4 * area / np.pi)
        
        # Circularity (4π * area / perimeter²)
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter != 0 else 0
        
        return {
            'area': area,
            'perimeter': perimeter,
            'aspect_ratio': aspect_ratio,
            'extent': extent,
            'solidity': solidity,
            'equiv_diameter': equiv_diameter,
            'circularity': circularity,
            'width': w,
            'height': h
        }
    
    def _is_valid_symbol(self, properties: Dict) -> bool:
        """
        Determine if contour properties indicate a valid symbol
        
        Args:
            properties: Dictionary of contour properties
            
        Returns:
            bool: True if valid symbol, False otherwise
        """
        # Filter by solidity (how "filled" the shape is)
        if properties['solidity'] < self.solidity_threshold:
            return False
        
        # Filter by aspect ratio (avoid very thin lines)
        if properties['aspect_ratio'] < self.aspect_ratio_threshold or properties['aspect_ratio'] > (1/self.aspect_ratio_threshold):
            return False
        
        # Filter by extent (avoid shapes that don't fill their bounding box well)
        if properties['extent'] < 0.2:
            return False
        
        return True
    
    def _classify_symbol(self, properties: Dict) -> str:
        """
        Classify symbol type based on geometric properties
        
        Args:
            properties: Dictionary of contour properties
            
        Returns:
            str: Symbol type classification
        """
        # Simple classification based on shape characteristics
        circularity = properties['circularity']
        aspect_ratio = properties['aspect_ratio']
        solidity = properties['solidity']
        
        # Circle-like symbols
        if circularity > 0.7 and abs(aspect_ratio - 1.0) < 0.3:
            return "Circular"
        
        # Square/Rectangle-like symbols
        elif solidity > 0.8 and (abs(aspect_ratio - 1.0) < 0.2 or abs(aspect_ratio - 1.0) > 0.5):
            if abs(aspect_ratio - 1.0) < 0.2:
                return "Square"
            else:
                return "Rectangle"
        
        # Triangle-like symbols
        elif solidity < 0.7 and circularity < 0.6:
            return "Triangle"
        
        # Complex shapes
        elif solidity < 0.8:
            return "Complex"
        
        # Default classification
        else:
            return "Other"
    
    def get_detection_statistics(self, symbols: List[Dict]) -> Dict:
        """
        Calculate statistics for detected symbols
        
        Args:
            symbols: List of detected symbols
            
        Returns:
            Dict: Statistics summary
        """
        if not symbols:
            return {'total': 0, 'types': {}, 'average_area': 0}
        
        # Count by type
        type_counts = {}
        total_area = 0
        
        for symbol in symbols:
            symbol_type = symbol['type']
            type_counts[symbol_type] = type_counts.get(symbol_type, 0) + 1
            total_area += symbol['area']
        
        average_area = total_area / len(symbols)
        
        return {
            'total': len(symbols),
            'types': type_counts,
            'average_area': average_area,
            'total_area': total_area
        }
