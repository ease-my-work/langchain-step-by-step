"""Barista Bot's shop tools, from step 06 (unchanged).

They moved here to keep app.py about what is new in this step.
"""

from langchain.tools import tool

from shared.shop import ORDERS, PRODUCTS


@tool
def get_order_status(order_id: str) -> dict:
    """Look up the status of a Bean Street Coffee order.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"error": f"No order {order_id}. Order numbers look like BS-1002."}
    items = [PRODUCTS[product_id]["name"] for product_id in order["items"]]
    return {"order_id": order_id, **order, "items": items}


@tool
def search_products(query: str) -> list[dict]:
    """Search the Bean Street Coffee catalogue by keyword.

    Args:
        query: One or two words, like "decaf", "grinder" or "espresso".
            Categories are: beans, grinders, brewers, espresso machines.
    """
    words = query.lower().split()
    matches = []
    for product_id, product in PRODUCTS.items():
        text = f"{product['name']} {product['category']} {product['notes']}".lower()
        if any(word in text for word in words):
            matches.append(
                {"product_id": product_id, "name": product["name"], "price_inr": product["price"]}
            )
    return matches  # an empty list tells the model "nothing found"


@tool
def check_stock(product_id: str) -> dict:
    """Check how many units of a product are in stock, plus tasting or product notes.

    Args:
        product_id: The product id from search_products, like "BEAN-MAL".
    """
    product = PRODUCTS.get(product_id.strip().upper())
    if product is None:
        return {"error": f"No product {product_id}. Use search_products to find the id."}
    return {"product_id": product_id, "in_stock": product["stock"], "notes": product["notes"]}
