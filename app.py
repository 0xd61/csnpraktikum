import operator
from re import template
from flask import Flask, render_template, url_for, redirect, jsonify, send_from_directory, render_template_string, send_file
from flask.globals import request
from flask.helpers import flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms import StringField, IntegerField, SubmitField, FloatField
from flask_sqlalchemy import SQLAlchemy
from wtforms.widgets.core import Option
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import numpy as np
import os

#flask, db, key config
app = Flask(__name__)
app.config["SECRET_KEY"] = "admin4"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///csn_projekt_db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Password.query.get(int(user_id))

#db.Model
class records(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    record = db.Column(db.String, nullable=False)
    operator = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)

class Password(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


#form model (testing)
class record_submit(FlaskForm):
    record_in = FloatField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    title = StringField(validators=[DataRequired()])
    operator = StringField(validators=[DataRequired()])
    submit = SubmitField("Daten hinzufügen.", validators=[DataRequired()])

class recordToUpdate(FlaskForm):
    record_in = FloatField(validators=[DataRequired()])
    title = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    operator = StringField(validators=[DataRequired()])
    submit = SubmitField("Betrag verändern", validators=[DataRequired()])

class login(FlaskForm):
    email = StringField(validators=[DataRequired()])
    password = StringField(validators=[DataRequired()])
    submit = SubmitField("Login", validators=[DataRequired()])

#function to calculate with operators
def addUp(array):
        count = 0
        for n in range(0, len(array)):
            antiZero = n + 1
            if antiZero % 2 == 0:
                operator = array[n - 1]
                if operator == "+":
                    count = count + float(array[n])
                else:
                    count = count - float(array[n])
        return count

#function for pythons sorted function.
def sortingDates(Dates):
    splitup = Dates.split('-')
    return  splitup[0], splitup[1], splitup[2]


@app.route('/login', methods = ['GET', 'POST'])
def logging_in():    
    form = login()
    email = None
    password = None
    if form.validate_on_submit():
        user = Password.query.filter_by(user= form.email.data).first()
        if user:
            a = check_password_hash(user.password_hash, form.password.data)
            if a:
                login_user(user)
                return redirect(url_for('index'))


    return render_template('login.html', form = form)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('logging_in'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    form = record_submit()
    recordToSubmit = None
    timeToSubmit = None
    #when submiting form
    if form.validate_on_submit():
        #db.add
        toSubmit = records(record = form.record_in.data, time = form.time.data, operator = form.operator.data, title = form.title.data)
        db.session.add(toSubmit)
        db.session.commit()
        #clearing froms
        form.record_in.data = ""
        form.time.data = ""
        form.operator.data = ""
    return render_template("add.html", form = form)

@app.route('/update/<id>', methods=['POST', 'GET'])
@login_required
def update(id):
    form = recordToUpdate()
    check = id
    toUpdate = records.query.get(id)
    if form.validate_on_submit():
        toUpdate.record = request.form['record_in']
        toUpdate.time = request.form['time']
        toUpdate.operator = request.form['operator']
        toUpdate.title = request.form['title']
        try:
            db.session.commit()
            flash("Der Datensatz wurde erfolgreich aktualisiert.")
            return redirect(url_for('index'))
        except:
            flash("Error")
            return render_template("update.html", form = form, check = check, toUpdate = toUpdate)
        #clearing form
    else:
        return render_template("update.html", form = form, check = check, toUpdate = toUpdate)

@app.route('/delete/<id>', methods=['POST', 'GET'])
@login_required
def delete(id):
    form = record_submit()
    check = id
    toDelete = records.query.get(id)
    try:
        db.session.delete(toDelete)
        db.session.commit()
        flash("Der Datensatz wurde erfolgreich gelöscht.")
        return redirect(url_for('history'))
    except:
        flash("Error")
        return redirect(url_for('history'))


#Database API for getting charts
@app.route('/request/chart/<id>', methods=['POST', 'GET'])
def updateChart(id):
    getDate = records.query.order_by()
    toAppend = []

    for n in getDate:
        toAppend.append(n.time)
    sortedByDate = sorted(toAppend, key=sortingDates)
    #function to add up all records by id
    sumArray = []
    numCache = []
    finalCache = []
    for date in range(0, len(sortedByDate)):
        if date == 0:
            tofilter = records.query.filter_by(time = sortedByDate[date])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(n.record)
                numCache.append(n.operator)
                numCache.append(n.record)
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedByDate[date]
        if toCheck == sortedByDate[date]:
            continue
        else:
            tofilter = records.query.filter_by(time = sortedByDate[date])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(n.record)
                numCache.append(n.operator)
                numCache.append(n.record)
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedByDate[date]
    final = addUp(finalCache)
    databaseDataQuery = sortedByDate
    databaseTrimVersion = list(dict.fromkeys(databaseDataQuery))
    allRecords = records.query.order_by()
    if id == "daily":
        return jsonify(sortedByDate, sumArray, databaseTrimVersion)
    elif id == "monthly":
        #loop for monthly
        stringArray = databaseTrimVersion
        intArray = sumArray
        stringToAppend = []
        intToAppend = []
        sum = 0
        for n in range(0, len(stringArray)):
            if n == 0:
                toCheck = stringArray[n][5:7]
                sum = sum + float(intArray[n])
                stringToAppend.append(stringArray[n][0:7])
            elif stringArray[n][5:7] == toCheck:
                sum = sum + float(intArray[n])
            elif stringArray[n][5:7] != toCheck:
                stringToAppend.append(stringArray[n][0:7])
                intToAppend.append(sum)
                sum = 0
                toCheck = stringArray[n][5:7]
                sum = sum + float(intArray[n])
        intToAppend.append(sum)
        sumArray = intToAppend
        databaseTrimVersion = stringToAppend
        return jsonify(sortedByDate, sumArray, databaseTrimVersion)
    else:
        monthQuery = []
        monthRecord = []
        for n in range(0, len(databaseTrimVersion)):
            if databaseTrimVersion[n][0:7] == id:
                monthQuery.append(databaseTrimVersion[n])
                monthRecord.append(sumArray[n])
        if monthQuery:
            databaseTrimVersion = monthQuery
            sumArray = monthRecord
            return jsonify('', sumArray, databaseTrimVersion)
        else:
            return jsonify("error")

def recreadeCSV():
    getDate = records.query.order_by()
    rows = []
    row = [] 
    for dates in getDate:
        rows.append([dates.id, dates.operator, dates.record, dates.time])
    
    with open('Projekt.csv', 'wb') as f:
        np.savetxt(rows, delimiter =", ", fmt ='% s')

   
@app.route("/history")
def history():
    allRecords = records.query.order_by()
    return render_template("history.html", allRecords = allRecords)

@app.route('/getfile/Projekt.csv')
def download():
    recreadeCSV()
    return send_file('Projekt.csv', as_attachment=True)


@app.route("/", methods=['POST', 'GET'])
def index():
    #sorting dates and appending to an array
    getDate = records.query.order_by()
    toAppend = []
    for n in getDate:
        toAppend.append(n.time)
    def sortingDates(Dates):
        splitup = Dates.split('-')
        return splitup[2], splitup[1], splitup[0]
    sortedArray = sorted(toAppend, key=sortingDates)

    #function to add up all records by id
    

    sumArray = []
    numCache = []
    finalCache = []
    for t in range(0, len(sortedArray)):
        if t == 0:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(n.record)
                numCache.append(n.operator)
                numCache.append(n.record)
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedArray[t]
        if toCheck == sortedArray[t]:
            continue
        else:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(n.record)
                numCache.append(n.operator)
                numCache.append(n.record)
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedArray[t]

    final = addUp(finalCache)
    databaseDataQuery = sortedArray
    databaseTrimVersion = list(dict.fromkeys(databaseDataQuery))
    allRecords = records.query.order_by()
    return render_template("index.html", allRecords = allRecords, final = final)


if __name__ == "__main__":
    app.run(debug=True, port=80)
