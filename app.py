from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/avi_map')
def avi_map():
    return render_template('avi_map.html')

if __name__=="__main__":
    app.run(debug=True)