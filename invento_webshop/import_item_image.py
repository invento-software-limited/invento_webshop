
# =====================================================
# CREATE ITEM PRICES
# =====================================================
def create_item_prices():
    """Create realistic price lists for all items"""
    
    print("\n💰 Creating Item Prices...")
    
    # Get or create Price Lists
    price_lists = setup_price_lists()
    
    # Get all items (excluding templates)
    items = frappe.get_all(
        "Item",
        filters={"has_variants": 0, "disabled": 0},
        fields=["name", "item_name", "item_group"]
    )
    
    if not items:
        print("⚠️ No items found to create prices for")
        return
    
    prices_created = 0
    
    for item in items:
        # Generate base price based on item group
        base_price = generate_realistic_price(item.get("item_group"), item.get("item_name"))
        
        # Create prices for each price list
        for price_list in price_lists:
            # Apply multiplier for different price lists
            multiplier = price_lists[price_list]["multiplier"]
            final_price = base_price * multiplier
            
            # Check if price already exists
            if not frappe.db.exists("Item Price", {
                "item_code": item.name,
                "price_list": price_list
            }):
                try:
                    price_doc = frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": item.name,
                        "price_list": price_list,
                        "price_list_rate": final_price,
                        "currency": "USD"  # Change to your currency
                    })
                    price_doc.insert(ignore_permissions=True)
                    prices_created += 1
                    
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), "Item Price Creation Error")
                    print(f"❌ Price error for {item.name}: {e}")
    
    frappe.db.commit()
    print(f"✅ Created {prices_created} item prices!")


def setup_price_lists():
    """Create or get standard price lists"""
    
    price_lists = {
        "Standard Selling": {
            "buying": 0,
            "selling": 1,
            "multiplier": 1.0,
            "currency": "USD"
        },
        "Retail": {
            "buying": 0,
            "selling": 1,
            "multiplier": 1.15,  # 15% markup
            "currency": "USD"
        },
        "Wholesale": {
            "buying": 0,
            "selling": 1,
            "multiplier": 0.85,  # 15% discount
            "currency": "USD"
        },
        "Standard Buying": {
            "buying": 1,
            "selling": 0,
            "multiplier": 0.70,  # 30% discount from selling
            "currency": "USD"
        }
    }
    
    for pl_name, pl_data in price_lists.items():
        if not frappe.db.exists("Price List", pl_name):
            try:
                pl_doc = frappe.get_doc({
                    "doctype": "Price List",
                    "price_list_name": pl_name,
                    "buying": pl_data["buying"],
                    "selling": pl_data["selling"],
                    "enabled": 1,
                    "currency": pl_data["currency"]
                })
                pl_doc.insert(ignore_permissions=True)
                print(f"✅ Created price list: {pl_name}")
            except Exception as e:
                print(f"⚠️ Price list {pl_name} error: {e}")
    
    frappe.db.commit()
    return price_lists


def generate_realistic_price(item_group, item_name):
    """Generate realistic prices based on product category"""
    
    # Base prices by category
    price_ranges = {
        "Electronics": {
            "laptop": (800, 3000),
            "phone": (500, 1500),
            "smartphone": (500, 1500),
            "iphone": (800, 1800),
            "samsung": (600, 1400),
            "ipad": (400, 1200),
            "tablet": (300, 900),
            "headphones": (50, 400),
            "airpods": (150, 250),
            "earbuds": (30, 200),
            "watch": (200, 800),
            "smartwatch": (200, 800),
            "mouse": (15, 100),
            "keyboard": (30, 200),
            "monitor": (150, 1000),
            "camera": (400, 3000),
            "cable": (5, 30),
            "power bank": (20, 80),
            "default": (50, 500)
        },
        "Fashion": {
            "shoes": (40, 200),
            "sneakers": (50, 250),
            "boot": (60, 300),
            "shirt": (15, 80),
            "tshirt": (10, 50),
            "jeans": (30, 150),
            "jacket": (50, 300),
            "wallet": (20, 150),
            "bag": (30, 200),
            "backpack": (40, 180),
            "handbag": (50, 500),
            "suitcase": (80, 400),
            "sunglasses": (20, 300),
            "default": (20, 100)
        },
        "Furniture": {
            "chair": (80, 600),
            "desk": (150, 1200),
            "lamp": (25, 150),
            "bookshelf": (100, 500),
            "table": (100, 800),
            "sofa": (400, 2000),
            "default": (50, 500)
        },
        "Sports": {
            "mat": (15, 80),
            "yoga": (15, 80),
            "dumbbell": (20, 150),
            "weight": (30, 200),
            "bottle": (10, 40),
            "bag": (25, 100),
            "default": (15, 100)
        },
        "Stationery": {
            "notebook": (3, 25),
            "pen": (2, 50),
            "pencil": (1, 15),
            "organizer": (10, 60),
            "default": (5, 30)
        },
        "Kitchen": {
            "coffee": (30, 300),
            "blender": (40, 200),
            "toaster": (25, 150),
            "cookware": (50, 300),
            "fryer": (60, 250),
            "default": (25, 200)
        }
    }
    
    # Default fallback
    min_price, max_price = 20, 200
    
    # Try to match item group
    if item_group in price_ranges:
        # Check item name for specific keywords
        item_name_lower = item_name.lower() if item_name else ""
        
        for keyword, price_range in price_ranges[item_group].items():
            if keyword in item_name_lower:
                min_price, max_price = price_range
                break
        else:
            # Use default for that category
            min_price, max_price = price_ranges[item_group].get("default", (20, 200))
    
    # Generate random price within range
    base_price = random.uniform(min_price, max_price)
    
    # Round to nearest .99 or .00
    if random.random() > 0.3:
        # 70% chance of .99 pricing
        base_price = round(base_price) - 0.01
    else:
        # 30% chance of round number
        base_price = round(base_price, -1)  # Round to nearest 10
    
    return round(base_price, 2)


