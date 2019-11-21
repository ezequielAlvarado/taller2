# coding=utf-8
from flask import Flask, redirect, url_for
from flask import render_template, request, jsonify
import schemadb
import time
import json

tiempo = 3600 # Una hora atras
app = Flask(__name__)
app.config['DEBUG'] = True

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


@app.route('/history_dat', methods= ['POST'])
def get_d():
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
        return jsonify({'date' : 0, 'hum': 0, 'temp' : 0, 'cant': N})
    else:
        for item in x:
            date.append(item["Date"]) #agrego valores ya que date[0] no existe al crearlo vacio
            temp.append(item["Temp"])
            hum.append(item["Hum"]) 
        return jsonify({'date' : date, 'hum': hum, 'temp' : temp, 'cant': N})

@app.route('/history_sel', methods=['POST'])
def handle_intervalo():
    inter = request.values.get('selected')
    print(inter)
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
    print(tiempo)
    get_d()

if __name__ == "__main__":
    print(schemadb.connectbd())
    app.run(host='localhost', port=5000, debug=True)