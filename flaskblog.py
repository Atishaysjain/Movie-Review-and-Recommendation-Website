from re import X
from flask import Flask, render_template, request, url_for,flash, redirect
from flask.wrappers import Response
from scipy.sparse import data
from forms import RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user 
import csv
import random
import difflib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
pd.options.display.max_columns = None

from scipy import stats
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet

import urllib.request
import json
app = Flask(__name__)
app.config['SECRET_KEY']='a8ca03f6bb27fb5d2e9543b0a5c0ded3'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
db=SQLAlchemy(app)
bcrypt=Bcrypt(app)
login_manager=LoginManager(app)

## New Code (Start)
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df2 = pd.read_csv('tmdb.csv')
count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(df2['soup'])

cosine_sim2 = cosine_similarity(count_matrix, count_matrix)

df2 = df2.reset_index()
indices = pd.Series(df2.index, index=df2['title'])
all_titles = [df2['title'][i] for i in range(len(df2['title']))]
## New Code (End)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(db.Model, UserMixin):
	id=db.Column(db.Integer,primary_key=True)
	username=db.Column(db.String(20),unique=True,nullable=False)
	email=db.Column(db.String(120),unique=True,nullable=False)
	password=db.Column(db.String(60),nullable=False)
	posts=db.relationship('Post',backref='author',lazy=True)
	def __repr__(self):
		return f"User('{self.username}','{self.email}')"

class Post(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	title=db.Column(db.String(100),nullable=False)
	date_posted=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
	content=db.Column(db.Text,nullable=False)
	user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
	def __repr__(self):
		return f"Post('{self.title}','{self.date_posted}')"

@app.route("/login",methods=['GET','POST'])
def login():
	form=LoginForm()
	if form.validate_on_submit():
		user=User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user,remember=form.remember.data)
			return render_template('home.html')
		else:
			flash('Login Unsucessful')

	return render_template('login.html',title='Login',form=form)

@app.route("/register",methods=['GET','POST'])
def register():
	form=RegistrationForm()
	if form.validate_on_submit():
		hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user=User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash('Account has been created for {form.username.data}!','success')
		return redirect(url_for('login'))
	return render_template('register.html',title='Register',form=form)

@app.route("/home",methods=['GET','POST'])
def home():
	if request.method=='POST':
		mk=request.form['mk']
		try:
			url='http://www.omdbapi.com/?apikey=34035a0a&type=movie&s='
			url=url+str(mk)
			url=url.replace(" ","+")
			json_obj=urllib.request.urlopen(url)
			data=json.load(json_obj)
			data=data['Search']
			
			with open('movieR.csv', 'a',newline='') as csv_file:
				fieldnames = ['Movie']
				writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
				writer.writerow({'Movie': mk})

		except KeyError:
			return(render_template('negative.html',name=mk))
		
		return render_template('about.html',data=data)
		
	return render_template('home.html')

@app.route("/about",methods=['GET','POST'])
def about():
	if request.method=='POST':
		imdb_id=request.form['imdbid']
		url='http://www.omdbapi.com/?apikey=34035a0a&i='+str(imdb_id)
		json_obj=urllib.request.urlopen(url)
		data=json.load(json_obj)
		return render_template('info.html',data=data)

@app.route("/info",methods=['GET','POST'])
def info():
	if request.method=='POST':
		return render_template('ThankYou.html')
	return render_template('home.html')

@app.route("/ThankYou",methods=['GET','POST'])
def ThankYou():
	if request.method=='POST':
		return render_template('home.html')

f_name = ''
@app.route("/review",methods=['GET','POST'])
def review():

	NewMovies=[]
	prediction = []
	with open('movieR.csv','r') as csvfile:
		readCSV = csv.reader(csvfile)
		NewMovies.append(random.choice(list(readCSV)))
		m_name = NewMovies[0][0]
		m_name = m_name.title()
	
		try:
			result_final = get_recommendations(m_name)
		except KeyError:
			print(" ** Anurag (Error): ", m_name)
			return render_template('review.html')

		f_name=m_name
		print(" ** Anurag (OK): ",f_name, ' ', m_name)
		names = []
		dates = []
		ratings = []
		overview=[]
		types=[]
		mid=[]
		for i in range(len(result_final)):
			names.append(result_final.iloc[i][0])
			dates.append(result_final.iloc[i][1])
			ratings.append(result_final.iloc[i][2])
			overview.append(result_final.iloc[i][3])
			types.append(result_final.iloc[i][4])
			mid.append(result_final.iloc[i][5])
			prediction.append(result_final.iloc[i][0])
	
	suggestions = get_suggestions()
		
	details=[]
	url='http://www.omdbapi.com/?apikey=34035a0a&type=movie&t='
	for i in prediction:
		i=i.replace(' ','%20')
		json_obj=urllib.request.urlopen(url+i)
		data=json.load(json_obj)
		details.append(data)	

	return render_template('review.html',details=details)

def get_recommendations(title):
	cosine_sim = cosine_similarity(count_matrix, count_matrix)
	idx = indices[title]
	sim_scores = list(enumerate(cosine_sim[idx]))
	sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
	sim_scores = sim_scores[1:11]
	movie_indices = [i[0] for i in sim_scores]
	tit = df2['title'].iloc[movie_indices]
	dat = df2['release_date'].iloc[movie_indices]
	rating = df2['vote_average'].iloc[movie_indices]
	moviedetails=df2['overview'].iloc[movie_indices]
	movietypes=df2['keywords'].iloc[movie_indices]
	movieid=df2['id'].iloc[movie_indices]

	return_df = pd.DataFrame(columns=['Title','Year'])
	return_df['Title'] = tit
	return_df['Year'] = dat
	return_df['Ratings'] = rating
	return_df['Overview']=moviedetails
	return_df['Types']=movietypes
	return_df['ID']=movieid
	return return_df

def get_suggestions():
	data = pd.read_csv('tmdb.csv')
	return list(data['title'].str.capitalize())

@app.route("/hello",methods=['GET','POST'])
def hello():
	if request.method=='GET':
		return render_template('hello.html')

@app.route("/Top_20_Rating",methods=['GET','POST'])
def Top_20_Rating():
	if request.method=='GET':
		return render_template('Top_20_Rating.html')

@app.route("/Bottom_20_Rating",methods=['GET','POST'])
def Bottom_20_Rating():
	if request.method=='GET':
		return render_template('Bottom_20_Rating.html')

@app.route("/Highest_Grossing",methods=['GET','POST'])
def Highest_Grossing():
	if request.method=='GET':
		return render_template('Highest_Grossing.html')

@app.route("/Least_Grossing",methods=['GET','POST'])
def Least_Grossing():
	if request.method=='GET':
		return render_template('Least_Grossing.html')

@app.route("/Highest_Budget",methods=['GET','POST'])
def Highest_Budget():
	if request.method=='GET':
		return render_template('Highest_Budget.html')

@app.route("/Lowest_Budget",methods=['GET','POST'])
def Lowest_Budget():
	if request.method=='GET':
		return render_template('Lowest_Budget.html')

@app.route("/Most_lengthy_movies",methods=['GET','POST'])
def Most_lengthy_movies():
	if request.method=='GET':
		return render_template('Most_lengthy_movies.html')

@app.route("/logout",methods=['GET','POST'])
def logout():
	if request.method=='GET':
		return render_template('logout.html')

if __name__=='__main__':
	app.run(debug=True)
