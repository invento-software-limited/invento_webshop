import frappe


@frappe.whitelist()
def cancel_order(order_id):
    try:
        sales_order = frappe.get_doc("Sales Order", order_id)

        if sales_order.docstatus == 2:
            return {"status": "error", "message": "Sales Order is already canceled"}

        sales_order.cancel()

        return {"status": "success", "message": f"Sales Order {order_id} has been canceled"}

    except frappe.DoesNotExistError:
        return {"status": "error", "message": "Sales Order not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def reorder(order_id):
    try:
        sales_order = frappe.get_doc("Sales Order", order_id)

        if sales_order.docstatus != 2:
            return {"status": "error", "message": "Order is not canceled, can't reorder"}

        new_sales_order = frappe.copy_doc(sales_order)
        new_sales_order.docstatus = 0
        new_sales_order.status = "Draft"
        new_sales_order.amended_from = sales_order.name

        for item in new_sales_order.items:
            latest_price = frappe.get_value("Item Price",
                                            {"item_code": item.item_code, "price_list": sales_order.selling_price_list},
                                            "price_list_rate")
            if latest_price:
                item.rate = latest_price
                item.amount = item.qty * latest_price

        new_sales_order.insert()
        new_sales_order.submit()

        return {"status": "success",
                "message": f"New Sales Order {new_sales_order.name} has been created and submitted from canceled order {order_id}, with updated prices."}

    except frappe.DoesNotExistError:
        return {"status": "error", "message": "Sales Order not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
