from flask import Flask, flash, session, jsonify, render_template, g, url_for, request, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

import os

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

engine = create_engine("DATABASE_URL")
db = scoped_session(sessionmaker(bind=engine))

app.secret_key = os.urandom(20)



@app.route('/', methods=['POST', 'GET'])
def index():

    if request.method == 'POST':
        session.pop('user', None)
        password = request.form.get("password")
        usermail = request.form.get("usermail")
        person = db.execute(
            "select * from userdata where usermail=:usermail", {"usermail": usermail}).fetchone()
        if person is None or person.password != password:
            return render_template('signin.html', wrongpassword=True)
        elif person.password == password:
            session['user'] = person.username
            return redirect(url_for('homepage'))

    return render_template("signin.html", wrongpassword=False)


@app.route('/signuppage')
def signuppage():
    return render_template('signup.html', mailexisted=False)


@app.route('/signup', methods=['POST'])
def signup():
    mailexisted = False
    username = request.form.get("username")
    usermail = request.form.get("usermail")
    password = request.form.get("password")

    if db.execute("select * from userdata where usermail=:usermail", {"usermail": usermail}).rowcount == 1:
        return render_template("signup.html", mailexisted=True)
    db.execute("insert into userdata (username,usermail,password) values (:username,:usermail,:password)", {
               "username": username, "usermail": usermail, "password": password})
    db.commit()
    return render_template('successsignup.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    if g.user:
        key = "%"+request.form.get("search")+"%"
        books = db.execute("select * from books where lower(title) like :title or lower(author) like :author or year like :year or isbn like :isbn" ,
                           {"title": key, "author": key, "year":key,"isbn":key}).fetchall()
        return render_template('homepage.html', list=books, user=session['user'])
    return redirect(url_for('index'))


@app.route('/homepage', methods=['POST', 'GET'])
def homepage():
    if g.user:
        return render_template("homepage.html", user=session['user'])
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']


@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return render_template('signin.html')


@app.route('/reviews/<string:title>')
def reviews(title):
    data_of_book = db.execute(
        "select * from books where title=:title", {"title": title}).fetchone()
    goodreads = requests.get("https://www.goodreads.com/book/review_counts.json",
                             params={"key": "API_KEY", "isbns": data_of_book.isbn})
    goodreads_data = goodreads.json()
    review = db.execute(
        "select * from reviews where title=:title", {"title": title}).fetchall()
    avg_rating = goodreads_data['books'][0]['average_rating']
    work_rating_count = goodreads_data['books'][0]['work_ratings_count']
    return render_template("reviewpage.html", data=data_of_book, review_list=review, avg_rating=avg_rating, work_rating_count=work_rating_count)


@app.route('/api/<string:isbn>')
def api(isbn):
    book = db.execute(
        "select * from books where isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return render_template('error.html')
    else:
        goodreads = requests.get("https://www.goodreads.com/book/review_counts.json",
                                 params={"key": "2EDc7SiQWEy7hLh3ADVk0w", "isbns": isbn}).json()
        return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "ratings_count": goodreads['books'][0]['ratings_count'],
            "reviews_count":  goodreads['books'][0]['reviews_count']
        })


@app.route('/submit_review/<string:title>',  methods=['POST','GET'])
def submit_review(title):
    if g.user:
        ref=db.execute("select * from reviews where username=:username and title=:title",{"username":g.user,"title":title}).fetchone()
        if ref is None:
            review_text = request.form.get("Field")
            rating = request.form.get("rating")
            db.execute(
                "Insert into reviews(username,title,review,rating) values(:username,:title,:review,:rating)",
                                {"username": g.user, "title": title, "rating": rating, "review": review_text})
            db.commit()
            return redirect(url_for('reviews',title=title))
        else:
            flash('* You cannot review the book twice!')
            return redirect(url_for('reviews',title=title))


if __name__ == "__main__":
    app.run(debug=True)
    wrongpassword = False
    mailexisted = False
