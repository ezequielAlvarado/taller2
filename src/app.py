from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

@app.route("/")
def main():
    return render_template('home.html')
    
if __name__ == "__main__":
    app.run("0.0.0.0", port=4000, debug=True)