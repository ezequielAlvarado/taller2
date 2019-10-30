from flask import Flask
from flask import render_template
#from flask_mongoalchemy import MongoAlchemy     
from flask_socketio import SocketIO
import time



temp= 33
timestamp="pollo"
hum= 23
datos = ['1','2']


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
#mongo = PyMongo(app, mongo.conect_db())



@app.route("/")
def main():
    return render_template('home.html',temp=temp,timestamp=timestamp)


@app.route('/history')
def hist():
    #leo el historial de la bd 
    return render_template('history.html') #aca envio el dato de la lectura de la bd

def background_thread():
   # """Example of how to send server generated events to clients."""
    loopCount = 0
    vueltas = 0
    states = ['22','24','26','30','29','28','27']
    print("-----------------> entro <-----------------------")
    times = ['15708357372','1570835738','1570835738','1570835739','1570835750','1570835750','1570835750']
    while vueltas < 3:   
        datos[0]=states[loopCount]
        datos[1]=times[loopCount]
        loopCount += 1
        print("-----------------> imprime 1 <-----------------------")
        socketio.emit('evento', data = datos)
        print("-----------------> emit <-----------------------")
        time.sleep(1)
        #guardo en la base de datos
        if(loopCount > 6):
            print("-----------------> vuelta <-----------------------")
            loopCount = 0
            vueltas += 1
    
      


if __name__ == "__main__":
    socketio.start_background_task(target=background_thread)
    socketio.run(app,debug=True)
    
