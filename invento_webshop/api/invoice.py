import frappe

@frappe.whitelist()
def get_sales_invoice_for_order(sales_order):
    """Get the Sales Invoice linked to a Sales Order and the configured print format"""
    
    # Get print format from Webshop Settings
    print_format = frappe.db.get_single_value(
        "Webshop Settings", 
        "default_sales_invoice_pdf_format"
    ) or "Invento Sales Invoice"  # fallback if not set
    
    # Find Sales Invoice Items linked to this Sales Order
    invoices = frappe.get_all(
        "Sales Invoice Item",
        filters={
            "sales_order": sales_order,
            "docstatus": 1
        },
        fields=["parent"],
        distinct=True
    )
    
    if not invoices:
        # Try finding via Sales Invoice directly with custom field
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={
                "custom_sales_order": sales_order,
                "docstatus": 1
            },
            fields=["name"],
            limit=1
        )
        if invoices:
            return {
                "success": True,
                "invoice_name": invoices[0]["name"],
                "print_format": print_format
            }
        
        # No invoice found - return gracefully instead of throwing
        return {
            "success": False,
            "message": "No invoice has been generated for this order yet. Please contact support if you believe this is an error."
        }
    
    return {
        "success": True,
        "invoice_name": invoices[0]["parent"],
        "print_format": print_format
    }