# =====================================================
# ADVANCED: CREATE TIERED PRICING
# =====================================================
def create_tiered_pricing():
    """Create quantity-based pricing (bulk discounts)"""
    
    print("\n📊 Creating Tiered Pricing...")
    
    # Get all items
    items = frappe.get_all(
        "Item",
        filters={"has_variants": 0, "disabled": 0},
        fields=["name", "item_name"],
        limit=20  # Limit for demo
    )
    
    price_list = "Standard Selling"
    tiers_created = 0
    
    for item in items:
        # Get base price
        base_price_doc = frappe.db.get_value(
            "Item Price",
            {"item_code": item.name, "price_list": price_list},
            "price_list_rate"
        )
        
        if not base_price_doc:
            continue
        
        base_price = float(base_price_doc)
        
        # Create tiered pricing
        tiers = [
            {"min_qty": 10, "discount": 5},    # 5% off for 10+ units
            {"min_qty": 50, "discount": 10},   # 10% off for 50+ units
            {"min_qty": 100, "discount": 15},  # 15% off for 100+ units
        ]
        
        for tier in tiers:
            discounted_price = base_price * (1 - tier["discount"] / 100)
            
            # Check if this tier already exists
            if not frappe.db.exists("Item Price", {
                "item_code": item.name,
                "price_list": price_list,
                "min_qty": tier["min_qty"]
            }):
                try:
                    price_doc = frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": item.name,
                        "price_list": price_list,
                        "price_list_rate": round(discounted_price, 2),
                        "min_qty": tier["min_qty"],
                        "currency": "USD"
                    })
                    price_doc.insert(ignore_permissions=True)
                    tiers_created += 1
                    
                except Exception as e:
                    print(f"❌ Tier error: {e}")
    
    frappe.db.commit()
    print(f"✅ Created {tiers_created} tiered prices!")


# =====================================================
# BATCH PRICING UPDATE
# =====================================================
def update_prices_by_percentage(item_group=None, percentage=10, price_list="Standard Selling"):
    """
    Increase/decrease prices by percentage
    
    Args:
        item_group: Filter by item group (None = all items)
        percentage: Percentage change (positive = increase, negative = decrease)
        price_list: Which price list to update
    """
    
    print(f"\n💹 Updating prices by {percentage}%...")
    
    filters = {"price_list": price_list}
    
    if item_group:
        # Get items in that group
        items = frappe.get_all("Item", filters={"item_group": item_group}, pluck="name")
        filters["item_code"] = ["in", items]
    
    # Get all prices to update
    prices = frappe.get_all(
        "Item Price",
        filters=filters,
        fields=["name", "price_list_rate"]
    )
    
    updated = 0
    multiplier = 1 + (percentage / 100)
    
    for price in prices:
        new_rate = float(price.price_list_rate) * multiplier
        
        frappe.db.set_value(
            "Item Price",
            price.name,
            "price_list_rate",
            round(new_rate, 2)
        )
        updated += 1
    
    frappe.db.commit()
    print(f"✅ Updated {updated} prices!")


