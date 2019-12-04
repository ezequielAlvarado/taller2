import app
import pymongo

cliente = pymongo.MongoClient("mongodb://localhost:27017/")
db = cliente["dbtaller"]
mediciones = db["Medicion"]

def connectbd():
    global cliente
    global db
    global mediciones
    dblist = cliente.database_names()
    if "dbtaller" in dblist:
        return("Existe la base de datos.")
    else:
        default_create()

def default_create():
    global mediciones
    default = {"Temp": float(0), "Date": 0, "Hum": float(0) }
    x=mediciones.insert_one(default)


def add_data(Data):
    global mediciones
    print(Data[0])
    if(Data[0] < 1.0) or (Data[0] > 100.0):
        return ("Temp erronea")
    else:
        if(Data[1] < 1):
            return ("Dia erroneo")
        else:
            if(Data[2] < 0.0) or (Data[2] > 100.0):
                return ("Humedad erronea")
            else:
                med = {"Temp": Data[0], "Date": Data[1], "Hum": Data[2]}
                x= mediciones.insert_one(med)
                return ("Se inserto el dato")


def busc_tiempo(ts2):
    global mediciones
    a = mediciones.find({"Date": {"$gt": ts2}},{ "_id": 0, "Date": 1, "Temp": 1, "Hum": 1}).sort("Date", 1)
    return a


