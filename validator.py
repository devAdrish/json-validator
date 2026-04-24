import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ValidationError

class HighlightTier(BaseModel):
    description: str
    value: str

class Highlight(BaseModel):
    title: str
    value: Optional[str] = None
    tiers: Optional[List[HighlightTier]] = None

class AboutItem(BaseModel):
    title: str
    value: str
    colSpan: Optional[int] = None
    fullWidth: Optional[bool] = None

class KPI(BaseModel):
    title: str
    value: str
    webOnly: Optional[bool] = None

class Colors(BaseModel):
    base: List[float]
    brightest: List[float]
    highlight: List[float]
    border: List[float]
    subtle: List[float]

class ChainItem(BaseModel):
    type: str
    title: str
    subtitle: str
    meta: str

class OwnershipBreakdown(BaseModel):
    colors: Colors
    currency: str
    currencySymbol: str
    ownershipText: str
    chain: List[ChainItem]

class MainItem(BaseModel):
    subscription: str
    commitment: str
    highlights: List[Highlight]
    highlightsLabel: str
    about: List[AboutItem]
    aboutLabel: str
    kpis: List[KPI]
    coInvestors: List[Any] # Accepts empty list or a list of anything. Change if you have a specific structure.
    coInvestorsLabel: str
    companyThesis: List[Any]
    companyThesisLabel: str
    keyPersonel: List[Any]
    info: str
    note: str
    downloadLink: str
    latestUpdateLink: str
    downloadLinkPlacement: str
    ownershipBreakdown: Optional[OwnershipBreakdown] = None

def format_friendly_error(item_name, error):
    """Translates raw Pydantic errors into readable, human-friendly text."""
    loc = error['loc']
    raw_msg = error['msg']
    
    path_parts = []
    for p in loc:
        if isinstance(p, int):
            path_parts.append(f"(Item {p + 1})")
        else:
            path_parts.append(str(p))
            
    readable_path = " -> ".join(path_parts)
    
    if raw_msg == "Field required":
        friendly_msg = "This field is missing but is required."
    elif "Input should be a valid" in raw_msg:
        friendly_msg = f"Wrong data type ({raw_msg})."
    else:
        friendly_msg = raw_msg
        
    return f"❌ [{item_name}]\n   Location: {readable_path}\n   Issue:    {friendly_msg}\n\n"

def show_error_window(root, error_text):
    """Creates a custom, scrollable popup window that resizes to fit the errors."""
    error_win = tk.Toplevel(root)
    error_win.title("Validation Failed")
    
    # We removed error_win.geometry("600x450") so it can auto-resize
    
    lbl = tk.Label(error_win, text="The following errors were found in the JSON file:", fg="red", font=("Arial", 12, "bold"))
    lbl.pack(pady=10, padx=20)

    text_frame = tk.Frame(error_win)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Calculate how many lines of text we have
    line_count = error_text.count('\n')
    # Set the box height to match the text, but keep it between 4 and 20 lines tall
    dynamic_height = min(max(line_count, 4), 20)

    # Apply the dynamic height to the Text widget
    text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD, 
                          font=("Courier", 13), height=dynamic_height, width=65)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=text_widget.yview)

    text_widget.insert(tk.END, error_text)
    text_widget.config(state=tk.DISABLED)

    btn = tk.Button(error_win, text="Close", command=error_win.destroy, width=15)
    btn.pack(pady=10)

    error_win.wait_window()

def main():
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

    root = tk.Tk()
    root.withdraw() # Hide the empty background window

    file_path = filedialog.askopenfilename(
        title="Select a JSON File to Validate",
        filetypes=[("JSON Files", "*.json")]
    )

    if not file_path:
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            
        if not isinstance(json_data, dict):
            messagebox.showerror("Error", "Top level of JSON must be an object (dictionary).")
            return

        all_errors = []

        # Validate each top-level key
        for item_name, item_data in json_data.items():
            try:
                MainItem(**item_data)
            except ValidationError as e:
                for error in e.errors():
                    friendly_error = format_friendly_error(item_name, error)
                    all_errors.append(friendly_error)

        # Output results
        if not all_errors:
            messagebox.showinfo("Success!", "Validation Passed! All data matches your template perfectly.")
        else:
            # Combine all errors into one massive block of text
            full_error_text = "".join(all_errors)
            # Show our custom scrollable popup
            show_error_window(root, full_error_text)

    except json.JSONDecodeError as e:
        messagebox.showerror("JSON Format Error", f"The file is not valid JSON.\nError: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

if __name__ == "__main__":
    main()