import frappe
import random
import string
import os
import requests
import time
from faker import Faker

fake = Faker()

PUBLIC_FILE_PATH = frappe.get_site_path("public", "files")


# =====================================================
# STEP 1: FETCH REAL PRODUCT DATA WITH IMAGES
# =====================================================
# =====================================================
# UPDATED: FETCH ONLY FROM DUMMYJSON (More Reliable)
# =====================================================
def fetch_real_products():
    """Fetch real product data with images from APIs"""
    
    print("\n🔍 Fetching real products with images...")
    print("=" * 70)
    
    all_products = []
    
    # Source 1: DummyJSON API (Best quality, real products)
    print("\n📦 Fetching from DummyJSON API...")
    dummyjson_products = fetch_from_dummyjson()
    all_products.extend(dummyjson_products)
    print(f"✅ Got {len(dummyjson_products)} products from DummyJSON")
    
    # Source 2: Fake Store API (OPTIONAL - may be blocked)
    # Commented out to avoid network issues
    # print("\n📦 Fetching from Fake Store API...")
    # fakestore_products = fetch_from_fakestore()
    # all_products.extend(fakestore_products)
    # print(f"✅ Got {len(fakestore_products)} products from Fake Store")
    
    print(f"\n✅ Total products fetched: {len(all_products)}")
    print("=" * 70)
    
    return all_products


