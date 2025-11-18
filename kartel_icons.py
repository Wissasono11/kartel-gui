#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KARTEL - Icon Management Module
Handles SVG icon loading and processing for the dashboard

Author: KARTEL Team
Created: November 17, 2025
"""

import os
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtSvg import QSvgRenderer

class IconManager:
    """Manages SVG icon loading and processing"""
    
    def __init__(self, svg_path: str = "asset/svg"):
        self.svg_path = svg_path
        self.icon_cache = {}
        self.pixmap_cache = {}
    
    def get_svg_path(self, icon_name: str) -> str:
        """Get full path to SVG icon"""
        if not icon_name.endswith('.svg'):
            icon_name += '.svg'
        return os.path.join(self.svg_path, icon_name)
    
    def load_svg_as_pixmap(self, icon_name: str, size: QSize = QSize(24, 24), color: str = None) -> QPixmap:
        """Load SVG file as QPixmap with optional coloring"""
        cache_key = f"{icon_name}_{size.width()}x{size.height()}_{color}"
        
        if cache_key in self.pixmap_cache:
            return self.pixmap_cache[cache_key]
        
        svg_path = self.get_svg_path(icon_name)
        
        if not os.path.exists(svg_path):
            # Return empty pixmap if file doesn't exist
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            self.pixmap_cache[cache_key] = pixmap
            return pixmap
        
        # Load SVG
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Render SVG to pixmap
        renderer.render(painter)
        
        # Apply color if specified
        if color:
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
        
        painter.end()
        
        self.pixmap_cache[cache_key] = pixmap
        return pixmap
    
    def load_svg_as_icon(self, icon_name: str, size: QSize = QSize(24, 24), color: str = None) -> QIcon:
        """Load SVG file as QIcon"""
        cache_key = f"icon_{icon_name}_{size.width()}x{size.height()}_{color}"
        
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        pixmap = self.load_svg_as_pixmap(icon_name, size, color)
        icon = QIcon(pixmap)
        
        self.icon_cache[cache_key] = icon
        return icon
    
    def create_colored_icon(self, icon_name: str, color: str, size: QSize = QSize(24, 24)) -> QIcon:
        """Create a colored version of an icon"""
        return self.load_svg_as_icon(icon_name, size, color)
    
    def get_logo_pixmap(self, size: QSize = QSize(48, 48)) -> QPixmap:
        """Get KARTEL logo pixmap"""
        # Try to load logo SVG first, fallback to creating a simple logo
        logo_path = os.path.join(self.svg_path, "logo.svg")
        
        if os.path.exists(logo_path):
            return self.load_svg_as_pixmap("logo", size)
        else:
            # Create a simple logo pixmap with gradient background and text
            pixmap = QPixmap(size)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw background circle with gradient
            from PyQt5.QtGui import QLinearGradient, QBrush
            gradient = QLinearGradient(0, 0, size.width(), size.height())
            gradient.setColorAt(0, QColor("#FFD54F"))
            gradient.setColorAt(1, QColor("#FF8F00"))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, size.width(), size.height())
            
            # Draw egg emoji or K letter
            painter.setPen(QColor("#FFFFFF"))
            from PyQt5.QtGui import QFont
            font = QFont("Manrope", int(size.width() * 0.4))
            font.setWeight(QFont.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "🥚")
            
            painter.end()
            return pixmap
    
    def clear_cache(self):
        """Clear icon and pixmap cache"""
        self.icon_cache.clear()
        self.pixmap_cache.clear()

# Global icon manager instance
icon_manager = IconManager()

# Convenience functions
def get_icon(icon_name: str, size: QSize = None, color: str = None) -> QIcon:
    """Get icon by name"""
    if size is None:
        size = QSize(24, 24)
    return icon_manager.load_svg_as_icon(icon_name, size, color)

def get_pixmap(icon_name: str, size: QSize = None, color: str = None) -> QPixmap:
    """Get pixmap by name"""
    if size is None:
        size = QSize(24, 24)
    return icon_manager.load_svg_as_pixmap(icon_name, size, color)

def get_colored_icon(icon_name: str, color: str, size: QSize = None) -> QIcon:
    """Get colored icon"""
    if size is None:
        size = QSize(24, 24)
    return icon_manager.create_colored_icon(icon_name, color, size)

def get_logo() -> QPixmap:
    """Get KARTEL logo"""
    return icon_manager.get_logo_pixmap()

# Icon name constants for easier use
class Icons:
    """Icon name constants"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    HUMIDIFIER = "humidifier"
    HUMIDIFIER_CONTROL = "humidifier-control"
    PEMANAS = "pemanas"
    PEMANAS_CONTROL = "pemanas-control"
    SETTINGS = "settings"
    WIFI = "wifi"
    CALENDAR = "calendar"
    GRAPH = "graph"
    MOTOR_DINAMO = "motor-dinamo"
    SAND_CLOCK = "sand-clock"
    STATUS_SYSTEM = "status-system"
    USERNAME = "username"
    PASSWORD = "password"
    DROPDOWN = "dropdown"

# Pre-load commonly used icons
def preload_icons():
    """Preload commonly used icons for better performance"""
    common_icons = [
        Icons.TEMPERATURE,
        Icons.HUMIDITY,
        Icons.HUMIDIFIER,
        Icons.PEMANAS,
        Icons.SETTINGS,
        Icons.WIFI,
        Icons.CALENDAR,
        Icons.GRAPH,
        Icons.STATUS_SYSTEM
    ]
    
    common_colors = ["#FFFFFF", "#7C4DFF", "#FFA726", "#4CAF50", "#F44336"]
    common_sizes = [QSize(16, 16), QSize(24, 24), QSize(32, 32)]
    
    for icon_name in common_icons:
        for color in common_colors:
            for size in common_sizes:
                # Preload in background
                try:
                    icon_manager.load_svg_as_pixmap(icon_name, size, color)
                    icon_manager.load_svg_as_icon(icon_name, size, color)
                except:
                    # Ignore errors during preloading
                    pass

# Call preload when module is imported
if __name__ != "__main__":
    preload_icons()