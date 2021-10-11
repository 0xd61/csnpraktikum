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
    time = db.Column(db.String, nullable=False)

#from model (testing)
class record_submit(FlaskForm):
    record_in = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    submit = SubmitField("Daten hinzufügen.", validators=[DataRequired()])

class recordToUpdate(FlaskForm):
    record_in = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    submit = SubmitField("Betrag verändern", validators=[DataRequired()])

@app.route("/", methods=['GET', 'POST'])
def index():
    form = record_submit()
    recordToSubmit = None
    timeToSubmit = None
    #when submiting form
    if form.validate_on_submit():
        #db.add
        toSubmit = records(record = form.record_in.data, time = form.time.data)
        db.session.add(toSubmit)
        db.session.commit()
        #clearing froms
        form.record_in.data = ""
        form.time.data = ""
    return render_template("index.html", form = form)

@app.route('/update/<id>', methods=['POST', 'GET'])
def update(id):
    form = recordToUpdate()
    check = id
    toUpdate = records.query.get(id)
    if form.validate_on_submit():
        toUpdate.record = request.form['record_in']
        toUpdate.time = request.form['time']
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

@app.route("/graph")
def graph():
    #sorting dates and appending to an array
    getDate = records.query.order_by()
    toAppend = []
    for n in getDate:
        toAppend.append(n.time)
    def sorting(L):
        splitup = L.split('-')
        return splitup[2], splitup[1], splitup[0]
    sortedArray = sorted(toAppend, key=sorting)

    #function to add up all records by id
    def multiplyList(toAdd) :
        result = 0
        for x in toAdd:
            result = result + x
        return result
    finalto = []
    test = []
    for t in range(0, len(sortedArray)):
        if t == 0:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                test.append(int(n.record))
            finalto.append(multiplyList(test))
            test.clear()
            toCheck = sortedArray[t]
        if toCheck == sortedArray[t]:
            continue
        else:
            tofilter = records.query.filter_by(time = sortedArray[t])
            for n in tofilter:
                test.append(int(n.record))
            finalto.append(multiplyList(test))
            test.clear()
            toCheck = sortedArray[t]

    databaseDataQuery = sortedArray
    databaseTrimVersion = list(dict.fromkeys(databaseDataQuery))
    
    final = multiplyList(finalto)
    return render_template("graph.html", sortedArray = sortedArray, final = final, test = test, finalto = finalto, databaseTrimVersion = databaseTrimVersion)


if __name__ == "__main__":
    app.run(debug=True)