def fetch_from_dummyjson():
    """Fetch products from DummyJSON - has real product images"""
    
    products = []
    
    try:
        # Fetch all products (limit 100)
        print("  🔗 Connecting to DummyJSON...")
        response = requests.get("https://dummyjson.com/products?limit=100", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"  📦 Processing {len(data.get('products', []))} products...")
            
            for item in data.get("products", []):
                # Extract brand or use Generic
                brand = item.get("brand")
                if brand:
                    ensure_brand_exists(brand)
                else:
                    brand = "Generic"
                    ensure_brand_exists(brand)
                
                # Map to our structure
                product = {
                    "name": item.get("title"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "price": item.get("price"),
                    "image_url": item.get("thumbnail") or (item.get("images", [None])[0]),
                    "brand": brand,
                    "stock": item.get("stock", 100),
                    "rating": item.get("rating", 4.0),
                    "source": "dummyjson"
                }
                
                # Determine ERPNext item group
                product["item_group"] = map_category_to_item_group(product["category"])
                
                products.append(product)
            
            print(f"  ✅ Processed {len(products)} products")
                
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Network error: Cannot reach DummyJSON API")
        print(f"  💡 Check your network settings or firewall")
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout: DummyJSON API took too long")
    except Exception as e:
        print(f"  ⚠️ DummyJSON error: {str(e)[:100]}")
        try:
            frappe.log_error(str(e)[:100], "DummyJSON Fetch Error")
        except:
            pass
    
    return products


def fetch_from_fakestore():
    """Fetch products from Fake Store API (OPTIONAL)"""
    
    products = []
    
    # Map of fake store categories to brands
    category_brands = {
        "electronics": ["Samsung", "Sony", "LG", "Apple", "Dell"],
        "men's clothing": ["Nike", "Adidas", "Tommy Hilfiger", "Calvin Klein", "Levi's"],
        "women's clothing": ["Zara", "H&M", "Mango", "Forever 21", "Uniqlo"],
        "jewelery": ["Gucci", "Prada", "Chanel", "Louis Vuitton"]
    }
    
    try:
        print("  🔗 Connecting to Fake Store API...")
        response = requests.get("https://fakestoreapi.com/products", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data:
                # Assign brand based on category
                category = item.get("category", "").lower()
                brand = "Premium"
                
                if category in category_brands:
                    brand = random.choice(category_brands[category])
                
                ensure_brand_exists(brand)
                
                product = {
                    "name": item.get("title"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "price": item.get("price"),
                    "image_url": item.get("image"),
                    "brand": brand,
                    "stock": random.randint(50, 200),
                    "rating": item.get("rating", {}).get("rate", 4.0),
                    "source": "fakestore"
                }
                
                product["item_group"] = map_category_to_item_group(product["category"])
                
                products.append(product)
            
            print(f"  ✅ Processed {len(products)} products")
                
    except requests.exceptions.ConnectionError:
        print(f"  ⚠️ Network error: Cannot reach Fake Store API (skipping)")
    except requests.exceptions.Timeout:
        print(f"  ⚠️ Timeout from Fake Store API (skipping)")
    except Exception as e:
        print(f"  ⚠️ Fake Store error: {str(e)[:100]}")
    
    return products


# =====================================================
# FALLBACK: CREATE PRODUCTS MANUALLY IF API FAILS
# =====================================================
def create_fallback_products():
    """Create products manually if API fetch fails"""
    
    print("\n⚠️ API fetch failed. Creating products manually...")
    
    products = [
        # Electronics
        {
            "name": "Samsung Galaxy S24",
            "description": "Latest Samsung flagship smartphone with amazing camera",
            "category": "smartphones",
            "price": 899,
            "image_url": "https://picsum.photos/seed/phone1/400/400",
            "brand": "Samsung",
            "stock": 50,
            "rating": 4.5,
            "source": "manual",
            "item_group": "Electronics"
        },
        {
            "name": "Apple iPhone 15 Pro",
            "description": "Premium iPhone with titanium design",
            "category": "smartphones",
            "price": 999,
            "image_url": "https://picsum.photos/seed/iphone/400/400",
            "brand": "Apple",
            "stock": 30,
            "rating": 4.8,
            "source": "manual",
            "item_group": "Electronics"
        },
        {
            "name": "Dell XPS 15 Laptop",
            "description": "High-performance laptop for professionals",
            "category": "laptops",
            "price": 1299,
            "image_url": "https://picsum.photos/seed/laptop1/400/400",
            "brand": "Dell",
            "stock": 25,
            "rating": 4.6,
            "source": "manual",
            "item_group": "Electronics"
        },
        {
            "name": "Sony WH-1000XM5 Headphones",
            "description": "Industry-leading noise canceling headphones",
            "category": "audio",
            "price": 399,
            "image_url": "https://picsum.photos/seed/headphones/400/400",
            "brand": "Sony",
            "stock": 40,
            "rating": 4.7,
            "source": "manual",
            "item_group": "Electronics"
        },
        # Fashion
        {
            "name": "Nike Air Max Sneakers",
            "description": "Comfortable running shoes with air cushioning",
            "category": "shoes",
            "price": 150,
            "image_url": "https://picsum.photos/seed/nike/400/400",
            "brand": "Nike",
            "stock": 60,
            "rating": 4.4,
            "source": "manual",
            "item_group": "Fashion"
        },
        {
            "name": "Levi's 501 Jeans",
            "description": "Classic straight fit jeans",
            "category": "mens-clothing",
            "price": 80,
            "image_url": "https://picsum.photos/seed/jeans/400/400",
            "brand": "Levi's",
            "stock": 100,
            "rating": 4.3,
            "source": "manual",
            "item_group": "Fashion"
        },
        {
            "name": "Adidas Backpack",
            "description": "Durable sports backpack with laptop compartment",
            "category": "accessories",
            "price": 60,
            "image_url": "https://picsum.photos/seed/backpack/400/400",
            "brand": "Adidas",
            "stock": 75,
            "rating": 4.2,
            "source": "manual",
            "item_group": "Fashion"
        },
    ]
    
    # Ensure brands exist
    for product in products:
        ensure_brand_exists(product["brand"])
    
    return products

def map_category_to_item_group(category):
    """Map API category to ERPNext Item Group"""
    
    if not category:
        return "All Item Groups"
    
    category_lower = category.lower()
    
    mapping = {
        # Electronics
        "smartphones": "Electronics",
        "laptops": "Electronics",
        "electronics": "Electronics",
        "tablets": "Electronics",
        "mobile-accessories": "Electronics",
        "automotive": "Electronics",
        
        # Fashion
        "mens-shirts": "Fashion",
        "womens-dresses": "Fashion",
        "mens-shoes": "Fashion",
        "womens-shoes": "Fashion",
        "womens-bags": "Fashion",
        "mens-watches": "Fashion",
        "womens-watches": "Fashion",
        "sunglasses": "Fashion",
        "men's clothing": "Fashion",
        "women's clothing": "Fashion",
        "jewelery": "Fashion",
        
        # Furniture
        "furniture": "Furniture",
        "home-decoration": "Furniture",
        "lighting": "Furniture",
        
        # Beauty
        "beauty": "Beauty",
        "fragrances": "Beauty",
        "skin-care": "Beauty",
        
        # Grocery
        "groceries": "Grocery",
        
        # Sports
        "sports-accessories": "Sports",
    }
    
    for key, value in mapping.items():
        if key in category_lower:
            return value
    
    return "All Item Groups"


# =====================================================
# STEP 2: DOWNLOAD AND SAVE IMAGES
# =====================================================
# =====================================================
# IMPROVED IMAGE DOWNLOAD WITH BETTER ERROR HANDLING
# =====================================================
def download_product_image(product_name, image_url):
    """Download image from URL and save to ERPNext"""
    
    if not image_url:
        return None
    
    # Create safe filename
    safe_name = product_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ('_', '-'))
    file_name = f"{safe_name[:30]}_{random.randint(1000, 9999)}.jpg"
    file_path = os.path.join(PUBLIC_FILE_PATH, file_name)
    
    # Ensure directory exists
    os.makedirs(PUBLIC_FILE_PATH, exist_ok=True)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(image_url, timeout=20, headers=headers, stream=True)
        
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 500:  # At least 500 bytes
                    return f"/files/{file_name}"
                else:
                    os.remove(file_path)
        
    except requests.exceptions.ConnectionError:
        print(f"    ⚠️ Network unreachable for image")
        # Don't log - just skip silently
    except requests.exceptions.Timeout:
        print(f"    ⚠️ Image download timeout")
    except Exception as e:
        # Log with truncated message to avoid error
        error_msg = str(e)[:100]  # Truncate to 100 chars
        try:
            frappe.log_error(error_msg, f"Image Error: {product_name[:50]}")
        except:
            pass  # If logging fails, just continue
    
    return None
# =====================================================
# STEP 3: SETUP ITEM ATTRIBUTES
# =====================================================
def setup_item_attributes():
    """Create Item Attributes for variants"""
    
    print("\n🔧 Setting up Item Attributes...")
    
    attributes = [
        {
            "name": "Storage",
            "values": [
                {"value": "64GB", "abbr": "64G"},
                {"value": "128GB", "abbr": "128"},
                {"value": "256GB", "abbr": "256"},
                {"value": "512GB", "abbr": "512"},
                {"value": "1TB", "abbr": "1TB"},
            ]
        },
        {
            "name": "Size",
            "values": [
                {"value": "XS", "abbr": "XS"},
                {"value": "S", "abbr": "S"},
                {"value": "M", "abbr": "M"},
                {"value": "L", "abbr": "L"},
                {"value": "XL", "abbr": "XL"},
                {"value": "XXL", "abbr": "2XL"}
            ]
        },
        {
            "name": "Color",
            "values": [
                {"value": "Black", "abbr": "BLK"},
                {"value": "White", "abbr": "WHT"},
                {"value": "Blue", "abbr": "BLU"},
                {"value": "Red", "abbr": "RED"},
                {"value": "Gray", "abbr": "GRY"},
                {"value": "Navy", "abbr": "NVY"},
                {"value": "Green", "abbr": "GRN"},
                {"value": "Silver", "abbr": "SLV"},
            ]
        },
        {
            "name": "RAM",
            "values": [
                {"value": "4GB", "abbr": "4GB"},
                {"value": "8GB", "abbr": "8GB"},
                {"value": "16GB", "abbr": "16G"},
                {"value": "32GB", "abbr": "32G"},
            ]
        },
    ]
    
    for attr in attributes:
        if not frappe.db.exists("Item Attribute", attr["name"]):
            try:
                attr_doc = frappe.get_doc({
                    "doctype": "Item Attribute",
                    "attribute_name": attr["name"],
                    "item_attribute_values": [
                        {"attribute_value": val["value"], "abbr": val["abbr"]}
                        for val in attr["values"]
                    ]
                })
                attr_doc.insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"✅ Created attribute: {attr['name']}")
            except Exception as e:
                print(f"⚠️ Attribute {attr['name']}: {e}")
        else:
            print(f"⏭️  Attribute exists: {attr['name']}")
    
    frappe.db.commit()
    print("✅ Attributes ready!\n")


# =====================================================
# STEP 4: CREATE ITEMS FROM REAL PRODUCT DATA
# =====================================================
def create_items_from_products(products, with_variants=True):
    """Create ERPNext items from fetched product data"""
    
    print("\n📦 Creating Items from Real Products...")
    print("=" * 70)
    
    items_created = 0
    variants_created = 0
    
    for idx, product in enumerate(products, 1):
        print(f"\n[{idx}/{len(products)}] {product['name']}")
        
        # Generate item code
        item_code = f"ITEM-{random.randint(10000, 99999)}"
        
        # Get or create item group
        item_group = ensure_item_group_exists(product['item_group'])
        
        # Download image
        print(f"  📸 Downloading image...")
        image_path = download_product_image(product['name'], product['image_url'])
        
        if image_path:
            print(f"  ✅ Image saved")
        else:
            print(f"  ⚠️ No image")
        
        # Decide if this product should have variants
        should_have_variants = with_variants and should_create_variants(product)
        
        if should_have_variants:
            # Create template + variants
            template_code = create_item_template(item_code, product, item_group)
            
            if template_code:
                variant_count = create_product_variants(
                    template_code, 
                    product, 
                    item_group, 
                    image_path
                )
                variants_created += variant_count
                print(f"  ✅ Created template + {variant_count} variants")
        else:
            # Create simple item
            success = create_simple_item(
                item_code,
                product,
                item_group,
                image_path
            )
            
            if success:
                items_created += 1
                print(f"  ✅ Created item")
    
    frappe.db.commit()
    
    print("\n" + "=" * 70)
    print(f"✅ Created {items_created} simple items")
    print(f"✅ Created {variants_created} variant items")
    print("=" * 70)


def should_create_variants(product):
    """Determine if product should have variants"""
    
    category = product.get('category', '').lower()
    
    # Products that commonly have variants
    variant_categories = [
        'smartphone', 'laptop', 'tablet', 'watch',
        'clothing', 'shirt', 'dress', 'shoe', 'bag'
    ]
    
    for cat in variant_categories:
        if cat in category:
            return random.random() > 0.5  # 50% chance
    
    return False


def create_item_template(item_code, product, item_group):
    """Create variant template"""
    
    # Determine attributes based on category
    category = product.get('category', '').lower()
    
    attributes = []
    if 'smartphone' in category or 'laptop' in category or 'tablet' in category:
        attributes = ["Storage", "Color"]
    elif 'clothing' in category or 'shirt' in category or 'dress' in category:
        attributes = ["Size", "Color"]
    else:
        attributes = ["Color"]
    
    attributes_table = [{"attribute": attr} for attr in attributes]
    
    try:
        template = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": product['name'],
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "has_variants": 1,
            "variant_based_on": "Item Attribute",
            "attributes": attributes_table,
            "description": product.get('description', '')
        })
        template.insert(ignore_permissions=True)
        frappe.db.commit()
        return item_code
        
    except Exception as e:
        print(f"  ❌ Template error: {e}")
        frappe.log_error(frappe.get_traceback(), "Template Creation Error")
        return None


