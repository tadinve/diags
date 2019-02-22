from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length
from wtforms.fields import FileField, SelectField, StringField, DateField, RadioField
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextInput
from wtforms import ValidationError
from models import Patient, Company, Gender, DiagImage, ImageType, Patient
from app import db


class MyDateWidget(TextInput):
    input_type = 'date'


class MyDateField(DateField):
    widget = MyDateWidget()


class PatientForm(FlaskForm):
    company_id = SelectField('Company', choices=[(i.id, i.name)
                                                 for i in db.session.query(Company).all()], coerce=int)
    first_name = StringField(validators=[DataRequired(), Length(max=50)])
    last_name = StringField(validators=[DataRequired(), Length(max=100)])
    email = EmailField(validators=[DataRequired(), Email(), Length(max=255)])
    date_of_birth = MyDateField(validators=[DataRequired()])
    gender = RadioField(choices=[(i.value, i.name)
                                 for i in Gender], coerce=int)
    photo = FileField(validators=[DataRequired()],
                      render_kw={'accept': 'image/*'})

    def validate_email(form, field):
        if db.session.query(Patient).filter_by(email=field.data).count() > 0:
            raise ValidationError('Patient already exists')


class DiagImageForm(FlaskForm):
    patient_id = SelectField('Patient', choices=[(i.id, '{} - {}'.format(repr(i), i.fullname))
                                                 for i in db.session.query(Patient).all()], coerce=int)
    image = FileField(validators=[DataRequired()],
                      render_kw={'accept': 'image/*'})
    image_type = RadioField(choices=[(i.value, i.value)
                                     for i in ImageType], coerce=str)
