import frappe


# =====================================================
# DELETE ITEMS (ITEM-XXXXXX)
# =====================================================
def delete_items():
    items = frappe.get_all(
        "Item",
        filters={"item_code": ["like", "ITEM-%"]},
        pluck="name"
    )

    for name in items:
        try:
            frappe.delete_doc("Item", name, ignore_permissions=True, force=True)
        except Exception:
            pass

    frappe.db.commit()
    print(f"Deleted Items: {len(items)}")


# =====================================================
# DELETE WAREHOUSES (Test Warehouse)
# =====================================================
def delete_warehouses():
    whs = frappe.get_all(
        "Warehouse",
        filters={"warehouse_name": ["like", "Test Warehouse%"]},
        pluck="name"
    )

    for name in whs:
        try:
            frappe.delete_doc("Warehouse", name, ignore_permissions=True, force=True)
        except Exception:
            pass

    frappe.db.commit()
    print(f"Deleted Warehouses: {len(whs)}")


# =====================================================
# DELETE CUSTOMERS (heuristic cleanup)
# =====================================================
def delete_customers():
    customers = frappe.get_all("Customer", pluck="name")

    count = 0
    for name in customers:
        try:
            doc = frappe.get_doc("Customer", name)

            # heuristic: Faker company names are usually multi-word
            if doc.customer_name and len(doc.customer_name.split()) > 1:
                frappe.delete_doc("Customer", name, ignore_permissions=True, force=True)
                count += 1
        except Exception:
            pass

    frappe.db.commit()
    print(f"Deleted Customers: {count}")


# =====================================================
# DELETE SUPPLIERS (heuristic cleanup)
# =====================================================
def delete_suppliers():
    suppliers = frappe.get_all("Supplier", pluck="name")

    count = 0
    for name in suppliers:
        try:
            doc = frappe.get_doc("Supplier", name)

            if doc.supplier_name and len(doc.supplier_name.split()) > 1:
                frappe.delete_doc("Supplier", name, ignore_permissions=True, force=True)
                count += 1
        except Exception:
            pass

    frappe.db.commit()
    print(f"Deleted Suppliers: {count}")


# =====================================================
# DELETE SALES PERSONS
# =====================================================
def delete_sales_persons():
    persons = frappe.get_all("Sales Person", pluck="name")

    for name in persons:
        try:
            frappe.delete_doc("Sales Person", name, ignore_permissions=True, force=True)
        except Exception:
            pass

    frappe.db.commit()
    print(f"Deleted Sales Persons: {len(persons)}")


# =====================================================
# MAIN RUNNER
# =====================================================
def run_cleanup():
    print("🧹 Starting ERPNext test data cleanup...\n")

    delete_items()
    delete_warehouses()
    delete_customers()
    delete_suppliers()
    delete_sales_persons()

    print("\n✅ Cleanup completed successfully!")