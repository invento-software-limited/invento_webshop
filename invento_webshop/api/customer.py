import frappe
from frappe import _
from erpnext.selling.doctype.customer.customer import parse_full_name

@frappe.whitelist()
def approve_customer(customer):
    customer = frappe.get_doc("Customer", customer)
    
    if customer.custom_is_approved:
        frappe.throw(_("Customer is already approved"))

    if not customer.tax_category:
        frappe.throw("Error: Value missing for Customer: Tax Category")
    
    contact_doc = None
    if customer.customer_primary_contact:
        contact_doc = frappe.get_doc("Contact", customer.customer_primary_contact)
    else:
        # Search for linked contacts and prioritize primary
        contact_links = frappe.get_all("Dynamic Link", filters={
            "link_doctype": "Customer", 
            "link_name": customer.name, 
            "parenttype": "Contact"
        }, fields=["parent"])
        
        contacts = []
        for link in contact_links:
            contacts.append(frappe.get_doc("Contact", link.parent))
            
        if contacts:
            contacts.sort(key=lambda x: x.is_primary_contact, reverse=True)
            contact_doc = contacts[0]
            # Link it to the customer record
            customer.customer_primary_contact = contact_doc.name
    
    email_id = None
    first_name = None
    last_name = None

    if contact_doc:
        first_name = contact_doc.first_name
        last_name = contact_doc.last_name
        
        # Determine primary email
        for e in contact_doc.email_ids:
            if e.is_primary:
                email_id = e.email_id
                break
        if not email_id and contact_doc.email_ids:
            email_id = contact_doc.email_ids[0].email_id
    
    # Fallback to customer name if contact details are missing
    if not first_name:
        first_name, middle_name, last_name = parse_full_name(customer.customer_name)
    
    if not email_id and customer.email_id:
        email_id = customer.email_id
        
    if not email_id:
        frappe.throw(_("No email address found for this Customer"))

    if frappe.db.exists("User", email_id):
        user = frappe.get_doc("User", email_id)
        # Ensure user has a name if missing
        if not user.first_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save(ignore_permissions=True)
    else:
        user = frappe.new_doc("User")
        user.email = email_id
        user.first_name = first_name
        user.last_name = last_name
        user.enabled = 1
        user.send_welcome_email = 1
        user.insert(ignore_permissions=True)
    
    if not frappe.db.exists("Portal User", {"parent": customer.name, "user": user.name}):
        customer.append("portal_users", {"user": user.name})
    
    customer.custom_is_approved = 1
    customer.save(ignore_permissions=True)
    
    return user.name
