from flask import Flask, render_template, flash ,redirect, request, url_for, session , logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'iiita123'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result=cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg= 'No Articles Found'
        return render_template('articles.html',msg=msg)
    
    #close connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    cur.execute("SELECT * FROM articles WHERE id= %s ",[id] )

    article = cur.fetchone()

    return render_template('article.html',  article = article)

class Registerform(Form):
    name = StringField('Name',[validators.Length(min=1,max=30)])
    username = StringField('Username',[validators.Length(min=1,max=30)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='passwords do not match')
    ])
    confirm = PasswordField('confirm password')

@app.route('/register',methods=['GET','POST'])
def register():
    form =Registerform(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email =form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO users(name ,email_id ,user_name ,password ) VALUES(%s, %s, %s, %s)",(name,email,username,password))

        #Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('you are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html',form=form)

#user login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method =='POST':
        #get form feilds
        username = request.form['username']
        password_candidate = request.form['password']

        #craete cursor

        cur =mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE user_name=%s",[username])
        if result>0 :
            #get hash
            data = cur.fetchone()
            password = data['password']

            #campare passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('you are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error = error)
            # cur close
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error = error)

    return render_template('login.html')

# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('you are now logged out','success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result=cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg= 'No Articles Found'
        return render_template('dashboard.html',msg=msg)
    
    #close connection
    cur.close()

#Article form class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1,max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])
    
#Add article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cur =mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES (%s ,%s, %s)",(title,body,session['username']))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        #flash msg 
        flash('Article created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

#edit article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    # get article by id
    cur.execute("SELECT * from articles WHERE id= %s",[id])
    
    article = cur.fetchone()

    form = ArticleForm(request.form)
    
    form.title.data = article['title']
    form.body.data = article['body']

    #cur.close()

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cur =mysql.connection.cursor()

        #execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title,body,id))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        #flash msg 
        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    #execute

    cur.execute("DELETE FROM articles WHERE id = %s ",[id])

    mysql.connection.commit()

    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
