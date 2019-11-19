# coding=utf-8
from flask import Flask
import datetime
import time
import pymongo
import schemadb



datos1 = [50.2,1572557926,96] #dia atras 
datos2 = [25.1,1572496726,95]
datos3 = [32.3,1572496626,22] #hora atras

act = time.time()
ts = 1571023418
#x = x.total_seconds()
ts2 = int(ts)
ts3 = ts2 - 3600 #Una hora atras.
ts4 = ts2 - 86400 #Un dia atras.
ts5 = ts2 - 604800 #Una semana atras.
ts6 = ts2 - (86400*365) #Un año atras.
ts6 =int(ts6)
print(ts3)
print(schemadb.connectbd())
schemadb.add_data(datos1)
schemadb.add_data(datos2)
schemadb.add_data(datos3)

#x = schemadb.buscar_dato_tiempo(ts4)
#N = x.count()
#print(N)
#if(N == 0):
#    print("No hay resultados.") 
#else:
#    for item in x:
#        print(item)

app = Flask(__name__)
app.config['DEBUG'] = True

if __name__ == "__main__":
    app.run(host='localhost', port=5000)

