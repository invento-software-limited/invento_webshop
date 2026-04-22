# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from urllib import robotparser
from urllib.parse import quote

import frappe
from frappe.model.document import get_controller
from frappe.utils import get_url, nowdate
from frappe.utils.caching import redis_cache
from frappe.website.router import get_doctypes_with_web_view, get_pages

from frappe.www.sitemap import get_public_pages_from_doctypes

no_cache = 1
base_template_path = "www/sitemap.xml"


def get_context(context):
    """generate the sitemap XML"""
    links = [
        {"loc": get_url(quote(page.name.encode("utf-8"))), "lastmod": nowdate()}
        for route, page in get_pages().items()
        if page.sitemap
    ]
    links.extend(
        {
            "loc": get_url(quote((route or "").encode("utf-8"))),
            "lastmod": f"{data['modified']:%Y-%m-%d}",
        }
        for route, data in get_public_pages_from_doctypes().items()
    )

    items = frappe.get_all(
        "Item",
        filters={"custom_publish_on_website": 1},
        fields=["custom_route", "modified"]
    )

    for item in items:
        if item.custom_route:
            links.append({
                "loc": get_url(quote(item.custom_route.encode("utf-8"))),
                "lastmod": f"{item.modified:%Y-%m-%d}"
            })

    return {"links": links}