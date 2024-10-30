from flask import render_template, request, redirect, url_for, flash, session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app import db, csrf
from app.models import (
    Person, Staff, Customer, Order, OrderLine, Item, Veggie, PremadeBox,
    Payment, WeightedVeggie, PackVeggie, UnitPriceVeggie, CreditCardPayment,
    DebitCardPayment, AccountPayment
)
from app.forms import LoginForm, PlaceOrderForm, ItemForm, PaymentForm, CheckoutForm


def calculate_item_price(item, quantity):
    if isinstance(item, WeightedVeggie):
        return item.weightPerKilo * quantity
    elif isinstance(item, PackVeggie):
        return item.pricePerPack * quantity
    elif isinstance(item, UnitPriceVeggie):
        return item.pricePerUnit * quantity
    elif isinstance(item, PremadeBox):
        return item.price * quantity
    elif isinstance(item, Veggie):
        # Handle generic Veggie objects (you may want to set a default price or log a warning)
        print(f"Warning: Generic Veggie object found: {item.vegName}")
        return 0  # or set a default price
    else:
        # Log an error or raise an exception for unknown item types
        print(f"Unknown item type: {type(item)}")
        return 0

def calculate_order_total(order):
    return sum(calculate_item_price(line.item, line.quantity) for line in order.orderLines)

