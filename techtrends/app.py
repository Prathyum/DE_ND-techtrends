from logging import handlers
import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Set logger to handle STDOUT and STDERR
stdout_handler = sys.stdout
stderr_handler = sys.stderr
handler = [stderr_handler, stdout_handler]


# Setting up logging 
logging.basicConfig(handlers=(logging.StreamHandler(stream=handler),logging.FileHandler('app.log')), 
                    level=logging.DEBUG, 
                    format=' %(levelname)s %(name)s%(asctime)s : %(message)s' 
                    )
# Function to get a database connection.
# This function connects to database with the name `database.db`

connection_count = 0

def get_db_connection():

    global connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get metrics for /metrics
def metrics_endpoint():
    """
    Increment no.of connections used.
    Count the total number of posts.
    """
    connection = get_db_connection()
    
    count = connection.execute('SELECT count(*) FROM posts').fetchone()
    post_count = count[0]
    connection.close()

    return post_count

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    
    global connection_count
    connection_count += 1
    
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):

    global connection_count
    connection_count += 1

    post = get_post(post_id)
    if post is None:
        logging.error('Article with id {} does not exists'.format(post_id))
        return render_template('404.html'), 404
    else:
        logging.info('Article "{}" retrieved!'.format(post['title']))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info('"About Us" page retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global connection_count
    connection_count += 1

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logging.info('Article "{}" created!'.format(title))

            return redirect(url_for('index'))

    return render_template('create.html')

# Define Healthz endpoint
@app.route('/healthz')
def healthz():
    
    try:
        connection = get_db_connection()
        connection.cursor()
        connection.execute('SELECT * FROM posts')
        connection.close()
        return {'result': 'OK - healthy'}
    except Exception:
        return {'result': 'NO - unhealthy'}, 500

# Define Metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    global connection_count

    post_count = metrics_endpoint()
    response = {
        'post_count': post_count,
        'db_connection_count': connection_count,
    }
    
    return response

# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
