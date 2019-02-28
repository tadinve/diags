from datetime import date
import json
import os
import uuid
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
from models import db, populate_database, Patient, Gender, DiagImage, ImageType
from utils import DiagnoseImage

app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'media', 'uploads')
app.secret_key = 'some secret key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
    populate_database(db)

os.makedirs(os.path.join(
    app.config['UPLOAD_FOLDER'], 'patients'), exist_ok=True)
os.makedirs(os.path.join(
    app.config['UPLOAD_FOLDER'], 'diagnostics'), exist_ok=True)


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.template_filter()
def todict(value):
    if not value:
        return {}
    return json.loads(value)


@app.template_filter()
def getage(born):
    if not born:
        return ''
    today = date.today()
    return str(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))


@app.route('/')
def index():
    return redirect(url_for('patient_profile', patient_id='P001'))


@app.route('/all-patients/')
def all_patients():
    patients = Patient.query.all()
    return render_template('home.html', patients=patients)


@app.route('/patient/add/', methods=['GET', 'POST'], defaults={'patient_id': None})
@app.route('/patient/edit/<patient_id>/', methods=['GET', 'POST'])
def add_patient(patient_id):
    from forms import PatientForm
    if patient_id:
        id = int(patient_id.replace('P00', '').replace(
            'P0', '').replace('P', ''))
        patient = Patient.query.get(id)
    else:
        patient = Patient()
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['photo']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = uuid.uuid4().hex+'.' + \
                secure_filename(file.filename).split('.')[-1].lower()
            form.photo.data.save(os.path.join(
                app.config['UPLOAD_FOLDER'], 'patients', filename))
            form.populate_obj(patient)
            patient.photo = filename
            patient.gender = Gender(form.gender.data)
            db.session.add(patient)
            db.session.commit()
            url = url_for('patient_profile', patient_id=repr(patient))
            flash(
                f'Patient saved with ID: {repr(patient)}, <a href="{url}">view patient profile</a>')
        return redirect(url_for('add_patient'))
    return render_template('add-patient.html', form=form)


@app.route('/patient/<patient_id>/')
def patient_profile(patient_id):
    id = int(patient_id.replace('P00', '').replace(
        'P0', '').replace('P', ''))
    patient = Patient.query.get(id)
    if not patient:
        return abort(404)
    diags = DiagImage.query.filter_by(
        patient=patient).order_by(DiagImage.date_loaded.desc()).all()
    return render_template('index2.html', patient=patient, patient_id=patient_id, diags=diags)


@app.route('/patient/img/<patient_photo>/')
def patient_img(patient_photo):
    if not patient_photo:
        return abort(404)
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'patients'), patient_photo)


@app.route('/diag/img/<diag_image>/')
def diagnostics_img(diag_image):
    if not diag_image:
        return abort(404)
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'diagnostics'), diag_image)


@app.route('/diag/add/', methods=['GET', 'POST'], defaults={'patient_id': None})
@app.route('/diag/add/<patient_id>/', methods=['GET', 'POST'])
def upload_image(patient_id):
    if patient_id:
        id = int(patient_id.replace('P00', '').replace(
            'P0', '').replace('P', ''))
        diag = DiagImage(patient_id=id)
    else:
        diag = DiagImage()
    from forms import DiagImageForm
    
    form = DiagImageForm(obj=diag)
    if form.validate_on_submit():
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['image']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = uuid.uuid4().hex+'.' + \
                secure_filename(file.filename).split('.')[-1].lower()
            form.image.data.save(os.path.join(
                app.config['UPLOAD_FOLDER'], 'diagnostics', filename))
            form.populate_obj(diag)
            diag.image = filename
            diag.image_type = ImageType(form.image_type.data).name
            diag_json, diag_boxes = DiagnoseImage(os.path.join(
                app.config['UPLOAD_FOLDER'], 'diagnostics', filename), form.image_type.data)
            diag.diag_boxes = diag_boxes
            diag.diag_json = diag_json
            db.session.add(diag)
            db.session.commit()
            url = url_for('patient_profile',
                          patient_id="P{0:0=3d}".format(diag.patient_id))
            flash(
                f'Image saved with ID: {repr(diag)}, <a href="{url}">view patient profile</a>')
        return redirect(url_for('upload_image'))
    return render_template('add-image.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