def init_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            
            # Try to find a staff member first
            user = Staff.query.filter(Staff.staffID == username).first()
            
            # If not found, try to find a customer
            if user is None:
                user = Customer.query.filter(Customer.custID == username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_type'] = user.type
                flash('Logged in successfully.')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.')
        return render_template('login.html', form=form)

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        session.pop('user_type', None)
        flash('Logged out successfully.')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = Person.query.get(session['user_id'])
        if user.type == 'staff':
            return render_template('staff_dashboard.html', user=user)
        else:
            return render_template('customer_dashboard.html', user=user)
    
    @app.route('/place_order', methods=['GET', 'POST'])
    def place_order():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        items = Item.query.all()

        if request.method == 'POST':
            order_items = []
            total = 0
            
            for item in items:
                quantity = int(request.form.get(f'quantity_{item.id}', 0))
                if quantity > 0:
                    price = calculate_item_price(item, quantity)
                    total += price
                    order_items.append({
                        'id': item.id,
                        'name': item.vegName if isinstance(item, Veggie) else item.boxSize,
                        'type': item.type,
                        'price': price,
                        'quantity': quantity
                    })
            
            if order_items:
                session['order_items'] = order_items
                session['order_total'] = total
                return redirect(url_for('checkout'))
            else:
                flash('Please add at least one item to your order.', 'warning')
        
        return render_template('place_order.html', items=items)
    
    @app.route('/place_order/premade_box/<size>', methods=['GET', 'POST'])
    def place_premade_box_order(size):
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        
        box_limits = {
            'small': {'weighted': {'min': 1, 'max': 2}, 'pack': {'min': 1, 'max': 2}, 'unit': {'min': 1, 'max': 3}},
            'medium': {'weighted': {'min': 3, 'max': 5}, 'pack': {'min': 3, 'max': 4}, 'unit': {'min': 4, 'max': 6}},
            'large': {'weighted': {'min': 6, 'max': 8}, 'pack': {'min': 5, 'max': 6}, 'unit': {'min': 7, 'max': 9}}
        }
        
        limits = box_limits.get(size.lower())
        if not limits:
            flash('Invalid box size selected.', 'error')
            return redirect(url_for('place_order'))
        
        weighted_veggies = WeightedVeggie.query.all()
        pack_veggies = PackVeggie.query.all()
        unit_veggies = UnitPriceVeggie.query.all()

        if request.method == 'POST':
            order_items = []
            total = 0
            error = False
            below_limit = False
            error_messages = []

            for veggie_type, veggies in [('weighted', weighted_veggies), ('pack', pack_veggies), ('unit', unit_veggies)]:
                type_total = 0
                for veggie in veggies:
                    quantity = float(request.form.get(f'quantity_{veggie.id}', 0))
                    if quantity > 0:
                        type_total += quantity
                        price = calculate_item_price(veggie, quantity)
                        total += price
                        order_items.append({
                            'id': veggie.id,
                            'name': veggie.vegName,
                            'type': veggie_type,
                            'price': price,
                            'quantity': quantity
                        })
                
                if type_total > limits[veggie_type]['max']:
                    error = True
                    error_messages.append(f'You have exceeded the limit for {veggie_type} vegetables in a {size} box. (Selected: {type_total}, Max: {limits[veggie_type]["max"]})')
                elif type_total < limits[veggie_type]['min']:
                    below_limit = True
                    error_messages.append(f'You have not reached the minimum for {veggie_type} vegetables in a {size} box. (Selected: {type_total}, Min: {limits[veggie_type]["min"]})')

            if error or below_limit:
                for message in error_messages:
                    flash(message, 'error')
                
                if below_limit:
                    smaller_size = {'small': None, 'medium': 'small', 'large': 'medium'}[size.lower()]
                    if smaller_size:
                        flash(f'Consider choosing a {smaller_size} box instead.', 'warning')
                    else:
                        flash(f'Please add more items to meet the minimum requirements.', 'warning')
                
                return render_template('place_premade_box_order.html', size=size, limits=limits, 
                                    weighted_veggies=weighted_veggies, pack_veggies=pack_veggies, 
                                    unit_veggies=unit_veggies)

            if order_items:
                session['order_items'] = order_items
                session['order_total'] = total
                return redirect(url_for('checkout'))
            else:
                flash('Please add at least one item to your order.', 'warning')
        
        return render_template('place_premade_box_order.html', size=size, limits=limits, 
                            weighted_veggies=weighted_veggies, pack_veggies=pack_veggies, 
                            unit_veggies=unit_veggies)

    @app.route('/checkout', methods=['GET', 'POST'])
    def checkout():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        if 'order_items' not in session or 'order_total' not in session:
            return redirect(url_for('place_order'))
        
        customer = Customer.query.get(session['user_id'])
        order_items = session['order_items']
        subtotal = session['order_total']
        delivery_fee = 10.00
        
        form = CheckoutForm()
        form.delivery_option.choices = [('pickup', 'Pickup'), ('delivery', 'Delivery')]
        
        if request.method == 'POST':
            if form.validate():
                try:
                    delivery_option = form.delivery_option.data
                    total = subtotal + (delivery_fee if delivery_option == 'delivery' else 0)

                    if form.payment_method.data == 'account' and total > customer.maxOwing:
                        flash(f'Order amount (${total:.2f}) exceeds your maximum owing limit (${customer.maxOwing:.2f}).', 'error')
                        return render_template('checkout.html', form=form, order_items=order_items, subtotal=subtotal, delivery_fee=delivery_fee, total=total)

                    new_order = Order(
                        orderCustomer=customer,
                        orderNumber=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        orderStatus='Pending',
                        deliveryOption=delivery_option
                    )
                    db.session.add(new_order)
                    db.session.flush()

                    for item in order_items:
                        order_line = OrderLine(
                            order_id=new_order.id,
                            item_id=item['id'],
                            quantity=item['quantity']
                        )
                        db.session.add(order_line)

                    payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    
                    if form.payment_method.data == 'credit':
                        payment = CreditCardPayment(
                            paymentAmount=total,
                            paymentDate=datetime.utcnow(),
                            paymentID=payment_id,
                            order_id=new_order.id,
                            cardExpiryDate=datetime.strptime(form.expiry_date.data, '%m/%y'),
                            cardNumber=form.card_number.data,
                            cardType='Credit'
                        )
                    elif form.payment_method.data == 'debit':
                        payment = DebitCardPayment(
                            paymentAmount=total,
                            paymentDate=datetime.utcnow(),
                            paymentID=payment_id,
                            order_id=new_order.id,
                            bankName=form.bank_name.data,
                            debitCardNumber=form.card_number.data
                        )
                    else:  # Charge to account
                        payment = Payment(
                            paymentAmount=total,
                            paymentDate=datetime.utcnow(),
                            paymentID=payment_id,
                            order_id=new_order.id,
                            type='account'
                        )
                        customer.custBalance += total
                    
                    db.session.add(payment)
                    new_order.orderStatus = 'Processing'  # Changed from 'Paid' to 'Processing'
                    
                    db.session.commit()
                    if form.payment_method.data == 'account':
                        flash('Order placed and amount is charged to your account. Your order is now processing.', 'success')
                    else:
                        flash('Order placed and payment processed successfully. Your order is now processing.', 'success')
                    session.pop('order_items', None)
                    session.pop('order_total', None)
                    return redirect(url_for('view_current_order'))
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f'Error processing payment: {str(e)}', exc_info=True)
                    flash(f'An error occurred while processing the payment: {str(e)}', 'error')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
        
        return render_template('checkout.html', form=form, order_items=order_items, subtotal=subtotal, delivery_fee=delivery_fee)

    @app.route('/settle_balance', methods=['GET', 'POST'])
    def settle_balance():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        form = PaymentForm()
        
        if request.method == 'POST':
            if form.validate():
                try:
                    payment_amount = float(form.payment_amount.data)
                    if payment_amount > customer.custBalance:
                        flash('Payment amount cannot exceed your current balance.', 'error')
                    else:
                        payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        
                        if form.payment_method.data == 'credit':
                            payment = CreditCardPayment(
                                paymentAmount=payment_amount,
                                paymentDate=datetime.utcnow(),
                                paymentID=payment_id,
                                order_id=None,  # Set to None for balance settlements
                                cardExpiryDate=datetime.strptime(form.expiry_date.data, '%m/%y'),
                                cardNumber=form.card_number.data,
                                cardType='Credit'
                            )
                        else:
                            payment = DebitCardPayment(
                                paymentAmount=payment_amount,
                                paymentDate=datetime.utcnow(),
                                paymentID=payment_id,
                                order_id=None,  # Set to None for balance settlements
                                bankName=form.bank_name.data,
                                debitCardNumber=form.card_number.data
                            )
                        
                        db.session.add(payment)
                        customer.custBalance -= payment_amount
                        db.session.commit()
                        flash(f'Payment of ${payment_amount:.2f} processed successfully. Your new balance is ${customer.custBalance:.2f}', 'success')
                        return redirect(url_for('view_customer_details'))
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f'Error processing payment: {str(e)}', exc_info=True)
                    flash(f'An error occurred while processing the payment: {str(e)}', 'error')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
        
        return render_template('settle_balance.html', form=form, customer=customer)

    @app.route('/view_current_order')
    def view_current_order():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        current_orders = Order.query.filter(
            Order.orderCustomer == customer,
            Order.orderStatus.notin_(['Delivered', 'Cancelled'])
        ).order_by(Order.orderDate.desc()).all()
        
        return render_template('current_order.html', orders=current_orders, calculate_order_total=calculate_order_total, calculate_item_price=calculate_item_price)

    @app.route('/cancel_order/<int:order_id>')
    def cancel_order(order_id):
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        order = Order.query.get(order_id)
        
        if order and order.orderStatus not in ['Delivered', 'Cancelled'] and order.orderCustomer == customer:
            try:
                total = calculate_order_total(order)
                order.orderStatus = 'Cancelled'
                
                # Check if the payment was charged to account
                account_payment = Payment.query.filter_by(order_id=order.id, type='account').first()
                if account_payment:
                    customer.custBalance -= total
                    customer.custBalance = max(customer.custBalance, 0)  # Ensure balance is non-negative
                    db.session.commit()
                    flash(f'Order {order.orderNumber} has been cancelled and your balance has been updated.', 'success')
                else:
                    db.session.commit()
                    flash(f'Order {order.orderNumber} has been cancelled and the ordered amount will be returned within a few days.', 'success')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error cancelling order: {str(e)}', exc_info=True)
                flash(f'An error occurred while cancelling the order: {str(e)}', 'error')
        else:
            flash('Unable to cancel the order.', 'error')
        
        return redirect(url_for('view_current_order'))
        
    @app.route('/view_previous_orders')
    def view_previous_orders():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        previous_orders = Order.query.filter(
            Order.orderCustomer == customer,
            Order.orderStatus.in_(['Delivered', 'Cancelled'])
        ).order_by(Order.orderDate.desc()).all()

        return render_template(
            'previous_orders.html', 
            orders=previous_orders, 
            calculate_order_total=calculate_order_total, 
            calculate_item_price=calculate_item_price
        )
    
    @app.route('/view_customer_details')
    def view_customer_details():
        if 'user_id' not in session or session['user_type'] != 'customer':
            return redirect(url_for('login'))
        
        customer = Customer.query.get(session['user_id'])
        return render_template('customer_details.html', customer=customer)

    @app.route('/staff/view_all_vegetables')
    def staff_view_all_vegetables():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        veggies = Veggie.query.all()

        box_limits = {
            'small': {'weighted': {'min': 1, 'max': 2}, 'pack': {'min': 1, 'max': 2}, 'unit': {'min': 1, 'max': 3}},
            'medium': {'weighted': {'min': 3, 'max': 5}, 'pack': {'min': 3, 'max': 4}, 'unit': {'min': 4, 'max': 6}},
            'large': {'weighted': {'min': 6, 'max': 8}, 'pack': {'min': 5, 'max': 6}, 'unit': {'min': 7, 'max': 9}}
        }

        premade_boxes = [
            {'name': 'Small Box', 'size': 'Small'},
            {'name': 'Medium Box', 'size': 'Medium'},
            {'name': 'Large Box', 'size': 'Large'}
        ]

        return render_template('staff_vegetables.html', veggies=veggies, premade_boxes=premade_boxes, box_limits=box_limits)

    @app.route('/staff/view_current_orders')
    def staff_view_current_orders():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        # Fetch all orders, sorted by date (most recent first)
        all_orders = Order.query.filter(
            Order.orderStatus.notin_(['Delivered', 'Cancelled'])
        ).order_by(Order.orderDate.desc()).all()
        
        return render_template('staff_current_orders.html', orders=all_orders, calculate_order_total=calculate_order_total)    
    
    @app.route('/staff/view_previous_orders')
    def staff_view_previous_orders():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        previous_orders = Order.query.filter(Order.orderStatus.in_(['Delivered', 'Cancelled'])
        ).order_by(Order.orderDate.desc()).all()
        return render_template('staff_previous_orders.html', orders=previous_orders, calculate_order_total=calculate_order_total)

    @app.route('/staff/update_order_status/<int:order_id>', methods=['POST'])
    @csrf.exempt  # Temporarily exempt this route from CSRF protection
    def staff_update_order_status(order_id):
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        order = Order.query.get(order_id)
        if order:
            new_status = request.form['status']
            order.orderStatus = new_status
            db.session.commit()
            flash('Order status updated successfully.')
        else:
            flash('Order not found.')
        return redirect(url_for('staff_view_current_orders'))   
    
    @app.route('/staff/view_all_customers')
    def staff_view_all_customers():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        customers = Customer.query.all()
        return render_template('staff_customers.html', customers=customers)

    @app.route('/staff/generate_customer_list')
    def staff_generate_customer_list():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        customers = Customer.query.all()
        customer_data = []

        for customer in customers:
            orders = Order.query.filter_by(orderCustomer=customer).all()
            order_count = len(orders)
            
            items_ordered = db.session.query(
                Item.name,
                func.sum(OrderLine.quantity).label('total_quantity')
            ).join(OrderLine, OrderLine.item_id == Item.id)\
            .join(Order, Order.id == OrderLine.order_id)\
            .filter(Order.orderCustomer == customer)\
            .group_by(Item.id)\
            .all()

            total_ordered_amount = db.session.query(func.sum(Payment.paymentAmount))\
                .join(Order, Order.id == Payment.order_id)\
                .filter(Order.orderCustomer == customer)\
                .scalar() or 0

            customer_data.append({
                'customer': customer,
                'order_count': order_count,
                'items_ordered': items_ordered,
                'total_ordered_amount': total_ordered_amount
            })

        return render_template('staff_customer_list.html', customer_data=customer_data)

    @app.route('/staff/generate_sales_report')
    def staff_generate_sales_report():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)
        
        def get_sales_data(start_date, end_date):
            return db.session.query(
                Item.name,
                func.sum(OrderLine.quantity).label('total_quantity'),
                func.sum(Payment.paymentAmount).label('total_amount')
            ).join(OrderLine, OrderLine.item_id == Item.id)\
            .join(Order, Order.id == OrderLine.order_id)\
            .join(Payment, Payment.order_id == Order.id)\
            .filter(Payment.paymentDate.between(start_date, end_date))\
            .group_by(Item.id)\
            .all()

        # Daily sales
        daily_sales_query = db.session.query(func.sum(Payment.paymentAmount))\
            .filter(func.date(Payment.paymentDate) == today)
        daily_sales = daily_sales_query.scalar() or 0
        
        daily_items_query = db.session.query(
            Item.name,
            func.sum(OrderLine.quantity).label('total_quantity'),
            func.sum(Payment.paymentAmount).label('total_amount')
        ).join(OrderLine, OrderLine.item_id == Item.id)\
        .join(Order, Order.id == OrderLine.order_id)\
        .join(Payment, Payment.order_id == Order.id)\
        .filter(func.date(Payment.paymentDate) == today)\
        .group_by(Item.id)
        
        daily_items = daily_items_query.all()

        # Weekly sales
        weekly_sales = db.session.query(func.sum(Payment.paymentAmount))\
            .filter(Payment.paymentDate >= week_ago).scalar() or 0
        weekly_items = get_sales_data(week_ago, now)

        # Monthly sales
        monthly_sales = db.session.query(func.sum(Payment.paymentAmount))\
            .filter(Payment.paymentDate >= month_ago).scalar() or 0
        monthly_items = get_sales_data(month_ago, now)

        # Yearly sales
        yearly_sales = db.session.query(func.sum(Payment.paymentAmount))\
            .filter(Payment.paymentDate >= year_ago).scalar() or 0
        yearly_items = get_sales_data(year_ago, now)
        
        return render_template('staff_sales_report.html', 
                            daily_sales=daily_sales,
                            daily_items=daily_items,
                            weekly_sales=weekly_sales,
                            weekly_items=weekly_items,
                            monthly_sales=monthly_sales,
                            monthly_items=monthly_items,
                            yearly_sales=yearly_sales,
                            yearly_items=yearly_items)

    @app.route('/staff/view_popular_items')
    def staff_view_popular_items():
        if 'user_id' not in session or session['user_type'] != 'staff':
            return redirect(url_for('login'))
        
        popular_items = db.session.query(Item, func.sum(OrderLine.quantity).label('total_quantity')).\
            join(OrderLine).group_by(Item.id).order_by(func.sum(OrderLine.quantity).desc()).limit(10).all()
        
        return render_template('staff_popular_items.html', popular_items=popular_items)

    return app
