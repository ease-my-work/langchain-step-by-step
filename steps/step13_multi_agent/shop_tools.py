"""Barista Bot's shop tools and customer context, from steps 06, 08 and 12 (unchanged).

They moved here to keep app.py about what is new in this step.
"""

from dataclasses import dataclass

from langchain.tools import ToolRuntime, tool

from shared.shop import ORDERS, PRODUCTS


@dataclass
class CustomerContext:
    customer_id: str


@tool
def get_order_status(order_id: str, runtime: ToolRuntime[CustomerContext]) -> dict:
    """Look up the status of one of the logged-in customer's orders.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None or order["customer_id"] != runtime.context.customer_id:
        return {"error": f"No order {order_id} on this customer's account."}
    items = [PRODUCTS[product_id]["name"] for product_id in order["items"]]
    return {"order_id": order_id, **order, "items": items}


@tool
def list_my_orders(runtime: ToolRuntime[CustomerContext]) -> list[dict]:
    """List all orders of the logged-in customer, newest first."""
    mine = [
        {"order_id": order_id, "placed": order["placed"], "status": order["status"]}
        for order_id, order in ORDERS.items()
        if order["customer_id"] == runtime.context.customer_id
    ]
    return sorted(mine, key=lambda order: order["placed"], reverse=True)


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


@tool
def issue_refund(
    order_id: str, amount_inr: int, reason: str, runtime: ToolRuntime[CustomerContext]
) -> dict:
    """Refund money to the customer for one of their orders. A human approves every refund.

    Args:
        order_id: The order number, like "BS-1002".
        amount_inr: How much to refund, in whole rupees. At most the order total.
        reason: One short sentence explaining why, for the approver.
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None or order["customer_id"] != runtime.context.customer_id:
        return {"error": f"No order {order_id} on this customer's account."}
    if order["status"] == "cancelled":
        return {"error": f"Order {order_id} was cancelled and never charged. Nothing to refund."}
    if not 0 < amount_inr <= order["total"]:
        return {"error": f"Refund must be between ₹1 and the order total, ₹{order['total']}."}
    return {
        "status": "refund issued",
        "order_id": order_id,
        "amount_inr": amount_inr,
        "arrives_in": "5 to 7 working days, to the original payment method",
    }
