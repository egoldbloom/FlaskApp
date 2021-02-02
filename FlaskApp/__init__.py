from flask import (
    Flask, 
    flash, 
    g, 
    jsonify,
    make_response, 
    redirect, 
    render_template, 
    request, 
    send_file, 
    send_from_directory,
    session, 
    url_for, 
    )
import sys
import traceback
import time
import os
from .content_management import Content
from .constants import CONSTANTS
from .dbconnect import connection

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, BooleanField
from pymysql import escape_string as thwart
import pymysql
import gc
# import email_validator
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import pygal
        
TOPIC_DICT = Content()

app = Flask(__name__, instance_path='/var/www/FlaskApp/FlaskApp/protected')

# ********* Set up flask_mail *********
app.config.update(
    MAIL_DEBUG=True,
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'evgoldbloom@gmail.com',
    MAIL_PASSWORD = 'iwantatruck'
    )
mail = Mail(app)

@app.route('/send-mail/')
def send_mail():
    try:
        if 'username' in session.keys():            
            username = session['username']
        else:
            username = "unknown"
        link = 'google.com'
        msg = Message("Forgot Password - PythonProgramming.net",
          sender="evgoldbloom@gmail.com",
          recipients=['e.goldbloom@gmail.com'])
        msg.body = 'Hello '+username+',\nYou or someone else has requested that a new password be generated for your account. If you made this request, then please follow this link:'+link
        msg.html = render_template('/mails/reset-password.html', username=username, link=link)
        mail.send(msg)
        return ('Mail sent!')
    except Exception as e:
        return("Exception " + repr(e) + " " +str(e)) 


# ********* File Downloads *********
@app.route('/download-to-browser/')
def download_to_browser():
    try:
        return render_template('downloads_to_browser.html')
    except Exception as e:
        return str(e)

@app.route('/file-downloads/')
def file_downloads():
    try:
        return render_template('downloads.html')
    except Exception as e:
        return str(e)

@app.route('/return-files/')
def return_files_tut():
    try:
        return send_file('/var/www/FlaskApp/FlaskApp/static/images/android-chrome-192x192.png', 
                         attachment_filename='android-chrome-192x192.png')
    except Exception as e:
        return str(e)    

# ********* Home page *********        
@app.route('/')
def homepage():
    return render_template("main.html")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            curr_time = int(time.time())
            if 'last_active' not in session.keys() or (curr_time - session['last_active']) > CONSTANTS["login_timeout"]:
                curr_path = request.path
                session.clear()
                session["curr_path"] = curr_path
                flash("Your login has timed out!")
                gc.collect()
                return redirect(url_for('login_page'))
            else:
                session['last_active'] = curr_time
                return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))

    return wrap