def create_product_variants(template_code, product, item_group, base_image):
    """Create variants for a product"""
    
    category = product.get('category', '').lower()
    variants_created = 0
    
    # Define variant combinations based on category
    if 'smartphone' in category or 'laptop' in category or 'tablet' in category:
        variant_combinations = [
            {"Storage": "128GB", "Color": "Black"},
            {"Storage": "256GB", "Color": "Blue"},
            {"Storage": "512GB", "Color": "Silver"},
        ]
    elif 'clothing' in category or 'shirt' in category:
        variant_combinations = [
            {"Size": "M", "Color": "Black"},
            {"Size": "L", "Color": "White"},
            {"Size": "XL", "Color": "Blue"},
        ]
    else:
        variant_combinations = [
            {"Color": "Black"},
            {"Color": "White"},
            {"Color": "Blue"},
        ]
    
    base_price = product.get('price', 50)
    
    for variant_attrs in variant_combinations:
        # Build variant name and code
        variant_parts = [product['name']]
        for attr_val in variant_attrs.values():
            variant_parts.append(str(attr_val))
        variant_name = " ".join(variant_parts)
        
        variant_suffix = "-".join([v.replace(" ", "")[:4].upper() for v in variant_attrs.values()])
        variant_code = f"{template_code}-{variant_suffix}"
        
        # Build attributes
        variant_attributes = [
            {"attribute": attr_name, "attribute_value": attr_value}
            for attr_name, attr_value in variant_attrs.items()
        ]
        
        try:
            variant_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": variant_code,
                "item_name": variant_name,
                "item_group": item_group,
                "stock_uom": "Nos",
                "is_stock_item": 1,
                "variant_of": template_code,
                "attributes": variant_attributes,
                "image": base_image,
                "description": product.get('description', '')
            })
            variant_doc.insert(ignore_permissions=True)
            
            # Create price for variant
            create_item_price_bdt(variant_code, base_price * random.uniform(0.95, 1.05))
            
            variants_created += 1
            
        except Exception as e:
            print(f"  ❌ Variant error: {e}")
    
    frappe.db.commit()
    return variants_created


