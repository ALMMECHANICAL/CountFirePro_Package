import numpy as np
from typing import Dict, List, Tuple, Any

class SectionManager:
    """Manages document sections and their properties"""
    
    def __init__(self):
        self.sections = []
    
    def create_section(self, name: str, canvas_rect: Dict, img_width: int, img_height: int) -> Dict:
        """
        Create a section from canvas rectangle data
        
        Args:
            name: Section name
            canvas_rect: Rectangle data from drawable canvas
            img_width: Original image width
            img_height: Original image height
            
        Returns:
            Dict: Section data with normalized coordinates
        """
        # Extract rectangle coordinates from canvas data
        left = canvas_rect.get('left', 0)
        top = canvas_rect.get('top', 0)
        width = canvas_rect.get('width', 100)
        height = canvas_rect.get('height', 100)
        
        # Get canvas dimensions
        canvas_width = canvas_rect.get('scaleX', 1.0)
        canvas_height = canvas_rect.get('scaleY', 1.0)
        
        # Create section data structure
        section = {
            'name': name,
            'coordinates': {
                'x': int(left),
                'y': int(top),
                'width': int(width),
                'height': int(height)
            },
            'normalized_coordinates': {
                'x': left / img_width if img_width > 0 else 0,
                'y': top / img_height if img_height > 0 else 0,
                'width': width / img_width if img_width > 0 else 0,
                'height': height / img_height if img_height > 0 else 0
            },
            'area': int(width * height),
            'created_at': None  # Could add timestamp if needed
        }
        
        return section
    
    def get_section_roi(self, image: np.ndarray, section: Dict) -> np.ndarray:
        """
        Extract region of interest from image based on section coordinates
        
        Args:
            image: Input image as numpy array
            section: Section data dictionary
            
        Returns:
            numpy.ndarray: ROI image section
        """
        coords = section['coordinates']
        
        # Ensure coordinates are within image bounds
        img_height, img_width = image.shape[:2]
        
        x = max(0, min(coords['x'], img_width - 1))
        y = max(0, min(coords['y'], img_height - 1))
        x2 = max(x + 1, min(x + coords['width'], img_width))
        y2 = max(y + 1, min(y + coords['height'], img_height))
        
        # Extract ROI
        roi = image[y:y2, x:x2]
        
        if roi.size == 0:
            # Return small dummy ROI if extraction failed
            return np.zeros((10, 10, 3) if len(image.shape) == 3 else (10, 10), dtype=image.dtype)
        
        return roi
    
    def get_section_mask(self, image_shape: Tuple, section: Dict) -> np.ndarray:
        """
        Create a binary mask for the section area
        
        Args:
            image_shape: Shape of the original image (height, width)
            section: Section data dictionary
            
        Returns:
            numpy.ndarray: Binary mask where section area is 1, rest is 0
        """
        mask = np.zeros(image_shape[:2], dtype=np.uint8)
        
        coords = section['coordinates']
        img_height, img_width = image_shape[:2]
        
        # Ensure coordinates are within bounds
        x = max(0, min(coords['x'], img_width - 1))
        y = max(0, min(coords['y'], img_height - 1))
        x2 = max(x + 1, min(x + coords['width'], img_width))
        y2 = max(y + 1, min(y + coords['height'], img_height))
        
        # Set section area to 1
        mask[y:y2, x:x2] = 1
        
        return mask
    
    def validate_section(self, section: Dict, image_shape: Tuple) -> bool:
        """
        Validate if section coordinates are valid for given image
        
        Args:
            section: Section data dictionary
            image_shape: Shape of the image (height, width)
            
        Returns:
            bool: True if section is valid, False otherwise
        """
        coords = section['coordinates']
        img_height, img_width = image_shape[:2]
        
        # Check if coordinates are within image bounds
        if (coords['x'] < 0 or coords['y'] < 0 or 
            coords['x'] >= img_width or coords['y'] >= img_height):
            return False
        
        # Check if section has positive dimensions
        if coords['width'] <= 0 or coords['height'] <= 0:
            return False
        
        # Check if section extends beyond image bounds
        if (coords['x'] + coords['width'] > img_width or 
            coords['y'] + coords['height'] > img_height):
            return False
        
        return True
    
    def get_section_info(self, section: Dict) -> Dict:
        """
        Get detailed information about a section
        
        Args:
            section: Section data dictionary
            
        Returns:
            Dict: Detailed section information
        """
        coords = section['coordinates']
        
        return {
            'name': section['name'],
            'area_pixels': section['area'],
            'dimensions': f"{coords['width']} x {coords['height']}",
            'top_left': f"({coords['x']}, {coords['y']})",
            'bottom_right': f"({coords['x'] + coords['width']}, {coords['y'] + coords['height']})",
            'center': f"({coords['x'] + coords['width']//2}, {coords['y'] + coords['height']//2})"
        }
