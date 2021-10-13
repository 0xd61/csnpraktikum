import operator
from flask import Flask, render_template, url_for, redirect, jsonify
from flask.globals import request
from flask.helpers import flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, IntegerField, SubmitField, FloatField
from flask_sqlalchemy import SQLAlchemy
import numpy as np

#flask, db, key config
app = Flask(__name__)
app.config["SECRET_KEY"] = "admin4"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///csn_projekt_db"
db = SQLAlchemy(app)

#db.Model
class records(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    record = db.Column(db.String, nullable=False)
    operator = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)

#from model (testing)
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

def sortingDates(Dates):
    splitup = Dates.split('-')
    return  splitup[0], splitup[1], splitup[2]

@app.route("/add", methods=['GET', 'POST'])
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
    if id == "dealy":
        return jsonify('', render_template('db.html', sortedArray = sortedArray, sumArray = sumArray, databaseTrimVersion = 
    databaseTrimVersion, allRecords = allRecords, final = final))
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
        return jsonify('', render_template('db.html', sortedArray = sortedArray, sumArray = sumArray, databaseTrimVersion = databaseTrimVersion, allRecords = allRecords, final = final))
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
            return jsonify('', render_template("db.html", sortedArray = sortedArray, sumArray = sumArray, databaseTrimVersion = databaseTrimVersion, allRecords = allRecords, final = final))
        else:
            error = "No Record found!"
            return jsonify('', render_template("error.html", error = error))

@app.route("/history")
def history():
    allRecords = records.query.order_by()
    return render_template("history.html", allRecords = allRecords)



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