def create_simple_item(item_code, product, item_group, image_path):
    """Create a simple item without variants"""
    
    try:
        item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": product['name'],
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 1,
            "image": image_path,
            "description": product.get('description', ''),
            "brand": product.get('brand', '')
        })
        item_doc.insert(ignore_permissions=True)
        
        # Create price
        create_item_price_bdt(item_code, product.get('price', 50))
        
        frappe.db.commit()
        return True
        
    except Exception as e:
        print(f"  ❌ Item error: {e}")
        frappe.log_error(frappe.get_traceback(), "Item Creation Error")
        return False


def ensure_item_group_exists(group_name):
    """Ensure item group exists, create if not"""
    
    if not frappe.db.exists("Item Group", group_name):
        try:
            parent = frappe.db.get_value("Item Group", {"is_group": 1}, "name") or "All Item Groups"
            
            group_doc = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group_name,
                "parent_item_group": parent,
                "is_group": 0
            })
            group_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            print(f"⚠️ Could not create group {group_name}: {e}")
            return "All Item Groups"
    
    return group_name


# =====================================================
# STEP 5: CREATE ITEM PRICES IN BDT
# =====================================================
def create_item_price_bdt(item_code, usd_price):
    """Create item price in BDT (Bangladeshi Taka)"""
    
    # USD to BDT conversion rate (approximate)
    USD_TO_BDT = 110.0
    
    # Convert USD to BDT
    bdt_price = usd_price * USD_TO_BDT
    
    # Round to nearest 10 BDT
    bdt_price = round(bdt_price / 10) * 10
    
    # Make it end in .00 or .50
    if random.random() > 0.7:
        bdt_price = round(bdt_price / 50) * 50
    
    price_lists = ["Standard Selling", "Retail", "Wholesale"]
    
    for price_list in price_lists:
        # Ensure price list exists
        ensure_price_list_exists(price_list)
        
        # Different multipliers for different price lists
        multipliers = {
            "Standard Selling": 1.0,
            "Retail": 1.15,
            "Wholesale": 0.85
        }
        
        final_price = bdt_price * multipliers.get(price_list, 1.0)
        
        if not frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list}):
            try:
                price_doc = frappe.get_doc({
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "price_list": price_list,
                    "price_list_rate": final_price,
                    "currency": "BDT"
                })
                price_doc.insert(ignore_permissions=True)
            except Exception as e:
                print(f"  ⚠️ Price error: {e}")
    
    frappe.db.commit()


