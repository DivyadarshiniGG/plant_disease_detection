import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from PIL import Image
import torchvision.transforms.functional as TF
import CNN
import numpy as np
import torch
import pandas as pd
import mysql.connector




# Establish a connection to your MySQL database
db = mysql.connector.connect(host='localhost', user='root', password='', port='3306', database='data')

# Create a cursor object to interact with the database


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
PERMANENT_SESSION_LIFETIME = 1800

# Set the SECRET_KEY before performing any session-related operations
app.config['SECRET_KEY'] = os.urandom(24)

Session(app)
# Use this cursor to execute queries



disease_info = pd.read_csv('disease_info.csv' , encoding='cp1252')
supplement_info = pd.read_csv('supplement_info.csv',encoding='cp1252')

model = CNN.CNN(39)    
model.load_state_dict(torch.load("plant_disease_model_1_latest.pt"))
model.eval()

def prediction(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index


app = Flask(__name__)

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/usignup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username is already taken
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return render_template('usignup.html', error='Username already exists. Please choose a different one.')
        else:
            # Insert the new user into the database
            insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, password))
            db.commit()  # Commit the transaction
            
            # Redirect to login page after successful signup
            return redirect('/login?signup_success=true')
        
        cursor.close()
    
    # Render the signup page
    return render_template('usignup.html')


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            # User found, set session variable to indicate user is logged in
            session['logged_in'] = True
            return redirect('/home')  # Redirect to home page after successful login
        else:
            # Handle incorrect credentials
            return render_template('login.html', error='Invalid credentials. Please try again.')
        
        cursor.close()
    
    # Render the login page
    return render_template('login.html')

@app.route('/home', methods=['POST'])


# Assuming you have established a connection to your MySQL database (db) and created a cursor (cursor) as shown in the previous example

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query to check if the provided username and password exist in the database
        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()  # Fetches the first row
        
        if user:
            # User found, redirect to the home page or perform further actions after successful login
            return render_template('home.html')
        else:
            # Handle incorrect credentials, redirect to login page with an error message
            return render_template('login.html', error='Invalid credentials. Please try again.')
        cursor.close()



@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/index')
def ai_engine_page():
    return render_template('index.html')

@app.route('/mobile-device')
def mobile_device_detected_page():
    return render_template('mobile-device.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        filename = image.filename
        file_path = os.path.join('static/uploads', filename)
        image.save(file_path)
        print(file_path)
        pred = prediction(file_path)
        title = disease_info['disease_name'][pred]
        description =disease_info['description'][pred]
        prevent = disease_info['Possible Steps'][pred]
        image_url = disease_info['image_url'][pred]
        supplement_name = supplement_info['supplement name'][pred]
        supplement_image_url = supplement_info['supplement image'][pred]
        supplement_buy_link = supplement_info['buy link'][pred]
        return render_template('submit.html' , title = title , desc = description , prevent = prevent , 
                               image_url = image_url , pred = pred ,sname = supplement_name , simage = supplement_image_url , buy_link = supplement_buy_link)

@app.route('/market', methods=['GET', 'POST'])
def market():
    return render_template('market.html', supplement_image = list(supplement_info['supplement image']),
                           supplement_name = list(supplement_info['supplement name']), disease = list(disease_info['disease_name']), buy = list(supplement_info['buy link']))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove logged_in session variable
    return redirect('/login')  # Redirect to login page after logout




if __name__ == '__main__':
    app.run(debug=True)
