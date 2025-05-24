"""
Complete GUI implementation for CipherCraft.

This file contains the complete implementation of the GUI class with all methods.
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, font, messagebox
from src.services.cipher_service import CipherService


class CipherGUI:
    """
    A GUI application for encryption and decryption using multiple cipher algorithms.

    This class is responsible only for UI interactions and delegates
    all cipher operations to the CipherService.
    """

    # Modern color palette
    COLORS = {
        'primary': '#2D3E50',      # Dark blue-gray
        'secondary': '#1ABC9C',    # Teal
        'accent': '#3498DB',       # Blue
        'danger': '#E74C3C',       # Red
        'warning': '#F39C12',      # Orange
        'success': '#2ECC71',      # Green
        'light': '#ECF0F1',        # Light gray
        'dark': '#2C3E50',         # Dark blue-gray
        'text': '#34495E',         # Dark gray-blue
        'bg': '#F5F7FA'            # Light background
    }

    # Spacing scale (in pixels)
    SPACING = {
        'xs': 2,
        'sm': 5,
        'md': 10,
        'lg': 20,
        'xl': 30
    }

    def __init__(self, root):
        """
        Initialize the GUI components.

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("CipherCraft")
        self.root.configure(bg=self.COLORS['bg'])
        
        # Set minimum window size
        self.root.minsize(800, 700)
        
        # Initialize the service layer
        self.cipher_service = CipherService()
        
        # Setup custom fonts
        self._setup_fonts()
        
        # Create custom styles for ttk widgets
        self._create_styles()
        
        # Create and configure the UI components
        self._create_widgets()
        self._layout_widgets()
    
    def _setup_fonts(self):
        """Setup custom fonts for the application."""
        # Store fonts as instance variables for later use
        self.font_heading = font.Font(
            family='Arial', size=18, weight='bold')
        self.font_subheading = font.Font(
            family='Arial', size=12, weight='bold')
        self.font_body = font.Font(
            family='Arial', size=10)
        self.font_small = font.Font(
            family='Arial', size=9)
        self.font_button = font.Font(
            family='Arial', size=10, weight='bold')
        self.font_code = font.Font(
            family='Courier New', size=10)
    
    def _create_styles(self):
        """Create custom ttk styles for widgets."""
        style = ttk.Style()
        
        # Configure the overall theme
        style.theme_use('clam')  # Use a modern-looking base theme
        
        # Configure TLabel
        style.configure(
            'TLabel',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TFrame
        style.configure(
            'TFrame',
            background=self.COLORS['bg']
        )
        
        # Configure TLabelframe
        style.configure(
            'TLabelframe',
            background=self.COLORS['bg'],
            foreground=self.COLORS['primary'],
            font=self.font_subheading
        )
        style.configure(
            'TLabelframe.Label',
            background=self.COLORS['bg'],
            foreground=self.COLORS['primary'],
            font=self.font_subheading
        )
        
        # Configure TButton
        style.configure(
            'TButton',
            background=self.COLORS['primary'],
            foreground=self.COLORS['light'],
            font=self.font_button,
            padding=(self.SPACING['md'], self.SPACING['sm'])
        )
        
        # Special button styles
        style.configure(
            'Primary.TButton',
            background=self.COLORS['primary'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Success.TButton',
            background=self.COLORS['success'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Accent.TButton',
            background=self.COLORS['accent'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Warning.TButton',
            background=self.COLORS['warning'],
            foreground='white',
            font=self.font_button
        )
        
        # Configure TRadiobutton
        style.configure(
            'TRadiobutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TCheckbutton
        style.configure(
            'TCheckbutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TEntry
        style.configure(
            'TEntry',
            fieldbackground='white',
            foreground=self.COLORS['text'],
            font=self.font_body,
            padding=self.SPACING['sm']
        )