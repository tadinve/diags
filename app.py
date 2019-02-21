import random
from datetime import date

from flask import Flask, render_template, request

from models import Patient, db, populate_database

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
    populate_database(db)


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def DiagnoseImage(ImageID, ImageType):
    DiagJSON = dict()
    DiagBoxes = dict()
    chest_diseases = ["Pneumonia", "PneumoThorax",
                      "Infusion", "CardioMegaly", "Nodule", "Bronchitis"]
    breast_diseases = ["Calcification", "Circumscribed",
                       "Spiculated", "Ill-defined", "Distortion", "Asymmetry"]
    retina_diseases = ["Macular Degeneration", "Melanoma - Cancer", "Diabetic Retinopathy",
                       "Glaucoma", "Hypertension", "Bronchitis"]
    c = random.sample(range(20, 79), 6)

    if ImageType == "ChestX-Ray":
        for i in range(len(c)):
            DiagJSON[chest_diseases[i]] = c[i]/100

    if ImageType == "BreastCancer":
        for i in range(len(c)):
            DiagJSON[breast_diseases[i]] = c[i]/100

    if ImageType == "RetinaImage":
        for i in range(len(c)):
            DiagJSON[retina_diseases[i]] = c[i]/100

    return DiagJSON, DiagBoxes


@app.route('/')
def index():
    data = {}
    data['updated'] = custom_strftime('%B {S}, %Y', date.today())
    data['name'] = 'James  Magnopolia'
    data['patient_id'] = '90-194-77734'
    data['image_id'] = 'TYBG003'
    data['diag_date'] = custom_strftime('%B {S}, %Y', date.today())
    data['gauges'] = [10, 25, 35, 50, 65, 80]

    return render_template('index.html', data=data)


@app.route('/patient')
def add_patient():
    from forms import PatientForm
    model = Patient()
    form = PatientForm(request.form, model, db=db)
    return render_template('add-patient.html', form=form)


if __name__ == '__main__':
    app.run()