# =====================================================
# PROMOTIONAL PRICING
# =====================================================
def create_promotional_prices(discount_percentage=20, valid_days=30):
    """Create temporary promotional prices"""
    
    from datetime import datetime, timedelta
    
    print(f"\n🎉 Creating {discount_percentage}% promotional prices...")
    
    # Create promotional price list
    promo_list_name = f"Promotional {discount_percentage}% Off"
    
    if not frappe.db.exists("Price List", promo_list_name):
        promo_list = frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": promo_list_name,
            "buying": 0,
            "selling": 1,
            "enabled": 1,
            "currency": "USD",
            "valid_from": datetime.now().date(),
            "valid_upto": (datetime.now() + timedelta(days=valid_days)).date()
        })
        promo_list.insert(ignore_permissions=True)
    
    # Get random items for promotion (50% of items)
    all_items = frappe.get_all(
        "Item",
        filters={"has_variants": 0, "disabled": 0},
        fields=["name"]
    )
    
    promo_items = random.sample(all_items, len(all_items) // 2)
    
    promo_created = 0
    
    for item in promo_items:
        # Get standard price
        standard_price = frappe.db.get_value(
            "Item Price",
            {"item_code": item.name, "price_list": "Standard Selling"},
            "price_list_rate"
        )
        
        if standard_price:
            promo_price = float(standard_price) * (1 - discount_percentage / 100)
            
            price_doc = frappe.get_doc({
                "doctype": "Item Price",
                "item_code": item.name,
                "price_list": promo_list_name,
                "price_list_rate": round(promo_price, 2),
                "currency": "USD"
            })
            price_doc.insert(ignore_permissions=True)
            promo_created += 1
    
    frappe.db.commit()
    print(f"✅ Created {promo_created} promotional prices!")

# =====================================================
# MAIN EXECUTION
# =====================================================
def run_all():
    print("=" * 70)
    print("🚀 ERPNext Test Data Generator with REAL Product Images")
    print("=" * 70)
    
    # STEP 1: Setup attributes
    setup_item_attributes()
    
    # STEP 2: Create data
    print("\n📋 Creating Customers...")
    create_customers(20)
    
    print("\n🏭 Creating Suppliers...")
    create_suppliers(15)
    
    print("\n📦 Creating Products...")
    create_items(50)
    
    # STEP 3: Create Item Prices (NEW!)
    create_item_prices()
    
    # OPTIONAL: Create tiered pricing for bulk orders
    # create_tiered_pricing()
    
    # OPTIONAL: Create promotional prices
    # create_promotional_prices(discount_percentage=20, valid_days=30)
    
    print("\n🏢 Creating Warehouses...")
    create_warehouses()
    
    print("\n👤 Creating Sales Persons...")
    create_sales_persons()
    
    frappe.db.commit()
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE! Check your ERPNext for:")
    print("   • Product variants with matching images")
    print("   • Item prices in multiple price lists")
    print("   • Customers & Suppliers with images")
    print("=" * 70)









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
# MATCHING PRODUCT IMAGES - IMPROVED
# =====================================================
def download_image(name, category, retry_count=3):
    """Download image that MATCHES the product category"""
    
    # Create safe filename
    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    file_name = f"{safe_name[:30]}_{random.randint(1000, 9999)}.jpg"
    file_path = os.path.join(PUBLIC_FILE_PATH, file_name)
    
    # Ensure directory exists
    os.makedirs(PUBLIC_FILE_PATH, exist_ok=True)
    
    print(f"    🔍 Searching for: {category}")
    
    # Try sources that actually search/match categories
    image_sources = [
        ("DummyJSON", lambda c: get_dummyjson_image(c)),
        ("Fake Store API", lambda c: get_fakestore_image(c)),
        ("Unsplash Random", lambda c: get_unsplash_search_image(c)),
        ("Placeholder with category", lambda c: get_category_placeholder(c)),
    ]
    
    for source_name, source_func in image_sources:
        for attempt in range(retry_count):
            try:
                print(f"    🔍 Trying {source_name}...")
                
                image_url = source_func(category)
                
                if not image_url:
                    print(f"    ⏭️  {source_name} returned no URL")
                    break
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(
                    image_url,
                    timeout=20,
                    allow_redirects=True,
                    headers=headers,
                    stream=True
                )
                
                if response.status_code == 200:
                    # Save file
                    with open(file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        if file_size > 1000:
                            print(f"    ✅ Got {category} image from {source_name}: {file_size} bytes")
                            return f"/files/{file_name}"
                        else:
                            os.remove(file_path)
                
                time.sleep(0.5)
                    
            except Exception as e:
                print(f"    ⚠️ {source_name} failed: {str(e)[:30]}")
                time.sleep(1)
        
        if os.path.exists(file_path):
            return f"/files/{file_name}"
    
    print(f"    ❌ No matching image found for {category}")
    return None


# =====================================================
# SOURCE 1: DummyJSON Product Images (BEST MATCH!)
# =====================================================
def get_dummyjson_image(category):
    """DummyJSON has real product images that match categories"""
    
    # Map categories to DummyJSON product IDs
    category_to_products = {
        # Electronics
        "smartphone": [1, 2, 3, 4, 5],
        "laptop": [6, 7, 8, 9, 10],
        "tablet": [11],
        "watch": [61, 62, 63],
        "headphones": [12, 13],
        "earbuds": [12, 13],
        "camera": [14],
        "monitor": [15],
        
        # Fashion
        "shoes": [59, 60, 66, 67, 68],
        "sneakers": [59, 60, 66],
        "boots": [67, 68],
        "shirt": [48, 49, 50, 51],
        "tshirt": [48, 49, 50],
        "dress": [42, 43, 44],
        "jacket": [54, 55],
        "jeans": [52, 53],
        "bag": [56, 57, 58],
        "backpack": [58],
        "watch": [61, 62, 63],
        "sunglasses": [69, 70],
        
        # Furniture
        "chair": [31, 32],
        "desk": [35],
        "table": [33, 34],
        "lamp": [36],
        "furniture": [31, 32, 33, 34, 35],
        
        # Beauty/Personal Care
        "perfume": [16, 17, 18],
        "skincare": [19, 20, 21],
        "makeup": [22, 23],
        
        # Home
        "decor": [38, 39, 40],
        "kitchen": [71, 72, 73],
        
        # Automotive
        "automotive": [74, 75, 76],
    }
    
    # Find matching products
    category_lower = category.lower()
    product_ids = []
    
    for key, ids in category_to_products.items():
        if key in category_lower:
            product_ids = ids
            break
    
    # If no match, use random electronics
    if not product_ids:
        product_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Get random product from category
    product_id = random.choice(product_ids)
    
    # Fetch product data
    try:
        response = requests.get(f"https://dummyjson.com/products/{product_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("images"):
                # Return first image
                return data["images"][0]
    except:
        pass
    
    return None


# =====================================================
# SOURCE 2: Fake Store API (Real Product Images)
# =====================================================
def get_fakestore_image(category):
    """Fake Store API has real product photos"""
    
    # Map categories to Fake Store categories
    category_map = {
        "laptop": "electronics",
        "phone": "electronics",
        "smartphone": "electronics",
        "electronics": "electronics",
        "tablet": "electronics",
        "camera": "electronics",
        "monitor": "electronics",
        
        "shirt": "men's clothing",
        "tshirt": "men's clothing",
        "jacket": "men's clothing",
        "jeans": "men's clothing",
        
        "jewelry": "jewelery",
        "necklace": "jewelery",
        "ring": "jewelery",
    }
    
    category_lower = category.lower()
    fakestore_category = None
    
    for key, value in category_map.items():
        if key in category_lower:
            fakestore_category = value
            break
    
    if not fakestore_category:
        return None
    
    try:
        # Get products from category
        url = f"https://fakestoreapi.com/products/category/{fakestore_category}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            products = response.json()
            if products:
                product = random.choice(products)
                return product.get("image")
    except:
        pass
    
    return None


# =====================================================
# SOURCE 3: Unsplash with Search (Rate limited but good)
# =====================================================
def get_unsplash_search_image(category):
    """Unsplash with actual search query"""
    
    # Clean category for better search
    search_terms = category.lower().strip()
    
    # Add random seed to avoid cache/rate limits
    seed = random.randint(1000, 9999)
    
    return f"https://source.unsplash.com/400x400/?{search_terms}&sig={seed}"


# =====================================================
# SOURCE 4: Category-based Placeholder (Last resort)
# =====================================================
def get_category_placeholder(category):
    """Colored placeholder with category name"""
    
    # Category-based colors
    color_map = {
        "electronics": "4A90E2",
        "fashion": "E24A90",
        "furniture": "90E24A",
        "sports": "E2904A",
        "kitchen": "4AE290",
    }
    
    bg_color = "CCCCCC"
    for key, color in color_map.items():
        if key in category.lower():
            bg_color = color
            break
    
    text = category.replace(' ', '+')
    return f"https://via.placeholder.com/400x400/{bg_color}/FFFFFF?text={text}"


# =====================================================
# IMPROVED CATEGORY DETECTION
# =====================================================
def determine_category_from_name(item_name):
    """Better category detection from item name"""
    
    item_lower = item_name.lower()
    
    # Detailed category mapping
    categories = {
        # Smartphones
        "iphone": "smartphone",
        "iphone 15": "smartphone",
        "samsung": "smartphone",
        "galaxy": "smartphone",
        "pixel": "smartphone",
        "oneplus": "smartphone",
        
        # Laptops
        "macbook": "laptop",
        "laptop": "laptop",
        "dell xps": "laptop",
        "thinkpad": "laptop",
        "chromebook": "laptop",
        
        # Tablets
        "ipad": "tablet",
        "tablet": "tablet",
        
        # Audio
        "airpods": "earbuds",
        "headphone": "headphones",
        "earbud": "earbuds",
        "speaker": "speaker",
        
        # Wearables
        "apple watch": "watch",
        "smartwatch": "watch",
        "fitbit": "watch",
        
        # Computer Accessories
        "mouse": "mouse",
        "keyboard": "keyboard",
        "monitor": "monitor",
        "webcam": "camera",
        
        # Fashion - Shoes
        "nike": "shoes",
        "adidas": "sneakers",
        "running shoes": "shoes",
        "sneaker": "sneakers",
        "boot": "boots",
        
        # Fashion - Clothing
        "t-shirt": "tshirt",
        "tshirt": "tshirt",
        "shirt": "shirt",
        "jeans": "jeans",
        "jacket": "jacket",
        "dress": "dress",
        
        # Accessories
        "wallet": "wallet",
        "bag": "bag",
        "backpack": "backpack",
        "sunglasses": "sunglasses",
        
        # Furniture
        "chair": "chair",
        "desk": "desk",
        "table": "table",
        "lamp": "lamp",
        "sofa": "furniture",
        "bookshelf": "furniture",
        
        # Sports
        "yoga mat": "yoga",
        "dumbbell": "dumbbell",
        "weight": "weights",
        "water bottle": "bottle",
        
        # Kitchen
        "coffee maker": "kitchen",
        "blender": "kitchen",
        "air fryer": "kitchen",
    }
    
    # Find best match
    for keyword, category in categories.items():
        if keyword in item_lower:
            return category
    
    return "product"


# =====================================================
# UPDATE FUNCTION (Same as before)
# =====================================================
def update_items_with_images(limit=None, delay=1.0):
    """Update existing items with MATCHING images"""
    
    print("\n📸 Updating Items with MATCHING Product Images...")
    print("=" * 70)
    
    items = frappe.db.sql("""
        SELECT name, item_name, item_group
        FROM `tabItem`
        WHERE has_variants = 0 
        AND disabled = 0
        ORDER BY creation DESC
        LIMIT %s
    """, limit or 999999, as_dict=True)
    
    if not items:
        print("✅ All items already have images!")
        return
    
    print(f"Found {len(items)} items without images\n")
    
    updated = 0
    failed = 0
    
    for idx, item in enumerate(items, 1):
        print(f"\n[{idx}/{len(items)}] {item.item_name}")
        
        category = determine_category_from_name(item.item_name)
        image_path = download_image(item.item_name, category, retry_count=2)
        
        if image_path:
            try:
                frappe.db.set_value("Item", item.name, "image", image_path)
                frappe.db.commit()
                updated += 1
            except Exception as e:
                print(f"  ❌ Update failed: {e}")
                failed += 1
        else:
            failed += 1
        
        if delay > 0 and idx < len(items):
            time.sleep(delay)
    
    print("\n" + "=" * 70)
    print(f"✅ Updated: {updated} items")
    print(f"❌ Failed: {failed} items")
    print("=" * 70)


def check_image_stats():
    """Check image statistics"""
    
    print("\n📊 Image Statistics...")
    print("=" * 70)
    
    total = frappe.db.count("Item", {"has_variants": 0, "disabled": 0})
    with_images = frappe.db.count("Item", {
        "has_variants": 0,
        "disabled": 0,
        "image": ["!=", ""]
    })
    without_images = total - with_images
    
    percentage = (with_images / total * 100) if total > 0 else 0
    
    print(f"Total Items: {total}")
    print(f"With Images: {with_images} ({percentage:.1f}%)")
    print(f"Without Images: {without_images}")
    print("=" * 70)