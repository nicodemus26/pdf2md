import tkinter as tk
from tkinter import ttk
from src.draggable_treeview import DraggableTreeview
from src.pdf import Pdf
from src.canvas.pdf_canvas import PdfCanvas
from src.toolbar.pdf_viewer_toolbar import PdfViewerToolbar
from src.toolbar.pdf_viewer_toolbar_item import PdfViewerToolbarItem

class PDFViewer(tk.Frame):
    def __init__(self, pdf_path, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=1)

        # Load the PDF with PyMuPDF and pdfminer
        self.pdf = Pdf(pdf_path)

        # Create toolbar
        self.toolbar = PdfViewerToolbar(self)
        self.toolbar.bind("<<ToolbarButtonClicked>>", self.on_toolbar_button_clicked)

        # Create a PanedWindow with horizontal orientation
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill='both', expand=1)

        # Initialize Canvas
        self.canvas = PdfCanvas(self.paned_window, self.pdf)
        self.paned_window.add(self.canvas)
        self.canvas.bind("<<PageChanged>>", self.on_page_changed_by_canvas)
        self.canvas.bind("<<SafeAreaChanged>>", self.on_safe_area_changed_by_canvas)
        self.canvas.bind("<<DragEnd>>", self.on_drag_end_by_canvas)
        self.canvas.bind("<<ElementLeftClicked>>", self.on_element_left_clicked_by_canvas)
        self.canvas.bind("<<ElementRightClicked>>", self.on_element_right_clicked_by_canvas)

        # Initialize Text widget
        self.text_widget = tk.Text(self.paned_window, font=("Times New Roman", 11))
        self.text_widget.config(spacing3=7)
        self.text_widget.pack(fill="both", expand=True)
        self.paned_window.add(self.text_widget)

        # Add elements to the Text widget
        self.add_elements_to_text_widget()

        # Set the minimum size of the Text widget to 60% of the window width
        self.paned_window.update()
        self.paned_window.sashpos(0, 600)

        # Apply initial tool selection
        self.toolbar.toggle_button(PdfViewerToolbarItem.SafeArea)

    def add_elements_to_text_widget(self):
        self.text_widget.delete('1.0', tk.END)  # Clear the text widget

        for key, element in self.pdf.iter_elements_page(self.canvas.get_current_page()):
            if not element.safe or not element.visible:
                continue  # Skip unsafe or invisible elements
            self.text_widget.insert(tk.END, f'{element.text}\n')

    def add_elements_to_treeview(self):
        self.dtv.delete_all_items()

        for key, element in self.pdf.iter_elements():
            tags = ()
            if not element.safe or not element.visible:
                tags += ("unsafe",)
            if element.page_number % 2 == 0:
                tags += ("oddpage",)

            self.dtv.insert('', "end", key, values=(element.page_number, element.text), tags=tags)

    def on_treeview_select(self, event):
        # Get the selected item
        selection = self.dtv.selection()
        if selection:
            selected_item = selection[0]

            # Extract the page number from the selected item
            page_number, _ = self.dtv.item(selected_item, "values")

            self.canvas.change_page(int(page_number) - 1)

    def on_page_changed_by_canvas(self, event):
        self.add_elements_to_text_widget()

    def on_safe_area_changed_by_canvas(self, event):
        if self.toolbar.get_current_selection() != PdfViewerToolbarItem.SafeArea:
            return
        
        new_safe_margin = self.canvas.get_new_safe_margin()
        self.pdf.set_safe_margin(new_safe_margin)
        self.canvas.redraw()
        self.add_elements_to_text_widget()

    def on_drag_end_by_canvas(self, event):
        if self.toolbar.get_current_selection() == PdfViewerToolbarItem.Visibility:
            elements = self.canvas.get_selected_elements()
            for key in elements:
                self.pdf.toggle_visibility(key)
            self.canvas.redraw()
            self.add_elements_to_text_widget()
        elif self.toolbar.get_current_selection() == PdfViewerToolbarItem.MergeAndSplit:
            elements = self.canvas.get_selected_elements()
            self.pdf.merge(self.canvas.get_current_page(), elements)
            self.canvas.redraw()
            self.add_elements_to_text_widget()

    def on_element_left_clicked_by_canvas(self, event):
        if self.toolbar.get_current_selection() == PdfViewerToolbarItem.Visibility:
            key = self.canvas.get_clicked_element()
            self.pdf.toggle_visibility(key)
            self.canvas.redraw()
            self.add_elements_to_text_widget()

    def on_element_right_clicked_by_canvas(self, event):
        if self.toolbar.get_current_selection() == PdfViewerToolbarItem.MergeAndSplit:
            key = self.canvas.get_clicked_element()
            self.pdf.split_element(key)
            self.canvas.redraw()
            self.add_elements_to_text_widget()

    def on_toolbar_button_clicked(self, event):
        self.canvas.change_mode(self.toolbar.get_current_selection())