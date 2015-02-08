import cv2
import subprocess
import atexit

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, url_for
from forecastio import load_forecast

API_KEY = 'f86b667ec9806787371221af2d56a3d8'

image_time = datetime.now()


def get_temperature():
    forecast = load_forecast(API_KEY, 52.0056394, 4.351788)
    return forecast.currently().temperature


def upload_to_dropbox(image_time):
    temperature = get_temperature()
    source_file = 'static/image.jpg'
    destination_file = 'slimme-meter/image_{0}_{1:0.0f}.jpg'.format(image_time.strftime("%Y%m%dT%H%M%S"), temperature * 1000)
    run_command = '/home/pi/Dropbox-Uploader/dropbox_uploader.sh'
    subprocess.call([run_command, 'upload', source_file, destination_file])
    print(run_command)


def make_image():
    global image_time
    image_time = datetime.now()
    image_name = 'image.jpg'
    cap = cv2.VideoCapture(0)
    for frnr in range(5):
        ret, frame = cap.read()
    cap.release()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('static/{0}'.format(image_name), cv2.flip(gray, flipCode=1))
    upload_to_dropbox(image_time)

app = Flask(__name__)

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/')
def image():
    global image_time
    make_image()
    image_name = 'image.jpg'
    image_location = url_for('static', filename=image_name)
    image_time_string = image_time.strftime("%Y-%m-%d %H:%M")
    return render_template('image.html', image=image_location, time=image_time_string)


if __name__ == '__main__':
    cron = BackgroundScheduler(deamon=True)

    cron.add_job(make_image, 'interval', minutes=30)
    cron.start()

    # Shutdown your cron thread if the web process is stopped
    atexit.register(lambda: cron.shutdown(wait=False))

    app.run(host='0.0.0.0')
