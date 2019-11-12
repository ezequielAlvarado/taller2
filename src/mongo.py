from pymongo import MongoClient
import json


client = MongoClient('localhost', 27017)
db = client["dbtaller"]
datos = db["Medicion"]

#x = datos.count()+1
#dato1 = {"_id": x, "Temp" : "23", "Hum":"56", "Date": "10/10/2019", "Time": {"H":"00","M":"00","S":"01"}}
#datos.insert_one(dato1)
#x = datos.count()+1
#dato2 = {"_id": x, "Temp" : "24", "Hum":"57", "Date": "10/10/2019", "Time": {"H":"00","M":"00","S":"02"}}
#datos.insert_one(dato2)


x= datos.find()
N = x.count() 
print(N)
dat = []
for item in x:
    print(item)
    dat.append(item["Date"])
for i in dat:
    print(i)
print(dat)
#for item in x:
#    print(item["Date"])
#datos.find({},{}) el primer {} del find es la parte del select
#x= datos.find().sort("_id", -1).limit(1) #me trae el ultimo dato (id mas grande)
#for item in x:
 #   print(item["Time"]["H"]) #Imprime el valor de Time en la hora H
