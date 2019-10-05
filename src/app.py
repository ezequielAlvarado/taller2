from flask import Flask
from flask import render_template

app = Flask(__name__)       

@app.route("/home")
def main():
    return render_template('home.html')

@app.route('/history')
def hist():
    return render_template('history.html')
    
if __name__ == "__main__":
    app.run("0.0.0.0", port=4000, debug=True)
