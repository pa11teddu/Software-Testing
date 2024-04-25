# app.py
from flask import Flask
import pymysql.cursors
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'secret'

app.config['REPORT_TYPE_OPTIONS'] = ['Coding Error', 'Design Issue', 'Suggestion', 'Documentation', 'Hardware', 'Query']
app.config['SEVERITY_LEVELS'] = ['Fatal', 'Serious', 'Minor']
app.config['PRIORITY_LEVELS'] = [1, 2, 3, 4, 5]
app.config['STATUS_OPTIONS'] = ['Open', 'Closed']
app.config['RESOLUTION_OPTIONS'] = ['Pending', 'Fixed', 'Irreproducible', 'Deferred', 'As designed', "Can't be fixed", 'Withdrawn by reporter', 'Need more info', 'Disagree with suggestion']
app.config['RESOLUTION_VERSION_OPTIONS'] = [1, 2, 3, 4]
app.config['UPLOAD_FOLDER'] = 'C:/Users/030855537/Desktop'

# Database parameters
db_params = {
    'host': 'localhost',
    'user': 'root',
    'db': 'bughound_tracker',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Recaptcha secret key
RECAPTCHA_SECRET_KEY = '6Ldy0wQpAAAAAEvqi5ppVXvpRtOIXwS-fcE0Qppn'

# Scheduler for database cleanup
job_scheduler = BackgroundScheduler()
job_scheduler.start()

# Ensure the scheduler shuts down when the app context is destroyed
@app.teardown_appcontext
def cease_scheduler(sender, *args, **kwargs):
    if job_scheduler.state:
        job_scheduler.shutdown(wait=False)

# Import routes
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
