import frappe
from frappe.utils import flt

def update_file_details(doc, method=None):
    if not doc.file:
        return

    # Fetch corresponding File record
    file_info = frappe.db.get_value("File", {"file_url": doc.file}, ["file_type", "file_size"], as_dict=True)
    
    if file_info:
        # 1. Handle File Size
        size = flt(file_info.file_size)
        if size < 1024:
            doc.file_size = f"{int(size)} B"
        elif size < 1024 * 1024:
            doc.file_size = f"{round(size / 1024, 1)} KB"
        else:
            doc.file_size = f"{round(size / (1024 * 1024), 1)} MB"
        
        # 2. Handle File Type (Short version like PDF, ZIP)
        ext = file_info.extension or ""
        if ext:
            doc.file_type = ext.replace('.', '').upper()
        elif file_info.file_type:
            doc.file_type = file_info.file_type.upper()
        else:
            # Fallback to URL extension
            url_parts = doc.file.split('.')
            if len(url_parts) > 1:
                doc.file_type = url_parts[-1].upper()
