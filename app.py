from flask import Flask, render_template
from datetime import date
app = Flask(__name__)


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

import random

def DiagnoseImage(ImageID,ImageType):
    DiagJSON = dict()
    DiagBoxes = dict()
    chest_diseases = ["Pneumonia","PneumoThorax","Infusion","CardioMegaly","Nodule","Bronchitis"]
    breast_diseases = ["Calcification","Circumscribed","Spiculated","Ill-defined","Distortion","Asymmetry"]
    retina_diseases = ["Macular Degeneration","Melanoma - Cancer","Diabetic Retinopathy",
                       "Glaucoma","Hypertension","Bronchitis"]
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


if __name__ == '__main__':
    app.run()