def ensure_price_list_exists(price_list_name):
    """Ensure price list exists"""
    
    if not frappe.db.exists("Price List", price_list_name):
        try:
            buying = 1 if "buying" in price_list_name.lower() else 0
            selling = 1 if not buying else 0
            
            pl_doc = frappe.get_doc({
                "doctype": "Price List",
                "price_list_name": price_list_name,
                "buying": buying,
                "selling": selling,
                "enabled": 1,
                "currency": "BDT"
            })
            pl_doc.insert(ignore_permissions=True)
            frappe.db.commit()
        except:
            pass


# =====================================================
# CUSTOMERS & SUPPLIERS
# =====================================================
def create_customers(count=20):
    """Create customers with images"""
    
    print("\n🏢 Creating Customers...")
    
    cg = get_customer_group()
    terr = get_territory()
    
    for i in range(count):
        name = fake.company()
        
        # Use a placeholder for company logos
        image_url = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=400&background=random"
        image_path = download_product_image(name, image_url)
        
        try:
            safe_insert("Customer", {
                "customer_name": name,
                "customer_type": "Company",
                "customer_group": cg,
                "territory": terr,
                "image": image_path
            })
        except Exception as e:
            print(f"⚠️ Customer error: {e}")
    
    print(f"✅ Created {count} customers")


