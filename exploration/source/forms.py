from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, ValidationError, Length, Regexp
from wtforms.fields import SelectField
import re

def validate_israeli_license_plate(form, field):
    """
    Custom validator for Israeli license plate format
    Validates: 8 digits only, no spaces or special characters
    """
    plate = field.data.strip()
    
    # Check if plate is exactly 8 digits
    if not plate.isdigit():
        raise ValidationError('License plate must contain only numbers (0-9)')
    
    if len(plate) != 8:
        raise ValidationError('License plate must be exactly 8 digits long')
    
    # Additional validation: Check for common invalid patterns
    if plate == '00000000':
        raise ValidationError('Invalid license plate number')
    
    # Check if all digits are the same (suspicious)
    if len(set(plate)) == 1:
        raise ValidationError('License plate cannot have all identical digits')
    
    # Check for sequential patterns (suspicious)
    if is_sequential(plate):
        raise ValidationError('License plate cannot be a sequential pattern')
    
    # Check for common test patterns
    test_patterns = ['12345678', '87654321', '11111111', '99999999']
    if plate in test_patterns:
        raise ValidationError('This appears to be a test license plate')

def is_sequential(plate):
    """
    Check if the plate number is a sequential pattern
    """
    digits = [int(d) for d in plate]
    
    # Check ascending sequence
    if digits == list(range(digits[0], digits[0] + 8)):
        return True
    
    # Check descending sequence
    if digits == list(range(digits[0], digits[0] - 8, -1)):
        return True
    
    return False

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')

class ParkingForm(FlaskForm):
    car_plate = StringField('Car Plate', validators=[
        DataRequired(),
        Length(min=8, max=8, message='License plate must be exactly 8 digits'),
        validate_israeli_license_plate
    ])
    vehicle_type_id = SelectField('Vehicle Type', coerce=int)
    slot = StringField('Slot', validators=[DataRequired()])
    image =  FileField('Image')
    submit    = SubmitField('Start Parking')


class EndParkingForm(FlaskForm):
    submit = SubmitField('End Parking')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Save')

class VehicleTypeForm(FlaskForm):
    name = StringField('Vehicle Type Name', validators=[DataRequired()])
    submit = SubmitField('Save') 