from app.models import Order, OrderLine, Item,WeightedVeggie,PackVeggie,UnitPriceVeggie,PremadeBox,CorporateCustomer
from app import db
from app.database import db

def calculate_order_total(order):
    total = 0
    for line in order.orderLines:
        item = Item.query.get(line.item_id)
        if isinstance(item, WeightedVeggie):
            total += item.weightPerKilo * line.quantity
        elif isinstance(item, PackVeggie):
            total += item.pricePerPack * line.quantity
        elif isinstance(item, UnitPriceVeggie):
            total += item.pricePerUnit * line.quantity
        elif isinstance(item, PremadeBox):
            total += item.BoxPrice() * line.quantity
    return total

def apply_corporate_discount(order):
    if isinstance(order.orderCustomer, CorporateCustomer):
        total = calculate_order_total(order)
        discounted_total = total * (1 - order.orderCustomer.discountRate)
        return discounted_total
    return calculate_order_total(order)

def check_customer_eligibility(customer, order_total):
    if isinstance(customer, CorporateCustomer):
        return customer.custBalance >= customer.minBalance
    else:
        return customer.custBalance + order_total <= customer.maxOwing

def generate_order_number():
    last_order = Order.query.order_by(Order.id.desc()).first()
    if last_order:
        last_number = int(last_order.orderNumber[4:])
        new_number = last_number + 1
    else:
        new_number = 1
    return f"ORD-{new_number:06d}"