#!/usr/bin/env python3
"""
CountFire Pro - Advanced Symbol Detection & Counting Desktop Application

A modern, fast desktop application for document symbol detection and counting.
Built to be faster and more powerful than web-based alternatives like Countfire.

Features:
- Advanced computer vision symbol detection
- Multi-document processing
- Real-time drawing with annotations
- Professional takeoff reports
- Offline functionality
- Exportable results to Excel/PDF
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import threading
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import numpy as np
import cv2
from PIL import Image, ImageTk, ImageDraw
import pandas as pd

# Import our existing modules
from document_processor import DocumentProcessor
from section_manager import SectionManager
from symbol_detector import SymbolDetector

# Set CustomTkinter appearance
ctk.set_appearance_mode("system")  # Modes: "system", "dark", "light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class CountFireProApp(ctk.CTk):
    """Main desktop application class"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("CountFire Pro - Professional Symbol Detection")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Initialize processors
        self.doc_processor = DocumentProcessor()
        self.section_manager = SectionManager()
        self.symbol_detector = SymbolDetector()
        
        # Application state
        self.current_document = None
        self.current_image = None
        self.sections = []
        self.symbol_results = {}
        self.canvas_scale = 1.0
        self.drawing_rectangles = []
        self.is_drawing = False
        self.start_x = None
        self.start_y = None
        
        # Setup UI
        self.setup_ui()
        
        # Load settings
        self.load_settings()
        
    def setup_ui(self):
        """Initialize the user interface"""
        
        # Create main layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.setup_sidebar()
        self.setup_main_content()
        
    def setup_sidebar(self):
        """Setup the left sidebar with controls"""
        
        # Logo and title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="CountFire Pro", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # File operations
        self.file_frame = ctk.CTkFrame(self.sidebar_frame)
        self.file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.file_frame, text="Document", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.upload_btn = ctk.CTkButton(
            self.file_frame,
            text="📁 Upload Document",
            command=self.upload_document,
            height=40
        )
        self.upload_btn.pack(pady=5, padx=10, fill="x")
        
        self.recent_files_combo = ctk.CTkComboBox(
            self.file_frame,
            values=["No recent files"],
            state="readonly"
        )
        self.recent_files_combo.pack(pady=5, padx=10, fill="x")
        
        # Section management
        self.section_frame = ctk.CTkFrame(self.sidebar_frame)
        self.section_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.section_frame, text="Sections", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.section_name_entry = ctk.CTkEntry(
            self.section_frame,
            placeholder_text="Section name..."
        )
        self.section_name_entry.pack(pady=5, padx=10, fill="x")
        
        self.add_section_btn = ctk.CTkButton(
            self.section_frame,
            text="➕ Add Section",
            command=self.add_current_section,
            height=32
        )
        self.add_section_btn.pack(pady=5, padx=10, fill="x")
        
        # Sections list
        self.sections_listbox = tk.Listbox(
            self.section_frame,
            height=6,
            bg="#212121",
            fg="white",
            selectbackground="#1f538d",
            relief="flat"
        )
        self.sections_listbox.pack(pady=5, padx=10, fill="x")
        
        self.delete_section_btn = ctk.CTkButton(
            self.section_frame,
            text="🗑️ Delete Selected",
            command=self.delete_selected_section,
            height=32,
            fg_color="darkred",
            hover_color="red"
        )
        self.delete_section_btn.pack(pady=5, padx=10, fill="x")
        
        # Symbol detection
        self.detection_frame = ctk.CTkFrame(self.sidebar_frame)
        self.detection_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.detection_frame, text="Detection", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Detection parameters
        ctk.CTkLabel(self.detection_frame, text="Min Area:").pack(pady=2)
        self.min_area_slider = ctk.CTkSlider(
            self.detection_frame,
            from_=50,
            to=1000,
            number_of_steps=19
        )
        self.min_area_slider.set(200)
        self.min_area_slider.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(self.detection_frame, text="Max Area:").pack(pady=2)
        self.max_area_slider = ctk.CTkSlider(
            self.detection_frame,
            from_=1000,
            to=10000,
            number_of_steps=18
        )
        self.max_area_slider.set(5000)
        self.max_area_slider.pack(pady=5, padx=10, fill="x")
        
        self.detect_btn = ctk.CTkButton(
            self.detection_frame,
            text="🎯 Detect Symbols",
            command=self.detect_symbols,
            height=40,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.detect_btn.pack(pady=10, padx=10, fill="x")
        
        # Results export
        self.export_frame = ctk.CTkFrame(self.sidebar_frame)
        self.export_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.export_frame, text="Export", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        self.export_excel_btn = ctk.CTkButton(
            self.export_frame,
            text="📊 Export to Excel",
            command=self.export_excel,
            height=32
        )
        self.export_excel_btn.pack(pady=5, padx=10, fill="x")
        
        self.export_pdf_btn = ctk.CTkButton(
            self.export_frame,
            text="📄 Export to PDF",
            command=self.export_pdf,
            height=32
        )
        self.export_pdf_btn.pack(pady=5, padx=10, fill="x")
        
        # Status
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=8, column=0, padx=20, pady=10)
        
    def setup_main_content(self):
        """Setup the main content area"""
        
        # Toolbar
        self.toolbar_frame = ctk.CTkFrame(self.main_frame, height=50)
        self.toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.toolbar_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas and scrollbars
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="white",
            cursor="crosshair"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Canvas event bindings
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_drawing)
        self.canvas.bind("<MouseWheel>", self.zoom_canvas)
        
        # Toolbar buttons
        toolbar_buttons = [
            ("🔍 Zoom In", self.zoom_in),
            ("🔍 Zoom Out", self.zoom_out),
            ("🔄 Reset View", self.reset_view),
            ("🧹 Clear Drawings", self.clear_drawings),
        ]
        
        for i, (text, command) in enumerate(toolbar_buttons):
            btn = ctk.CTkButton(
                self.toolbar_frame,
                text=text,
                command=command,
                width=120,
                height=32
            )
            btn.grid(row=0, column=i, padx=5, pady=10)
        
        # Results panel (initially hidden)
        self.results_frame = ctk.CTkFrame(self.main_frame)
        # Will be shown when results are available
        
    def upload_document(self):
        """Upload and process a document"""
        file_types = [
            ("All supported", "*.pdf *.png *.jpg *.jpeg"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.png *.jpg *.jpeg")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Document",
            filetypes=file_types
        )
        
        if filename:
            self.set_status("Processing document...")
            threading.Thread(
                target=self._process_document_thread,
                args=(filename,),
                daemon=True
            ).start()
    
    def _process_document_thread(self, filename):
        """Process document in a separate thread"""
        try:
            # Process the document
            with open(filename, 'rb') as file:
                self.current_image = self.doc_processor.process_document(file)
            
            # Update UI in main thread
            self.after(0, self._document_processed, filename)
            
        except Exception as e:
            self.after(0, self._document_error, str(e))
    
    def _document_processed(self, filename):
        """Handle successful document processing"""
        self.current_document = filename
        self.display_image()
        self.set_status(f"Loaded: {os.path.basename(filename)}")
        
        # Clear previous data
        self.sections = []
        self.symbol_results = {}
        self.drawing_rectangles = []
        self.update_sections_list()
        
    def _document_error(self, error_msg):
        """Handle document processing error"""
        messagebox.showerror("Error", f"Failed to process document:\n{error_msg}")
        self.set_status("Error loading document")
    
    def display_image(self):
        """Display the current image on canvas"""
        if self.current_image is None:
            return
        
        # Convert to PIL Image
        if isinstance(self.current_image, np.ndarray):
            if len(self.current_image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(self.current_image)
        else:
            pil_image = self.current_image
        
        # Scale image to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Canvas is initialized
            # Calculate scale to fit
            img_width, img_height = pil_image.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            self.canvas_scale = min(scale_x, scale_y, 1.0)  # Don't upscale
            
            # Resize image
            new_width = int(img_width * self.canvas_scale)
            new_height = int(img_height * self.canvas_scale)
            self.display_pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to Tkinter format
            self.tk_image = ImageTk.PhotoImage(self.display_pil_image)
            
            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            
            # Configure scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def start_drawing(self, event):
        """Start drawing a rectangle"""
        if self.current_image is None:
            return
        
        self.is_drawing = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
    
    def draw_rectangle(self, event):
        """Draw rectangle while dragging"""
        if not self.is_drawing:
            return
        
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        
        # Remove previous temporary rectangle
        self.canvas.delete("temp_rect")
        
        # Draw new temporary rectangle
        self.canvas.create_rectangle(
            self.start_x, self.start_y, current_x, current_y,
            outline="red", width=2, fill="", tags="temp_rect"
        )
    
    def end_drawing(self, event):
        """Finish drawing a rectangle"""
        if not self.is_drawing:
            return
        
        self.is_drawing = False
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Check if rectangle is large enough
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        
        if width > 10 and height > 10:
            # Convert canvas coordinates to image coordinates
            img_x1 = int(min(self.start_x, end_x) / self.canvas_scale)
            img_y1 = int(min(self.start_y, end_y) / self.canvas_scale)
            img_width = int(width / self.canvas_scale)
            img_height = int(height / self.canvas_scale)
            
            # Store rectangle
            rect_data = {
                'canvas_coords': (self.start_x, self.start_y, end_x, end_y),
                'image_coords': (img_x1, img_y1, img_width, img_height)
            }
            self.drawing_rectangles.append(rect_data)
            
            # Remove temporary rectangle and draw permanent one
            self.canvas.delete("temp_rect")
            self.canvas.create_rectangle(
                self.start_x, self.start_y, end_x, end_y,
                outline="red", width=2, fill="rgba(255,0,0,0.2)", tags="rectangle"
            )
            
            self.set_status(f"Rectangle drawn. Total: {len(self.drawing_rectangles)}")
        else:
            self.canvas.delete("temp_rect")
    
    def add_current_section(self):
        """Add the last drawn rectangle as a section"""
        section_name = self.section_name_entry.get().strip()
        
        if not section_name:
            messagebox.showwarning("Warning", "Please enter a section name")
            return
        
        if not self.drawing_rectangles:
            messagebox.showwarning("Warning", "Please draw a rectangle first")
            return
        
        # Check for duplicate names
        if any(s['name'] == section_name for s in self.sections):
            messagebox.showwarning("Warning", "Section name already exists")
            return
        
        # Get last drawn rectangle
        last_rect = self.drawing_rectangles[-1]
        img_x, img_y, img_width, img_height = last_rect['image_coords']
        
        # Create section data compatible with existing system
        drawable_rect = {
            "type": "rect",
            "left": img_x,
            "top": img_y,
            "width": img_width,
            "height": img_height
        }
        
        if self.current_image is not None:
            img_height_full, img_width_full = self.current_image.shape[:2]
            section_data = self.section_manager.create_section(
                section_name,
                drawable_rect,
                img_width_full,
                img_height_full
            )
            
            self.sections.append(section_data)
            self.update_sections_list()
            self.section_name_entry.delete(0, tk.END)
            self.set_status(f"Section '{section_name}' added")
    
    def update_sections_list(self):
        """Update the sections listbox"""
        self.sections_listbox.delete(0, tk.END)
        for section in self.sections:
            self.sections_listbox.insert(tk.END, section['name'])
    
    def delete_selected_section(self):
        """Delete the selected section"""
        selection = self.sections_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        section_name = self.sections[index]['name']
        
        # Remove from lists
        del self.sections[index]
        if section_name in self.symbol_results:
            del self.symbol_results[section_name]
        
        self.update_sections_list()
        self.set_status(f"Section '{section_name}' deleted")
    
    def detect_symbols(self):
        """Detect symbols in all sections"""
        if not self.sections:
            messagebox.showwarning("Warning", "Please add at least one section first")
            return
        
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please upload a document first")
            return
        
        self.set_status("Detecting symbols...")
        threading.Thread(
            target=self._detect_symbols_thread,
            daemon=True
        ).start()
    
    def _detect_symbols_thread(self):
        """Detect symbols in a separate thread"""
        try:
            min_area = int(self.min_area_slider.get())
            max_area = int(self.max_area_slider.get())
            
            results = {}
            for section in self.sections:
                section_results = self.symbol_detector.detect_symbols_in_section(
                    self.current_image,
                    section,
                    min_area=min_area,
                    max_area=max_area
                )
                results[section['name']] = section_results
            
            self.after(0, self._symbols_detected, results)
            
        except Exception as e:
            self.after(0, self._detection_error, str(e))
    
    def _symbols_detected(self, results):
        """Handle successful symbol detection"""
        self.symbol_results = results
        self.show_results()
        
        total_symbols = sum(len(r['symbols']) for r in results.values())
        self.set_status(f"Detection complete: {total_symbols} symbols found")
    
    def _detection_error(self, error_msg):
        """Handle symbol detection error"""
        messagebox.showerror("Error", f"Symbol detection failed:\n{error_msg}")
        self.set_status("Detection failed")
    
    def show_results(self):
        """Show detection results"""
        if not self.symbol_results:
            return
        
        # Create results window
        results_window = ctk.CTkToplevel(self)
        results_window.title("Symbol Detection Results")
        results_window.geometry("800x600")
        
        # Results text
        text_widget = tk.Text(
            results_window,
            bg="#212121",
            fg="white",
            font=("Courier", 11)
        )
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Generate results text
        results_text = "SYMBOL DETECTION RESULTS\n"
        results_text += "=" * 50 + "\n\n"
        
        total_symbols = 0
        for section_name, results in self.symbol_results.items():
            symbol_count = len(results['symbols'])
            total_symbols += symbol_count
            
            results_text += f"Section: {section_name}\n"
            results_text += f"Symbols found: {symbol_count}\n"
            
            if results['symbols']:
                results_text += "Details:\n"
                for i, symbol in enumerate(results['symbols'][:10]):  # Show first 10
                    results_text += f"  #{i+1}: Area={symbol['area']}, Type={symbol['type']}\n"
                if len(results['symbols']) > 10:
                    results_text += f"  ... and {len(results['symbols']) - 10} more\n"
            
            results_text += "\n" + "-" * 30 + "\n\n"
        
        results_text += f"TOTAL SYMBOLS: {total_symbols}\n"
        results_text += f"SECTIONS PROCESSED: {len(self.symbol_results)}\n"
        results_text += f"TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        text_widget.insert("1.0", results_text)
        text_widget.configure(state="disabled")
    
    def export_excel(self):
        """Export results to Excel"""
        if not self.symbol_results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Excel Report",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if filename:
            try:
                # Create Excel report
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_data = []
                    for section_name, results in self.symbol_results.items():
                        summary_data.append({
                            'Section': section_name,
                            'Symbol Count': len(results['symbols']),
                            'Processing Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Detail sheets for each section
                    for section_name, results in self.symbol_results.items():
                        if results['symbols']:
                            detail_data = []
                            for i, symbol in enumerate(results['symbols']):
                                detail_data.append({
                                    'Symbol ID': i + 1,
                                    'Area': symbol['area'],
                                    'Center X': symbol['center'][0],
                                    'Center Y': symbol['center'][1],
                                    'Type': symbol['type']
                                })
                            
                            detail_df = pd.DataFrame(detail_data)
                            detail_df.to_excel(writer, sheet_name=f"{section_name[:30]}", index=False)
                
                messagebox.showinfo("Success", f"Results exported to:\n{filename}")
                self.set_status("Excel export completed")
                
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")
    
    def export_pdf(self):
        """Export results to PDF"""
        messagebox.showinfo("Info", "PDF export feature coming soon!")
    
    def zoom_in(self):
        """Zoom into the canvas"""
        self.canvas_scale *= 1.25
        self.display_image()
    
    def zoom_out(self):
        """Zoom out of the canvas"""
        self.canvas_scale /= 1.25
        self.display_image()
    
    def zoom_canvas(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def reset_view(self):
        """Reset canvas view to original"""
        self.canvas_scale = 1.0
        self.display_image()
    
    def clear_drawings(self):
        """Clear all drawn rectangles"""
        self.canvas.delete("rectangle")
        self.canvas.delete("temp_rect")
        self.drawing_rectangles = []
        self.set_status("Drawings cleared")
    
    def set_status(self, message):
        """Update status message"""
        self.status_label.configure(text=message)
        self.update_idletasks()
    
    def load_settings(self):
        """Load application settings"""
        # Placeholder for settings loading
        pass
    
    def save_settings(self):
        """Save application settings"""
        # Placeholder for settings saving
        pass
    
    def on_closing(self):
        """Handle application closing"""
        self.save_settings()
        self.destroy()

def main():
    """Main application entry point"""
    app = CountFireProApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()