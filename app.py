from flask import Flask, render_template
from datetime import date
app = Flask(__name__)


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


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
