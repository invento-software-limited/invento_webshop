import frappe

@frappe.whitelist(methods=['DELETE'])
def delete_address(name):
    try:
        frappe.delete_doc("Address", name)
        return {"message": "Address deleted"}
    except Exception as e:
        frappe.log_error(f"Failed to delete address {name}: {str(e)}", "Address Delete Failed")

        try:
            doc = frappe.get_doc("Address", name)
            doc.disabled = 1
            doc.save(ignore_permissions=True)
            return {"message": "Address could not be deleted, so it was disabled instead"}
        except Exception as inner_e:
            frappe.log_error(f"Also failed to disable address {name}: {str(inner_e)}", "Address Disable Failed")
            frappe.throw("Failed to delete or disable the address.")
