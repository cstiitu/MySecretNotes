import json, sqlite3, click, functools, os, hashlib,time, random, sys
from flask import Flask, current_app, g, session, redirect, render_template, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash




### DATABASE FUNCTIONS ###

def connect_db():
    conn = sqlite3.connect(app.database)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with our great SQL schema"""
    conn = connect_db()
    db = conn.cursor()
    db.executescript("""

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assocUser INTEGER NOT NULL,
    dateWritten DATETIME NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);
""")
    db.execute("INSERT INTO users VALUES(null,?, ?);", ("admin", "pbkdf2:sha256:150000$siQ6si2q$eb30acb6b5751a022ad0101c85eda833dca9f8776e191ca28b6286abc0a08495"))
    db.execute("INSERT INTO users VALUES(null,?, ?);", ("bernardo", "pbkdf2:sha256:150000$xbRn40ZJ$e755f49aec660af12a59ab41703f747165522328716146d8991ac7addbd1aeae"))
    db.execute("INSERT INTO users VALUES(null,?, ?);", ("hans_bjarne", "pbkdf2:sha256:150000$xhTcwDIz$1daa3d226916c2740add892e66f20728a093534ba9da380ba7adb551a4a0c288"))
    db.execute("INSERT INTO notes VALUES(null,2,'1993-09-23 10:10:10','hello my friend');")
    db.execute("INSERT INTO notes VALUES(null,2,'1993-09-23 12:10:10','i want lunch pls');")
    db.execute("INSERT INTO notes VALUES(null,3,'2011-11-11 11:11:11','Very private note to self: How to get into SSH: ssh -J pensim@130.226.143.130 hans_bjarne@10.0.1.47 password: mygoodpassword');")
    conn.commit()



### APPLICATION SETUP ###
app = Flask(__name__)
app.database = "db.sqlite3"
app.secret_key = os.urandom(32)

### ADMINISTRATOR'S PANEL ###
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return redirect(url_for('notes'))


@app.route("/notes/", methods=('GET', 'POST'))
@login_required
def notes():
    importerror=""
    #Posting a new note:
    if request.method == 'POST':
        if request.form['submit_button'] == 'add note':
            note = request.form['noteinput'].strip()
            db = connect_db()
            c = db.cursor()
            statement = "INSERT INTO notes(id,assocUser,dateWritten,note) VALUES(null,?,?,?);"
            fields = (session['userid'],time.strftime('%Y-%m-%d %H:%M:%S'),note)
            print(statement)
            c.execute(statement, fields)
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'import note':
            noteid = request.form['noteid']
            db = connect_db()
            c = db.cursor()
            statement = "SELECT * from NOTES where id = ?"
            fields = (noteid,)
            c.execute(statement, fields)
            result = c.fetchone()
            if(result is not None):
                statement = "INSERT INTO notes(id,assocUser,dateWritten,note) VALUES(null,?,?,?);"
                fields = (session['userid'],result['dateWritten'],result['note'])
                c.execute(statement, fields)
            else:
                importerror="No such note with that ID!"
            db.commit()
            db.close()
    
    db = connect_db()
    c = db.cursor()
    statement = "SELECT * FROM notes WHERE assocUser = ?;"
    fields = (session['userid'],)
    print(statement)
    c.execute(statement, fields)
    notes = c.fetchall()
    print(notes)
    
    return render_template('notes.html',notes=notes,importerror=importerror)

@app.route("/delete/", methods=["POST"])
def deleteNote():
    if request.method == 'POST':
        noteid = request.form['noteid']
        db = connect_db()
        c = db.cursor()
        statement = "DELETE FROM notes WHERE id = ?;"
        fields = (noteid,)
        c.execute(statement, fields)
        db.commit()
        db.close()
    return redirect(url_for('notes'))



@app.route("/login/", methods=('GET', 'POST'))
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        statement = "SELECT * FROM users WHERE username = ?;"
        fields = (username,)
        c.execute(statement, fields)
        result = c.fetchone()

        if (result is not None):
            if check_password_hash(result['password'], password):
                session.clear()
                session['logged_in'] = True
                session['userid'] = result['id']
                session['username'] = result['username']
                return redirect(url_for('index'))
            else:
                error = "Wrong username or password!"
        else:
            error = "Wrong username or password!"
    return render_template('login.html',error=error)


@app.route("/register/", methods=('GET', 'POST'))
def register():
    errored = False
    errormessage = ""
    if request.method == 'POST':
        
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            errored = True
            errormessage = "Username and Password are required fields."
        elif len(username) < 3:
            errored = True
            errormessage = "Username must be at least 3 characters long."
        elif len(username) > 50:
            errored = True
            errormessage = "Username too long."
        elif len(password) < 8:
            errored = True
            errormessage = "Password must be at least 8 characters long."
        elif len(password) > 100:
            errored = True
            errormessage = "Password too long."

        if(not errored):
            hashed_password = generate_password_hash(password)

            db = connect_db()
            c = db.cursor()

            user_statement = "SELECT * FROM users WHERE username = ?;"
            user_fields = (username,)
            c.execute(user_statement, user_fields)
            if(c.fetchone() is not None):
                errored = True
                errormessage = "That username is already in use by someone else!"

            statement = "INSERT INTO users(id,username,password) VALUES(null,?,?);"
            fields = (username,hashed_password)
            print(statement)
            c.execute(statement, fields)
            db.commit()
            db.close()
            return f"""<html>
                        <head>
                            <meta http-equiv="refresh" content="2;url=/" />
                        </head>
                        <body>
                            <h1>SUCCESS!!! Redirecting in 2 seconds...</h1>
                        </body>
                        </html>
                        """
        
    return render_template('register.html',errormessage=errormessage)


@app.route("/logout/")
@login_required
def logout():
    """Logout: clears the session"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    #create database if it doesn't exist yet
    if not os.path.exists(app.database):
        init_db()
    runport = 5000
    if(len(sys.argv)==2):
        runport = sys.argv[1]
    try:
        app.run(host='0.0.0.0', port=runport) # runs on machine ip address to make it visible on netowrk
    except:
        print("Something went wrong. the usage of the server is either")
        print("'python3 app.py' (to start on port 5000)")
        print("or")
        print("'sudo python3 app.py 80' (to run on any other port)")