from app.models import Staff, Customer, Veggie, WeightedVeggie, PackVeggie, UnitPriceVeggie, PremadeBox, Item, OrderLine
from app import create_app, db
from datetime import date

app = create_app()
app.app_context().push()

#Create a staff member
staff = Staff(firstName="shop", lastName="staff", staffID="staff001", dateJoined=date(2023, 1, 1), deptName="Management")
staff.set_password("staffpass123")

# Create a customer
customer = Customer(firstName="james", lastName="cameron", custID="cust001", custAddress="123 Main St", maxOwing=100.0)
customer.set_password("custpass123")

# Add WeightedVeggie items
carrot = WeightedVeggie(name="Carrot", vegName="Fresh Carrot", weight=1.0, weightPerKilo=2.5)
potato = WeightedVeggie(name="Potato", vegName="Russet Potato", weight=1.0, weightPerKilo=1.8)

# Add PackVeggie items
lettuce = PackVeggie(name="Lettuce", vegName="Iceberg Lettuce", numOfPack=1, pricePerPack=2.99)
spinach = PackVeggie(name="Spinach", vegName="Baby Spinach", numOfPack=1, pricePerPack=3.49)

# Add UnitPriceVeggie items
tomato = UnitPriceVeggie(name="Tomato", vegName="Ripe Tomato", pricePerUnit=0.75, quantity=1)
cucumber = UnitPriceVeggie(name="Cucumber", vegName="English Cucumber", pricePerUnit=1.25, quantity=1)

# Add PremadeBox items
small_box = PremadeBox(name="Small Veggie Box", boxSize="Small", numOfBoxes=1, price=15.99)
large_box = PremadeBox(name="Large Veggie Box", boxSize="Large", numOfBoxes=1, price=25.99)




# Add to database
db.session.add_all([staff, customer,carrot, potato, lettuce, spinach, tomato, cucumber, small_box, large_box])
db.session.commit()

print("Database updated successfully!")