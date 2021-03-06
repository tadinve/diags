from flask_sqlalchemy import SQLAlchemy
import datetime
import enum
from utils import DiagnoseImage
db = SQLAlchemy()


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return "C{0:0=3d}".format(self.id)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'),
                           nullable=False, default=1)
    company = db.relationship('Company',
                              backref=db.backref('users', lazy=True))

    @property
    def fullname(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return "U{0:0=3d}".format(self.id)


class Gender(enum.Enum):
    Male = 0
    Female = 1


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True)
    photo = db.Column(db.String)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender))
    phone = db.Column(db.String(16), nullable=True)
    address = db.Column(db.String(300), nullable=True)

    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'),
                           nullable=False, default=1)
    company = db.relationship('Company',
                              backref=db.backref('patients', lazy=True))

    @property
    def fullname(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def __repr__(self):
        return "P{0:0=3d}".format(self.id)


class ImageType(enum.Enum):
    ChestX_Ray = 'ChestX-Ray'
    RetinaImage = 'RetinaImage'
    BreastCancer = 'BreastCancer'


class DiagImage(db.Model):
    __tablename__ = 'diagimages'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String)
    image_type = db.Column(db.Enum(ImageType))
    diag_json = db.Column(db.Text)
    diag_boxes = db.Column(db.Text)
    date_loaded = db.Column(
        db.DateTime, default=datetime.datetime.now, index=True)

    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'),
                           nullable=False, index=True)
    patient = db.relationship('Patient',
                              backref=db.backref('diagimages', lazy=True))

    def __repr__(self):
        return "I{0:0=3d}".format(self.id)


class DiagNotes(db.Model):
    __tablename__ = 'diagnotes'
    id = db.Column(db.Integer, primary_key=True)
    notes = db.Column(db.Text)
    image_id = db.Column(db.Integer, db.ForeignKey('diagimages.id'),
                         nullable=False, index=True)
    image = db.relationship('DiagImage',
                            backref=db.backref('diagnotes', lazy=False))
    date_added = db.Column(
        db.DateTime, default=datetime.datetime.now, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('diagnotes', lazy=False))

    def __repr__(self):
        return "N{0:0=3d}".format(self.id)


def populate_database(db):
    # check if there is 1 company then don't populate the database
    if db.session.query(Company).count() == 0:
        import pandas as pd

        xl = pd.ExcelFile('data/ML Diags - Database Model.xlsx')

        companies_data = xl.parse('Companies')
        for index, row in companies_data.iterrows():
            company_id = int(row['CompanyID'].replace(
                'C00', '').replace('C0', '').replace('C', ''))
            c = Company(id=company_id, name=row['CompanyName'])
            db.session.add(c)

        users_data = xl.parse('Users')
        for index, row in users_data.iterrows():
            company_id = int(row['CompanyID'].replace(
                'C00', '').replace('C0', '').replace('C', ''))
            user_id = int(row['UserID'].replace(
                'U00', '').replace('U0', '').replace('U', ''))
            u = User(id=user_id, first_name=row['FirstName'],
                     last_name=row['LastName'], email=row['Email'], company_id=company_id)
            db.session.add(u)

        patient_data = xl.parse('Patients')
        for index, row in patient_data.iterrows():
            company_id = int(row['CompanyID'].replace(
                'C00', '').replace('C0', '').replace('C', ''))
            patient_id = int(row['PatientID'].replace(
                'P00', '').replace('P0', '').replace('P', ''))
            p = Patient(id=patient_id, first_name=row['FirstName'],
                        last_name=row['LastName'], email=row['Email'], photo='team-3.jpg', date_of_birth=row['DateOfBirth'],
                        gender=Gender[row['Gender']], company_id=company_id)
            db.session.add(p)

        diagimages_data = xl.parse('DiagImages')
        for index, row in diagimages_data.iterrows():
            patient_id = int(row['PatientID'].replace(
                'P00', '').replace('P0', '').replace('P', ''))
            image_id = int(row['ImageID'].replace(
                'I00', '').replace('I0', '').replace('I', ''))
            diag_json, diag_boxes = DiagnoseImage(image_id, row['ImageType'])
            image = ''
            if row['ImageType'] == 'RetinaImage':
                image = 'retina_image.png'
            elif row['ImageType'] == 'BreastCancer':
                image = 'breastcancer_image.png'
            else:
                image = 'chestxray_image.png'
            d = DiagImage(id=image_id, image_type=ImageType(row['ImageType']), diag_json=diag_json,
                          diag_boxes=diag_boxes, date_loaded=row['DateLoaded'], patient_id=patient_id, image=image)
            db.session.add(d)

        db.session.commit()
