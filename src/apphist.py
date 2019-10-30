# coding=utf-8
from flask import Flask, redirect, url_for
from flask import render_template  
from flask_socketio import SocketIO
import schemadb
import time
import json

tiempo = 3600 # Una hora atras

app = Flask(__name__)
app.config['DEBUG'] = True
socketio = SocketIO(app)

@app.route('/history')
def hist():
    global tiempo
    ts = time.time()
    ts = int(ts)
    ts2 = ts - tiempo
    #leo el historial de la bd 
    x = schemadb.busc_tiempo(ts2)
    N = x.count()
    print(x)
    date = []
    temp = []
    hum = []
    print(N)
    print("llega")
    if(N == 0):
        print("No hay resultados.")
        return render_template('history.html', date=date, temp=temp, hum=hum, cant=0)
    else:
        for item in x:
            date.append(item["Date"]) #agrego valores ya que date[0] no existe al crearlo vacio
            temp.append(item["Temp"])
            hum.append(item["Hum"]) 
        return render_template('history.html', date=date, temp=temp, hum=hum, cant=N)


@socketio.on('intervalo')
def handle_intervalo(inter):
    print ("Intervalo: " + inter)
    global tiempo
    if(inter == "H"):
        tiempo = 3600 #Una hora atras.
    if(inter == "D"):
        tiempo = 86400 #Un dia atras.
    if(inter == "W"):
        tiempo = 604800 #Una semana atras.
    if(inter == "Y"):
        tiempo = (86400*365) #Un año atras.
    socketio.emit('reload')

if __name__ == "__main__":
    print(schemadb.connectbd())
    socketio.run(app,debug=True)