def create_suppliers(count=15):
    """Create suppliers with images"""
    
    print("\n🏭 Creating Suppliers...")
    
    sg = get_supplier_group()
    
    for i in range(count):
        name = fake.company()
        
        image_url = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=400&background=random&color=fff"
        image_path = download_product_image(name, image_url)
        
        try:
            safe_insert("Supplier", {
                "supplier_name": name,
                "supplier_type": "Company",
                "supplier_group": sg,
                "image": image_path
            })
        except Exception as e:
            print(f"⚠️ Supplier error: {e}")
    
    print(f"✅ Created {count} suppliers")


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def safe_insert(doctype, data):
    try:
        doc = frappe.get_doc({"doctype": doctype, **data})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Insert Error: {doctype}")
        return None


def get_customer_group():
    return frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Individual"

def get_territory():
    return frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"

def get_supplier_group():
    return frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"


def create_warehouses():
    """Create warehouses"""
    
    print("\n🏢 Creating Warehouses...")
    
    company = frappe.defaults.get_global_default("company")
    warehouses = ["Main Warehouse", "Dhaka Warehouse", "Chittagong Warehouse", "Online Store"]
    
    for wh in warehouses:
        if not frappe.db.exists("Warehouse", {"warehouse_name": wh}):
            safe_insert("Warehouse", {
                "warehouse_name": wh,
                "company": company,
                "is_group": 0
            })
    
    print("✅ Warehouses created")


def create_sales_persons():
    """Create sales persons"""
    
    print("\n👤 Creating Sales Persons...")
    
    for i in range(5):
        name = fake.name()
        if not frappe.db.exists("Sales Person", {"sales_person_name": name}):
            safe_insert("Sales Person", {
                "sales_person_name": name,
                "enabled": 1
            })
    
    print("✅ Sales persons created")


