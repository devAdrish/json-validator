import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ValidationError, StrictStr, StrictInt

class VideoPresenter(BaseModel):
    avatar: str
    name: str
    role: str

class Video(BaseModel):
    link: str
    thumbnailImage: Optional[str] = None
    title: str
    kicker: str
    duration: StrictStr | StrictInt
    presentedBy: Optional[VideoPresenter] = None

class CTAStyle(BaseModel):
    backgroundColor: str
    textColor: str
    borderColor: str

class HTML(BaseModel):
    fileName: str
    backgroundColor: str
    ctaStyle: CTAStyle

class HighlightTier(BaseModel):
    description: str
    value: str

class Highlight(BaseModel):
    title: str
    value: Optional[str] = None
    tiers: Optional[List[HighlightTier]] = None

class InvestmentDocument(BaseModel):
    title: str
    link: str

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
    pricePerShareDisclaimer: Optional[str] = None
    chain: List[ChainItem]

class MainItem(BaseModel):
    html: Optional[HTML] = None
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
    investmentDocsPlacement: str
    investmentDocs: Optional[List[InvestmentDocument]] = None
    latestUpdateDocs: Optional[List[InvestmentDocument]] = None
    ownershipBreakdown: Optional[OwnershipBreakdown] = None
    video: Optional[Video] = None

# Pydantic inserts a branch tag (e.g. 'str', 'int') into `loc` for each arm of a
# union field. We drop those so errors for the same field group by their real location.
_UNION_TAGS = {"str", "int", "float", "bool"}

def format_friendly_error(item_name, loc, raw_msg, types=None):
    """Translates a raw Pydantic error into readable, human-friendly text."""
    path_parts = [f"(Item {p + 1})" if isinstance(p, int) else str(p) for p in loc]
    readable_path = " -> ".join(path_parts)

    if types:
        friendly_msg = f"Wrong data type (should be {' or '.join(types)})."
    elif raw_msg == "Field required":
        friendly_msg = "This field is missing but is required."
    elif "should be a valid" in raw_msg:
        friendly_msg = f"Wrong data type ({raw_msg})."
    else:
        friendly_msg = raw_msg

    return f"❌ [{item_name}]\n   Location: {readable_path}\n   Issue:    {friendly_msg}\n\n"

def validate_json_data(json_data):
    """Returns (success_bool, message_or_error_text)."""
    if not isinstance(json_data, dict):
        return False, "❌ Top level of JSON must be an object (dictionary).\n"

    all_errors = []

    if "__disclaimers" not in json_data:
        all_errors.append("❌ [Top Level]\n   Location: __disclaimer\n   Issue:    This field is missing but is required.\n\n")

    for item_name, item_data in json_data.items():
        if item_name.startswith("__"):
            continue
        if not isinstance(item_data, dict):
            all_errors.append(
                f"❌ [{item_name}]\n   Location: (top level)\n"
                f"   Issue:    Expected an object, but got {type(item_data).__name__}.\n\n"
            )
            continue
        try:
            MainItem(**item_data)
        except ValidationError as e:
            # Group errors by field location, collecting the accepted types so a
            # union field (e.g. str | int) reports as a single "should be a or b".
            grouped = {}  # loc -> {"msg": str, "types": [str]}
            for error in e.errors():
                loc = tuple(p for p in error['loc'] if p not in _UNION_TAGS)
                g = grouped.setdefault(loc, {"msg": error['msg'], "types": []})
                if "should be a valid" in error['msg']:
                    g["types"].append(error['msg'].split("should be a valid")[-1].strip())
            for loc, g in grouped.items():
                types = list(dict.fromkeys(g["types"]))
                all_errors.append(format_friendly_error(item_name, loc, g["msg"], types))

    if not all_errors:
        return True, "✅ Validation Passed! All data matches your template perfectly."
    return False, "".join(all_errors)


class ValidatorApp:
    def __init__(self, root):
        self.root = root
        root.title("JSON Validator")
        root.geometry("720x520")
        root.minsize(560, 400)

        self.file_label_var = tk.StringVar(value="No file selected")
        self.status_var = tk.StringVar(value="")

        top_frame = tk.Frame(root, pady=12, padx=20)
        top_frame.pack(fill=tk.X)

        file_lbl = tk.Label(top_frame, textvariable=self.file_label_var,
                            font=("Arial", 12, "bold"), anchor="w")
        file_lbl.pack(fill=tk.X)

        btn_frame = tk.Frame(root, padx=20)
        btn_frame.pack(fill=tk.X)

        self.open_btn = tk.Button(btn_frame, text="Open JSON File…",
                                  command=self.on_open, width=20,
                                  font=("Arial", 11))
        self.open_btn.pack(side=tk.LEFT, pady=(0, 8))

        self.progress = ttk.Progressbar(btn_frame, mode="indeterminate", length=180)

        status_lbl = tk.Label(root, textvariable=self.status_var,
                              font=("Arial", 11, "bold"), anchor="w", padx=20)
        status_lbl.pack(fill=tk.X)
        self.status_lbl = status_lbl

        text_frame = tk.Frame(root, padx=20, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set,
                                   wrap=tk.WORD, font=("Courier", 12),
                                   state=tk.DISABLED, height=14)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)

    def set_results(self, text, color):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert(tk.END, text)
        self.text_widget.config(state=tk.DISABLED, fg=color)

    def clear_results(self):
        self.status_var.set("")
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def start_loading(self):
        self.open_btn.config(state=tk.DISABLED)
        self.progress.pack(side=tk.LEFT, padx=10, pady=(0, 8))
        self.progress.start(10)
        self.status_var.set("Validating…")
        self.status_lbl.config(fg="black")

    def stop_loading(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.open_btn.config(state=tk.NORMAL)

    def on_open(self):
        file_path = filedialog.askopenfilename(
            title="Select a JSON File to Validate",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return

        self.file_label_var.set(f"File: {os.path.basename(file_path)}")
        self.clear_results()
        self.start_loading()

        thread = threading.Thread(target=self._run_validation, args=(file_path,), daemon=True)
        thread.start()

    def _run_validation(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            success, message = validate_json_data(json_data)
            self.root.after(0, self._on_done, success, message)
        except json.JSONDecodeError as e:
            self.root.after(0, self._on_done, False, f"❌ The file is not valid JSON.\nError: {str(e)}")
        except Exception as e:
            self.root.after(0, self._on_done, False, f"❌ An unexpected error occurred:\n{str(e)}")

    def _on_done(self, success, message):
        self.stop_loading()
        if success:
            self.status_var.set("Validation Passed")
            self.status_lbl.config(fg="#0a7d2c")
            self.set_results(message, "#0a7d2c")
        else:
            self.status_var.set("Validation Failed")
            self.status_lbl.config(fg="#b00020")
            self.set_results(message, "#b00020")


def main():
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass

    root = tk.Tk()
    ValidatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()