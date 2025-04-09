import os
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgRenderer

def load_svg_logo(svg_path, width=None, height=None):
    """Load an SVG file and convert it to a QPixmap of specified size."""
    if not os.path.exists(svg_path):
        return QPixmap()
        
    renderer = QSvgRenderer(svg_path)
    original_size = renderer.defaultSize()
    
    # Calculate dimensions while preserving aspect ratio
    if width is not None and height is None:
        # Scale based on width while preserving aspect ratio
        aspect_ratio = original_size.width() / original_size.height()
        height = int(width / aspect_ratio)
    elif height is not None and width is None:
        # Scale based on height while preserving aspect ratio
        aspect_ratio = original_size.width() / original_size.height()
        width = int(height * aspect_ratio)
    elif width is None and height is None:
        # Use original size
        width = original_size.width()
        height = original_size.height()
    
    # Create a pixmap to render to
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)  # Fill with transparent background
    
    # Create a painter to render with
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return pixmap 