# =====================================================
# MAIN EXECUTION
# =====================================================
# =====================================================
# BRAND CREATION
# =====================================================
def create_brands():
    """Create popular brands"""
    
    print("\n🏷️ Creating Brands...")
    
    brands = [
        # Electronics Brands
        "Apple", "Samsung", "Dell", "HP", "Lenovo", "Asus", "Acer",
        "Sony", "LG", "Xiaomi", "OnePlus", "Huawei", "Google", "Microsoft",
        "Canon", "Nikon", "Bose", "JBL", "Beats", "Logitech",
        
        # Fashion Brands
        "Nike", "Adidas", "Puma", "Reebok", "Under Armour", "New Balance",
        "Zara", "H&M", "Gucci", "Louis Vuitton", "Prada", "Chanel",
        "Tommy Hilfiger", "Calvin Klein", "Ralph Lauren", "Levi's",
        "Gap", "Uniqlo", "Forever 21", "Mango",
        
        # Generic Brands
        "Generic", "Premium", "Pro", "Elite", "Classic", "Deluxe",
        "Standard", "Basic", "Essence", "Pure"
    ]
    
    created = 0
    
    for brand_name in brands:
        if not frappe.db.exists("Brand", brand_name):
            try:
                brand_doc = frappe.get_doc({
                    "doctype": "Brand",
                    "brand": brand_name
                })
                brand_doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠️ Brand {brand_name}: {e}")
        else:
            print(f"  ⏭️  Brand exists: {brand_name}")
    
    frappe.db.commit()
    print(f"✅ Created {created} new brands")


def ensure_brand_exists(brand_name):
    """Ensure a brand exists, create if not"""
    
    if not brand_name:
        return None
    
    if not frappe.db.exists("Brand", brand_name):
        try:
            brand_doc = frappe.get_doc({
                "doctype": "Brand",
                "brand": brand_name
            })
            brand_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return brand_name
        except Exception as e:
            frappe.log_error(str(e), f"Brand Creation Error: {brand_name}")
            return None
    
    return brand_name


