from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b' # random string
Bootstrap(app)

##CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Movie.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

db.create_all()

# Create form class
class UpdateRating(FlaskForm):
    rating = StringField("Rating", validators=[DataRequired()])
    review = StringField("Review", validators=[DataRequired()])
    submit = SubmitField("Submit")

class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add")

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    start = 1
    for movie in all_movies[::-1]:
        movie.ranking = start
        start += 1
        db.session.commit()

    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = UpdateRating()
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_selected.rating = float(form.rating.data)
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))


    return render_template("edit.html",
                           form=form,)

@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        title = form.title.data
        p = {
            "api_key": os.environ["api_key"],
            "query": title
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=p)
        data = response.json()["results"]
        return render_template("select.html",
                               data=data, )
    return render_template("add.html", form=form)

@app.route("/fetch", methods=['GET', 'POST'])
def fetch():
    movie_id = request.args.get('id')
    p = {
        "api_key": os.environ["api_key"],
    }
    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params=p)
    data = response.json()

    new_movie = Movie(
        title=data["title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        rating=0,
        ranking=0,
        review="",
        img_url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
