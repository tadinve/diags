from datetime import date
import json
import os
import uuid
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, abort, session
from werkzeug.utils import secure_filename
from models import db, populate_database, Patient, Gender, DiagImage, ImageType, DiagNotes, Company
from utils import DiagnoseImage

app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'media', 'uploads')
app.secret_key = 'some secret key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
db.session.expire_on_commit = False
with app.app_context():
    db.create_all()
    populate_database(db)

os.makedirs(os.path.join(
    app.config['UPLOAD_FOLDER'], 'patients'), exist_ok=True)
os.makedirs(os.path.join(
    app.config['UPLOAD_FOLDER'], 'diagnostics'), exist_ok=True)

LABELS = {'RetinaImage': 'Retinopathy',
          'ChestX-Ray': 'Chest X-Ray', 'BreastCancer': 'Mammogram'}


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# TODO: this will be changed after login implementation
@app.context_processor
def get_company():
    return dict(company=Company.query.get(1))


@app.template_filter()
def todict(value):
    if not value:
        return {}
    return json.loads(value)


@app.template_filter()
def tosortedlist(value):
    mydict = json.loads(value)
    keys = sorted(mydict, key=mydict.__getitem__, reverse=True)
    output = []
    for key in keys:
        output.append((key, mydict[key]))
    return output


@app.template_filter()
def getlabel(value):
    return LABELS[value]


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
                'Patient saved with ID: {}, <a href="{}">view patient profile</a>'.format(repr(patient), url))
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
    available_types = []
    for item in diags:
        if item.image_type.value not in available_types:
            available_types.append(item.image_type.value)
    from forms import get_notes_form
    noteform = get_notes_form(id)
    session['url'] = url_for('patient_profile', patient_id=patient_id)
    return render_template('index2.html', patient=patient, patient_id=patient_id, diags=diags, available_types=available_types, form=noteform)


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
                'Image saved with ID: {}, <a href="{}">view patient profile</a>'.format(repr(diag), url))
        return redirect(url_for('upload_image'))
    return render_template('add-image.html', form=form)


# @app.route('/notes/add/', methods=['POST'], defaults={'image_id': None})
@app.route('/notes/add/<image_id>/', methods=['POST'])
def add_note(image_id):
    note = DiagNotes()
    from forms import get_notes_form
    image = DiagImage.query.get(image_id)
    form = get_notes_form(image.patient_id, obj=note)
    if form.validate_on_submit():
        form.populate_obj(note)
        note.user_id = 1  # TODO: this should be changed after user login system implementation
        try:
            db.session.add(note)
            db.session.commit()
            flash('Note saved with ID: {}'.format(
                repr(note)), category='success')
        except Exception:
            flash('Failed to add the note', category='danger')
        url = url_for('patient_profile',
                      patient_id="P{0:0=3d}".format(note.image.patient_id))
        return redirect(url)


if __name__ == '__main__':
    app.run(debug=True)
