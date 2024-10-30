from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Person(db.Model):
    __tablename__ = 'person'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(200))
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Staff(Person):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    dateJoined = db.Column(db.Date, nullable=False)
    deptName = db.Column(db.String(50), nullable=False)
    staffID = db.Column(db.String(20), unique=True, nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'staff',
    }

class Customer(Person):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    custAddress = db.Column(db.String(200), nullable=False)
    custBalance = db.Column(db.Float, default=0.0)
    custID = db.Column(db.String(20), unique=True, nullable=False)
    maxOwing = db.Column(db.Float, default=100.0)

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

class CorporateCustomer(Customer):
    __tablename__ = 'corporate_customer'
    id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    discountRate = db.Column(db.Float, default=0.1)
    maxCredit = db.Column(db.Float, nullable=False)
    minBalance = db.Column(db.Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'corporate_customer',
    }

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    orderCustomer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    orderDate = db.Column(db.DateTime, default=datetime.utcnow)
    orderNumber = db.Column(db.String(20), unique=True, nullable=False)
    orderStatus = db.Column(db.String(20), default='Pending')
    deliveryOption = db.Column(db.String(20), nullable=False)
    
    orderCustomer = db.relationship('Customer', backref='orders')
    orderLines = db.relationship('OrderLine', backref='order', cascade='all, delete-orphan')

class OrderLine(db.Model):
    __tablename__ = 'order_line'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    
    item = db.relationship('Item', backref='order_lines')

class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'item',
        'polymorphic_on': type
    }

class Veggie(Item):
    __tablename__ = 'veggie'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    vegName = db.Column(db.String(100), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'veggie',
    }

class WeightedVeggie(Veggie):
    __tablename__ = 'weighted_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    weightPerKilo = db.Column(db.Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'weighted_veggie',
    }

class PackVeggie(Veggie):
    __tablename__ = 'pack_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    numOfPack = db.Column(db.Integer, nullable=False)
    pricePerPack = db.Column(db.Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'pack_veggie',
    }

class UnitPriceVeggie(Veggie):
    __tablename__ = 'unit_price_veggie'
    id = db.Column(db.Integer, db.ForeignKey('veggie.id'), primary_key=True)
    pricePerUnit = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'unit_price_veggie',
    }

class PremadeBox(Item):
    __tablename__ = 'premade_box'
    id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    boxSize = db.Column(db.String(20), nullable=False)
    numOfBoxes = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'premade_box',
    }

    def BoxPrice(self):
        return self.price * self.numOfBoxes

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    paymentAmount = db.Column(db.Float, nullable=False)
    paymentDate = db.Column(db.DateTime, default=datetime.utcnow)
    paymentID = db.Column(db.String(20), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # Changed to nullable=True
    type = db.Column(db.String(50))

    order = db.relationship('Order', backref='payments')

    __mapper_args__ = {
        'polymorphic_identity': 'payment',
        'polymorphic_on': type
    }

class CreditCardPayment(Payment):
    __tablename__ = 'credit_card_payment'
    id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    cardExpiryDate = db.Column(db.Date, nullable=False)
    cardNumber = db.Column(db.String(16), nullable=False)
    cardType = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'credit_card_payment',
    }

class DebitCardPayment(Payment):
    __tablename__ = 'debit_card_payment'
    id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    bankName = db.Column(db.String(50), nullable=False)
    debitCardNumber = db.Column(db.String(16), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'debit_card_payment',
    }

class AccountPayment(Payment):
    __tablename__ = 'account_payment'
    id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'account',
    }