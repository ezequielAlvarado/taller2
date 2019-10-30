from flask import Flask
from flask import render_template
from flask_mongoalchemy import MongoAlchemy     
from flask_socketio import SocketIO
import schemadb
import time



temp= 33
timestamp="p"
hum= 23
datos = ['1','2','3']


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['MONGOALCHEMY_DATABASE'] = 'bdtaller'
db = MongoAlchemy(app)
socketio = SocketIO(app)


@app.route("/")
def main():
    return render_template('home.html',temp=temp,timestamp=timestamp, hum=hum)


#@app.route('/history')
#def hist():
    #leo el historial de la bd 
    #return render_template('history.html', historial = his) #aca envio el dato de la lectura de la bd

def background_thread():
   # """Example of how to send server generated events to clients."""
    loopCount = 0
    vueltas = 0
    states = [12.1,04.1,26.1,30.1,49.1,28.1,27.1]
    humi = [52,54,56,50,59,58,57]
    print("-----------------> entro <-----------------------")
    times = [1571023418,1570835738,1571023417,1570835739,1571023415,1570835750,1570835750]
    while vueltas < 3:   
        datos[0]=states[loopCount]
        datos[1]=times[loopCount]
        datos[2]=humi[loopCount]
        print(datos[1])
        #med = Medicion(Temp = datos[0], Date = datos[1], Hum = datos[2])
        #med.save()
        #x = schemadb.add_data(datos)
        #print(x)
        loopCount += 1
        socketio.emit('evento', data = datos)
        time.sleep(2)
        if(loopCount > 6):
            loopCount = 0
            vueltas += 1
    
      


if __name__ == "__main__":
    socketio.start_background_task(target=background_thread)
    socketio.run(app,debug=True)
    
    
    

    

    

