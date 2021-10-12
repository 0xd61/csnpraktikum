import operator
from flask import Flask, render_template, url_for, redirect
from flask.globals import request
from flask.helpers import flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, IntegerField, SubmitField
from flask_sqlalchemy import SQLAlchemy


#flask, db, key config
app = Flask(__name__)
app.config["SECRET_KEY"] = "admin4"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///csn_projekt_db"
db = SQLAlchemy(app)

#db.Model
class records(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record = db.Column(db.String, nullable=False)
    operator = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)

#from model (testing)
class record_submit(FlaskForm):
    record_in = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    operator = StringField(validators=[DataRequired()])
    submit = SubmitField("Daten hinzufügen.", validators=[DataRequired()])

class recordToUpdate(FlaskForm):
    record_in = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    operator = StringField(validators=[DataRequired()])
    submit = SubmitField("Betrag verändern", validators=[DataRequired()])

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = record_submit()
    recordToSubmit = None
    timeToSubmit = None
    #when submiting form
    if form.validate_on_submit():
        #db.add
        toSubmit = records(record = form.record_in.data, time = form.time.data, operator = form.operator.data)
        db.session.add(toSubmit)
        db.session.commit()
        #clearing froms
        form.record_in.data = ""
        form.time.data = ""
        form.operator.data = ""
    return render_template("index.html", form = form)

@app.route('/update/<id>', methods=['POST', 'GET'])
def update(id):
    form = recordToUpdate()
    check = id
    toUpdate = records.query.get(id)
    if form.validate_on_submit():
        toUpdate.record = request.form['record_in']
        toUpdate.time = request.form['time']
        toUpdate.operator = request.form['operator']
        try:
            db.session.commit()
            flash("Der Datensatz wurde erfolgreich aktualisiert.")
            return redirect(url_for('history'))
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


@app.route("/history")
def history():
    allRecords = records.query.order_by()
    return render_template("history.html", allRecords = allRecords)

@app.route("/")
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
    def addUp(array):
        count = 0
        for n in range(0, len(array)):
            antiZero = n + 1
            if antiZero % 2 == 0:
                operator = array[n - 1]
                if operator == "+":
                    count = count + array[n]
                else:
                    count = count - array[n]
        return count

    sumArray = []
    numCache = []
    finalCache = []
    for t in range(0, len(sortedArray)):
        if t == 0:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(int(n.record))
                numCache.append(n.operator)
                numCache.append(int(n.record))
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedArray[t]
        if toCheck == sortedArray[t]:
            continue
        else:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                finalCache.append(n.operator)
                finalCache.append(int(n.record))
                numCache.append(n.operator)
                numCache.append(int(n.record))
            sumArray.append(addUp(numCache))
            numCache.clear()
            toCheck = sortedArray[t]

    final = addUp(finalCache)
    databaseDataQuery = sortedArray
    databaseTrimVersion = list(dict.fromkeys(databaseDataQuery))
    allRecords = records.query.order_by()
    return render_template("graph.html", sortedArray = sortedArray, sumArray = sumArray, databaseTrimVersion = 
    databaseTrimVersion, allRecords = allRecords, final = final)


if __name__ == "__main__":
    app.run(debug=True)
