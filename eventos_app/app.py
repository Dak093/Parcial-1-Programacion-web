from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, NumberRange
import datetime, re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_para_formularios'

# Datos en memoria
categories = ['Tecnología', 'Académico', 'Cultural', 'Deportivo', 'Social']

events = [
    {
        'id': 1,
        'title': 'Conferencia de Python',
        'slug': 'conferencia-python',
        'description': 'Un espacio para aprender sobre Python y sus buenas prácticas.',
        'date': '2025-09-15',
        'time': '14:00',
        'location': 'Auditorio Principal',
        'category': 'Tecnología',
        'max_attendees': 50,
        'attendees': [{'name': 'Juan Pérez', 'email': 'juan@example.com'}],
        'featured': True
    }
]

# Formularios
class EventForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    date = StringField('Fecha (YYYY-MM-DD)', validators=[DataRequired(), Length(max=10)])
    time = StringField('Hora (HH:MM)', validators=[DataRequired(), Length(max=5)])
    location = StringField('Ubicación', validators=[DataRequired(), Length(max=120)])
    category = SelectField('Categoría', choices=[], validators=[DataRequired()])
    max_attendees = IntegerField('Máximo asistentes', validators=[DataRequired(), NumberRange(min=1)])
    featured = BooleanField('Destacado')
    submit = SubmitField('Crear evento')

class RegisterForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Registrarme')

# Helpers
def make_slug(text):
    s = text.lower()
    s = re.sub(r'[^a-z0-9áéíóúñü]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

def get_event_by_slug(slug):
    return next((e for e in events if e['slug'] == slug), None)

def parse_event_datetime(e):
    return datetime.datetime.strptime(e['date'] + ' ' + e['time'], '%Y-%m-%d %H:%M')

# Rutas
@app.route('/')
def index():
    today = datetime.date.today()
    upcoming = [e for e in events if datetime.datetime.strptime(e['date'], '%Y-%m-%d').date() >= today]
    upcoming.sort(key=parse_event_datetime)
    featured = [e for e in upcoming if e.get('featured')]
    return render_template('index.html', events=upcoming, featured=featured, categories=categories)

@app.route('/event/<slug>/')
def event_detail(slug):
    e = get_event_by_slug(slug)
    if not e: abort(404)
    return render_template('event_detail.html', event=e)

@app.route('/admin/event/', methods=['GET','POST'])
def admin_event():
    form = EventForm()
    form.category.choices = [(c,c) for c in categories]
    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = make_slug(title)
        if get_event_by_slug(slug):
            flash('Ya existe un evento con ese título.', 'danger')
        else:
            try:
                datetime.datetime.strptime(form.date.data.strip(), '%Y-%m-%d')
                datetime.datetime.strptime(form.time.data.strip(), '%H:%M')
            except Exception:
                flash('Formato de fecha/hora inválido.', 'danger')
                return render_template('admin.html', form=form)
            new_event = {
                'id': max([ev['id'] for ev in events]) + 1 if events else 1,
                'title': title,
                'slug': slug,
                'description': form.description.data.strip(),
                'date': form.date.data.strip(),
                'time': form.time.data.strip(),
                'location': form.location.data.strip(),
                'category': form.category.data,
                'max_attendees': int(form.max_attendees.data),
                'attendees': [],
                'featured': bool(form.featured.data)
            }
            events.append(new_event)
            flash('Evento creado correctamente.', 'success')
            return redirect(url_for('event_detail', slug=new_event['slug']))
    return render_template('admin.html', form=form)

@app.route('/event/<slug>/register/', methods=['GET','POST'])
def register_event(slug):
    e = get_event_by_slug(slug)
    if not e: abort(404)
    form = RegisterForm()
    if form.validate_on_submit():
        if len(e['attendees']) >= e['max_attendees']:
            flash('Evento lleno.', 'danger')
            return redirect(url_for('event_detail', slug=slug))
        e['attendees'].append({'name': form.name.data.strip(), 'email': form.email.data.strip()})
        flash('Registro exitoso.', 'success')
        return redirect(url_for('event_detail', slug=slug))
    return render_template('register.html', form=form, event=e)

@app.route('/events/category/<category>/')
def events_by_category(category):
    filtered = [e for e in events if e['category'].lower() == category.lower()]
    filtered.sort(key=parse_event_datetime)
    return render_template('index.html', events=filtered, featured=[e for e in filtered if e.get('featured')], categories=categories)

if __name__ == '__main__':
    app.run(debug=True)
