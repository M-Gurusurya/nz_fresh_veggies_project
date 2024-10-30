from app import create_app, db
from app.models import Person, Staff, Customer, Order, OrderLine, Item, Veggie, PremadeBox, Payment

app = create_app()
app.app_context().push()

# Create all tables
db.create_all()

print("Tables created successfully!")