# ********* Setup a protected directory *********
def special_requirement(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            if 'goldbed' == session['username']:
                return f(*args, **kwargs)
            else:
                flash("Wrong user")
                return redirect(url_for('homepage'))
        except:
            flash("Failure in wrap")
            return redirect(url_for('homepage'))
    return wrap

@app.route('/protected/<path:filename>')
@special_requirement
def protected(filename):
    try:
        return send_from_directory(
            os.path.join(app.instance_path, ''),
            filename
        )
    except Exception as e:
        flash("Failure sending " + repr(e))
        return redirect(url_for('homepage'))


# ********* Interactive JQuery example *********    
@app.route('/interactive/')
def interactive():
    return render_template('interactive.html')

@app.route('/_background_process')
def background_process():
    try:
        lang = request.args.get('proglang', 0, type=str)
        if lang.lower() == 'python':
            return jsonify(result='You are wise')
        else:
            return jsonify(result='Try again.')
    except Exception as e:
        return str(e)
    
# ********* pygal example ********* 
@app.route('/pygalexample/')
def pygalexample():
    try:
        graph = pygal.Line()
        graph.title = '% Change Coolness of programming languages over time.'
        graph.x_labels = ['2011','2012','2013','2014','2015','2016']
        graph.add('Python',  [15, 31, 89, 200, 356, 900])
        graph.add('Java',    [15, 45, 76, 80,  91,  95])
        graph.add('C++',     [5,  51, 54, 102, 150, 201])
        graph.add('All others combined!',  [5, 15, 21, 55, 92, 105])
        graph_data = graph.render_data_uri()
        return render_template("graphing.html", graph_data = graph_data)
    except Exception as e:
        return(str(e))     
    

# ********* Dashboard *********
@app.route('/dashboard/')
@login_required
def dashboard():
    # flash("flash test!!!!")
    # flash("fladfasdfsaassh test!!!!")
    # flash("asdfas asfsafs!!!!")
    return render_template("dashboard.html", TOPIC_DICT = TOPIC_DICT)

@app.route('/login/', methods=["GET","POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":

            data = c.execute("SELECT password FROM users WHERE username = (%s)",
                             thwart(request.form['username']))
            
            data = c.fetchone()[0]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                session['last_active'] = int(time.time())

                flash("You are now logged in")
                if "curr_path" in session.keys():
                    curr_path = session["curr_path"]
                    session.pop("curr_path", None)
                    return redirect(curr_path)
                else:
                    return redirect(url_for("dashboard"))
            else:
                error = "Invalid credentials, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        #flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error = error)  
                    
   
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

class RegistrationForm(FlaskForm):
    username   = StringField('Username', [validators.Length(min=4, max=20)])
    name       = StringField('Name you go by', 
                             [validators.DataRequired(),
                              validators.Length(min=1, max=100)])
    email      = StringField('Email Address', [
                    validators.Length(min=6, max=50)
                    # validators.Email(message='Invalid email address format')
                    ])
    password   = PasswordField('New Password', [
                    validators.DataRequired(),
                    validators.EqualTo('confirm', message='Passwords must match')])
    confirm    = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 22, 2015)', 
                              [validators.DataRequired()])
    


@app.route('/register/', methods=["GET","POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if form.validate_on_submit():
            username  = form.username.data
            name      = form.name.data
            email     = form.email.data
            password  = sha256_crypt.encrypt((str(form.password.data)))
            c, conn   = connection()
            try:
                x = c.execute("SELECT * FROM users WHERE username = (%s)",
                              (thwart(username)))
            except pymysql.Error as e:
                return("Failure checking for previous user %d: %s" %(e.args[0], e.args[1]))

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                try:
                    x = c.execute("INSERT INTO users (username, goes_by_name, password, email, tracking) VALUES (%s, %s, %s, %s, %s)",
                              (thwart(username), thwart(name), thwart(password), thwart(email), thwart("/introduction-to-python-programming/")))
                    conn.commit()
                except pymysql.Error as e:
                    return("Failure inserting new user %d: %s" %(e.args[0], e.args[1]))

                flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username
                session['last_active'] = int(time.time())
                
                return redirect(url_for('dashboard'))

        return render_template("register.html", form=form)
    except AssertionError:
        """
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]
    
        return('An error occurred on line {} in statement {}'.format(line, text))
        """
        app.logger.error('An error occurred on line {} in statement {}'.format(line, text))
        return ("An error occurred during signup.")
    
    except Exception as e:
        rtn = "<p>Attr:</p>"
        for attr in dir(e):
            rtn = rtn + "<p>" + attr + "</p>"
        return(repr(e))
        

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('homepage'))
    
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    try:
      """Generate sitemap.xml. Makes a list of urls and date modified."""
      pages=[]
      ten_days_ago=(datetime.now() - timedelta(days=7)).date().isoformat()
      # static pages
      for rule in app.url_map.iter_rules():
          if "GET" in rule.methods and len(rule.arguments)==0:
              pages.append(
                           ["https://flaskapp.localhost"+str(rule.rule),ten_days_ago]
                           )

      sitemap_xml = render_template('sitemap_template.xml', pages=pages)
      response= make_response(sitemap_xml)
      response.headers["Content-Type"] = "application/xml"    
    
      return response
    except Exception as e:
        return(str(e))    

@app.route('/include_example/')
def include_example():
    replies = {'Jack':'Cool post',
               'Jane':'+1',
               'Erika':'Most definitely',
               'Bob':'wow',
               'Carl':'amazing!',}

    return render_template("includes_tutorial.html", replies = replies)  

@app.route('/jinjaman/')
def jinjaman():
    try:
        data = [15, '15', 'Python is good','Python, Java, php, SQL, C++','<p><strong>Hey there!</strong></p>']
        return render_template("jinja-templating.html", data = data)
    except Exception as e:
        return(str(e))  

@app.route('/converters/')                
@app.route('/converters/<string:article>/<int:page>/')
def convertersexample(article="MyArticle", page=1):
    try:    
        return render_template("converterexample.html", page=page, article=article)
    except Exception as e:
        return(str(e)) 
    
    
if __name__ == "__main__":
    app.run()
