from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.validators import DataRequired, Email
from wtforms.fields import FileField, SelectField
from models import Patient, Company
from app import db

PatientFormBase = model_form(Patient, FlaskForm, exclude=['diagimages'], field_args={
    'first_name': {
        'validators': [DataRequired()]
    },
    'last_name': {
        'validators': [DataRequired()]
    },
    'email': {
        'validators': [DataRequired(), Email()],
        'render_kw': {'type': 'email'}
    },
    'date_of_birth': {
        'validators': [DataRequired()],
        'render_kw': {'type': 'date'}
    }
})


class PatientForm(PatientFormBase):
    company = SelectField(choices=[(i.id, i.name)
                                   for i in db.session.query(Company).all()])
    photo = FileField(validators=[DataRequired()])
