from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FieldList, FormField, HiddenField, SelectField, DecimalField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError, Optional
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ItemForm(FlaskForm):
    item_id = HiddenField('Item ID', validators=[DataRequired()])
    item_name = HiddenField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[NumberRange(min=0)], default=0)

class PlaceOrderForm(FlaskForm):
    items = FieldList(FormField(ItemForm), min_entries=1)
    submit = SubmitField('Proceed to Checkout')

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[('credit', 'Credit Card'), ('debit', 'Debit Card')], validators=[DataRequired()])
    card_number = StringField('Card Number', validators=[Optional(), Length(min=16, max=16)])
    expiry_date = StringField('Expiry Date (MM/YY)', validators=[Optional(), Length(min=5, max=5)])
    cvv = StringField('CVV', validators=[Optional(), Length(min=3, max=4)])
    bank_name = StringField('Bank Name', validators=[Optional()])
    payment_amount = DecimalField('Payment Amount', validators=[Optional(), NumberRange(min=0.01)])
    submit = SubmitField('Complete Payment')

    def validate_expiry_date(form, field):
        if form.payment_method.data == 'credit':
            if not field.data:
                raise ValidationError('Expiry date is required for credit cards')
            try:
                expiry_date = datetime.strptime(field.data, '%m/%y')
                if expiry_date < datetime.now():
                    raise ValidationError('The expiry date must be in the future')
            except ValueError:
                raise ValidationError('Invalid date format. Please use MM/YY')

    def validate_cvv(form, field):
        if form.payment_method.data == 'credit' and not field.data:
            raise ValidationError('CVV is required for credit cards')

    def validate_bank_name(form, field):
        if form.payment_method.data == 'debit' and not field.data:
            raise ValidationError('Bank name is required for debit cards')

    def validate(self, extra_validators=None):
        if not super(PaymentForm, self).validate():
            return False
        if self.payment_method.data == 'credit':
            if not self.expiry_date.data:
                self.expiry_date.errors.append('Expiry date is required for credit cards')
                return False
            if not self.cvv.data:
                self.cvv.errors.append('CVV is required for credit cards')
                return False
        elif self.payment_method.data == 'debit':
            if not self.bank_name.data:
                self.bank_name.errors.append('Bank name is required for debit cards')
                return False
        return True
class CheckoutForm(FlaskForm):
    delivery_option = SelectField('Delivery Option', choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')], validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[('credit', 'Credit Card'), ('debit', 'Debit Card'), ('account', 'Charge to Account')], validators=[DataRequired()])
    card_number = StringField('Card Number', validators=[Optional(), Length(min=16, max=16)])
    expiry_date = StringField('Expiry Date (MM/YY)', validators=[Optional(), Length(min=5, max=5)])
    cvv = StringField('CVV', validators=[Optional(), Length(min=3, max=4)])
    bank_name = StringField('Bank Name', validators=[Optional()])
    submit = SubmitField('Complete Payment')

    def validate_expiry_date(form, field):
        if form.payment_method.data == 'credit':
            if not field.data:
                raise ValidationError('Expiry date is required for credit cards')
            try:
                expiry_date = datetime.strptime(field.data, '%m/%y')
                if expiry_date < datetime.now():
                    raise ValidationError('The expiry date must be in the future')
            except ValueError:
                raise ValidationError('Invalid date format. Please use MM/YY')

    def validate_cvv(form, field):
        if form.payment_method.data == 'credit' and not field.data:
            raise ValidationError('CVV is required for credit cards')

    def validate_bank_name(form, field):
        if form.payment_method.data == 'debit' and not field.data:
            raise ValidationError('Bank name is required for debit cards')

    def validate(self, extra_validators=None):
        if not super(CheckoutForm, self).validate():
            return False
        if self.payment_method.data == 'credit':
            if not self.expiry_date.data:
                self.expiry_date.errors.append('Expiry date is required for credit cards')
                return False
            if not self.cvv.data:
                self.cvv.errors.append('CVV is required for credit cards')
                return False
        elif self.payment_method.data == 'debit':
            if not self.bank_name.data:
                self.bank_name.errors.append('Bank name is required for debit cards')
                return False
        return True