# =====================================================
# UPDATE fetch_from_dummyjson to extract brands
# =====================================================
def fetch_from_dummyjson():
    """Fetch products from DummyJSON - has real product images"""
    
    products = []
    
    try:
        # Fetch all products (limit 100)
        response = requests.get("https://dummyjson.com/products?limit=100", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get("products", []):
                # Extract brand or use Generic
                brand = item.get("brand")
                if brand:
                    ensure_brand_exists(brand)  # Create brand if doesn't exist
                else:
                    brand = "Generic"
                    ensure_brand_exists(brand)
                
                # Map to our structure
                product = {
                    "name": item.get("title"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "price": item.get("price"),
                    "image_url": item.get("thumbnail") or (item.get("images", [None])[0]),
                    "brand": brand,
                    "stock": item.get("stock", 100),
                    "rating": item.get("rating", 4.0),
                    "source": "dummyjson"
                }
                
                # Determine ERPNext item group
                product["item_group"] = map_category_to_item_group(product["category"])
                
                products.append(product)
                
    except Exception as e:
        print(f"⚠️ DummyJSON error: {e}")
        frappe.log_error(str(e), "DummyJSON Fetch Error")
    
    return products


# =====================================================
# UPDATE fetch_from_fakestore
# =====================================================
def fetch_from_fakestore():
    """Fetch products from Fake Store API"""
    
    products = []
    
    # Map of fake store categories to brands
    category_brands = {
        "electronics": ["Samsung", "Sony", "LG", "Apple", "Dell"],
        "men's clothing": ["Nike", "Adidas", "Tommy Hilfiger", "Calvin Klein", "Levi's"],
        "women's clothing": ["Zara", "H&M", "Mango", "Forever 21", "Uniqlo"],
        "jewelery": ["Gucci", "Prada", "Chanel", "Louis Vuitton"]
    }
    
    try:
        response = requests.get("https://fakestoreapi.com/products", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data:
                # Assign brand based on category
                category = item.get("category", "").lower()
                brand = "Premium"
                
                if category in category_brands:
                    brand = random.choice(category_brands[category])
                
                ensure_brand_exists(brand)
                
                product = {
                    "name": item.get("title"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "price": item.get("price"),
                    "image_url": item.get("image"),
                    "brand": brand,
                    "stock": random.randint(50, 200),
                    "rating": item.get("rating", {}).get("rate", 4.0),
                    "source": "fakestore"
                }
                
                product["item_group"] = map_category_to_item_group(product["category"])
                
                products.append(product)
                
    except Exception as e:
        print(f"⚠️ Fake Store error: {e}")
        frappe.log_error(str(e), "FakeStore Fetch Error")
    
    return products


# =====================================================
# UPDATE run_all WITH FALLBACK
# =====================================================
def run_all(with_variants=True):
    """
    Complete workflow with fallback if APIs fail
    """
    
    print("\n" + "=" * 70)
    print("🚀 ERPNext Test Data Generator - Real Products with Matching Images")
    print("=" * 70)
    
    # Step 0: Create brands FIRST
    create_brands()
    
    # Step 1: Fetch real product data (with fallback)
    products = fetch_real_products()
    
    # Fallback if no products fetched
    if not products or len(products) < 10:
        print("\n⚠️ Few or no products from API. Using fallback products...")
        products = create_fallback_products()
    
    if not products:
        print("❌ No products available. Cannot continue.")
        return
    
    # Step 2: Setup attributes
    setup_item_attributes()
    
    # Step 3: Create items from real products
    create_items_from_products(products, with_variants=with_variants)
    
    # Step 4: Create other data
    create_customers(20)
    create_suppliers(15)
    create_warehouses()
    create_sales_persons()
    
    frappe.db.commit()
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE! Your ERPNext now has:")
    print("   • Real products with matching images")
    print("   • Prices in BDT (Bangladeshi Taka)")
    print("   • Product variants (if enabled)")
    print("   • Popular brands")
    print("   • Customers & Suppliers")
    print("=" * 70)

# =====================================================
# STANDALONE BRAND CREATION (if needed)
# =====================================================
def create_brands_only():
    """Just create brands without creating items"""
    create_brands()
    check_brand_stats()


def check_brand_stats():
    """Show brand statistics"""
    
    print("\n📊 Brand Statistics")
    print("=" * 70)
    
    brands = frappe.get_all("Brand", fields=["brand", "name"])
    
    print(f"Total Brands: {len(brands)}")
    
    if brands:
        print("\nBrands created:")
        for b in brands[:20]:  # Show first 20
            print(f"  • {b.brand}")
        
        if len(brands) > 20:
            print(f"  ... and {len(brands) - 20} more")
    
    print("=" * 70)


# =====================================================
# BULK BRAND IMPORT FROM API
# =====================================================
def import_brands_from_api():
    """Import brands from DummyJSON to get real brand names"""
    
    print("\n🔍 Importing brands from API...")
    
    try:
        response = requests.get("https://dummyjson.com/products?limit=100", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            brands = set()
            
            for item in data.get("products", []):
                brand = item.get("brand")
                if brand:
                    brands.add(brand)
            
            print(f"Found {len(brands)} unique brands from API")
            
            created = 0
            for brand_name in brands:
                if ensure_brand_exists(brand_name):
                    created += 1
            
            print(f"✅ Created {created} new brands")
            frappe.db.commit()
            
    except Exception as e:
        print(f"⚠️ Error importing brands: {e}")


# =====================================================
# STATISTICS
# =====================================================
def check_stats():
    """Show statistics of created data"""
    
    print("\n📊 Data Statistics")
    print("=" * 70)
    
    items = frappe.db.count("Item", {"has_variants": 0, "disabled": 0})
    templates = frappe.db.count("Item", {"has_variants": 1})
    with_images = frappe.db.count("Item", {"has_variants": 0, "disabled": 0, "image": ["!=", ""]})
    
    customers = frappe.db.count("Customer")
    suppliers = frappe.db.count("Supplier")
    prices = frappe.db.count("Item Price", {"currency": "BDT"})
    brands = frappe.db.count("Brand")
    
    print(f"Items: {items}")
    print(f"Templates: {templates}")
    print(f"Items with images: {with_images} ({with_images/items*100 if items > 0 else 0:.1f}%)")
    print(f"Customers: {customers}")
    print(f"Suppliers: {suppliers}")
    print(f"Prices (BDT): {prices}")
    print(f"Brands: {brands}")
    print("=" * 70)