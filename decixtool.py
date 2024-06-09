import requests
import ipaddress
from datetime import datetime
from datetime import date
import smtplib
import configparser
import re
import json

AS=""                     #AS que debe estar en el aspath
ID=""                     #Para diferenciar si tienes varias instancias corriendo
MAILS=""                  #Direcciones de envío de mail
PREFIX_DIFF=0            #diferencia de prefijos para mandar mail en valor absoluto

def carga_rangos(fichero):
    try:
        with open(fichero, "r") as f:
            lista_rangos=[]
            #print ("---------------Load ranges from",fichero,"---------------")
            for linea in f:
                try:
                    ip = ipaddress.IPv4Network(linea[:-1]) # para quitar el retorno de carro
                    #print(ip, "it is a correct network")
                    lista_rangos.append(linea[:-1]) 
                except ValueError:
                    print(linea, "it is a incorrect network. Not loaded")
            #print ("---------------Loaded Ranges---------------")
            return lista_rangos
    except (OSError, IOError) as e:
        print ("---------------No ranges to load---------------")
        return list()   

def carga_config():
    global MAILS
    global ID
    global AS
    global PREFIX_DIFF
    config = configparser.ConfigParser()
    try:
        with open ('decixtool.ini') as f:  #Falta gestionar si un id no existe en el fichero
            config.read_file(f)
            if 'ID' in config['default']:
                ID=config['default']['ID']
            if 'MAILS' in config['default']:
                MAILS=config['default']['MAILS'].split(sep=',')
            if 'AS' in config['default']:
                AS=config['default']['AS']
            if 'PREFIX_DIFF' in config['default']:
                PREFIX_DIFF=config['default']['PREFIX_DIFF']

    except (OSError, IOError) as e:
        print ("No configuration file")



def envia_correo(asunto, mensaje):
    remitente = "david.hernandezc@gmail.com"
    destinatario = MAILS
    asunto="DECIXTOOL: " + ID + " " + asunto
    #print("EMAIL with subject-->", asunto)
    email = """From: %s
To: %s
MIME-Version: 1.0
Content-type: text/html
Subject: %s
    
%s
""" % (remitente, ",".join(destinatario), asunto, mensaje)
    try:
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(remitente, MAILS, email)
        #print ("Email sent succesfully")
    except:
        print ("Error: we canot send the email "+str(asunto)+"<br>")



url_status="https://lg.de-cix.net/api/v1/routeservers/rs1_mad_ipv4/status"
url="https://lg.de-cix.net/api/v1/routeservers/rs1_mad_ipv4/neighbors/R192_33/routes" #ALC
url2="https://lg.de-cix.net/api/v1/routeservers/rs2_mad_ipv4/neighbors/R192_33/routes" #ALC
url3="https://lg.de-cix.net/api/v1/routeservers/rs1_mad_ipv4/neighbors/R192_145/routes" #ATO
url4="https://lg.de-cix.net/api/v1/routeservers/rs2_mad_ipv4/neighbors/R192_145/routes" #ATO


# Obtenemos solo las aceptadas

carga_config()
rangos=carga_rangos("rangos.txt")
log=""
hora = datetime.now().replace(microsecond=0)
log="-------------Start time: " + str(hora) + "-------------<BR>\n DECIXTOOL " + ID + " "+ str(len(rangos))+" Ranges <BR><BR><BR>\n"
texto2="""<TABLE BORDER="1"> <TR><TH>RANGE</TH><TH>STATUS</TH><TH>AS PATH</TH></TR>"""
log=log+texto2
texto2=""
data = {}
data["DECIXTOOL " + ID] = []

try:
    response=requests.get(url)
except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
        exit(0)
else:
        print('Success!')

dic=response.json()

# for key in dic:
#     print(key)
# api
# pagination
# imported
# filtered
# not_exported

paginas=dic["pagination"]["total_pages"]

pagina=0
fallo=0
aceptadas=dic["imported"]
filtradas=dic["filtered"]
redes_aceptadas=[]
for red in aceptadas:
    redes_aceptadas.append(red["id"])

while (paginas>1):
    pagina=pagina+1
    paginas=paginas-1
    url_page=url+"?page="+str(pagina)
    try:
        response=requests.get(url_page)
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
        exit(0)
    else:
        print('Success!')

    dic=response.json()
    aceptadas=dic["imported"]
    for red in aceptadas:
        redes_aceptadas.append(red["network"])


aspath="no data"

for rango in rangos:
    if rango in redes_aceptadas:
        texto2="<TR><TD>" + rango + " </TD><TD>Routed</TD><TD>" + str(aspath) + "</TD></TR>"
        data["DECIXTOOL " + ID].append({
                'range': rango,
                'Status': 'Routed'})

    else:
        #print ("ALERT: " + rango + " NOT Routed")
        texto="ALERT: " + rango + " NOT Routed"
        texto2="""<TR bgcolor="red"><TD>"""  + rango + "</TD><TD>NOT Routed</TD></TR>"
        data["DECIXTOOL " + ID].append({
                'range': rango,
                'Status': 'NOT Routed'})
        fallo+=1
    log=log+texto2
log=log+"</TABLE>"

with open('ultimo.json', 'w') as file:
    json.dump(data, file, indent=4)



num_prefijos_antes=-1
lista_prefijos_antes=[]
try:
    with open("num_prefijos.txt", "r") as fichero_prefijos:
        for linea in fichero_prefijos:
            lista_prefijos_antes.append(linea[:-1])
        num_prefijos_antes=lista_prefijos_antes[0]
except(OSError, IOError) as e:
        print ("There is no files with last prefix sample")

lista_prefijos_ahora=[]
lista_prefijos_ahora=redes_aceptadas
num_prefijos_ahora=len(lista_prefijos_ahora)
diferencia_de_rutas=num_prefijos_ahora-int(num_prefijos_antes)

texto="<br><br>Routed routes in DECIX for Vodafone Spain: " + str(num_prefijos_ahora)
log=log+texto
texto="<br><br>Last sample Routed in DECIX for Vodafone Spain: " + str(num_prefijos_antes)
log=log+texto
print("Routed routes in DECIX for Vodafone Spain: " + str(num_prefijos_ahora))
print("Last sample Routed routes in DECIX for Vodafone Spain: " + str(num_prefijos_antes))
with open("num_prefijos.txt", "w") as fichero_prefijos:
    fichero_prefijos.write(str(num_prefijos_ahora)+"\n")
    for prefijo in lista_prefijos_ahora:
        fichero_prefijos.write(str(prefijo)+"\n")

no_esta_ahora=[]
no_estaba_antes=[]

for prefijo_antes in lista_prefijos_antes:
    if "/" in str(prefijo_antes):
        if prefijo_antes not in lista_prefijos_ahora:
            no_esta_ahora.append(prefijo_antes)
for prefijo_ahora in lista_prefijos_ahora:
    if "/" in str(prefijo_ahora):
        if prefijo_ahora not in lista_prefijos_antes:
            no_estaba_antes.append(prefijo_ahora)
print("These prefixes were before and now they are not:")
print(no_esta_ahora)
print("These prefixes are now and they were not before:")
print(no_estaba_antes)

texto="<br><br>These prefixes were before and now they are not: " + str(no_esta_ahora)
log=log+texto
texto="<br><br>These prefixes are now and they were not before: " + str(no_estaba_antes)
log=log+texto


hora_fin = datetime.now().replace(microsecond=0)
texto2="<br><br><br>-------------End time: " + str(hora_fin) + "-------------<BR>\n"
log=log +texto2
if (fallo>0):
    envia_correo("FAIL IN " + str(fallo) + " RANGE(S)",log)
if ((diferencia_de_rutas>int(PREFIX_DIFF)) or (diferencia_de_rutas<-int(PREFIX_DIFF))):
    envia_correo("Sudden change of  " + str(diferencia_de_rutas) + " prefixes from the previous sample",log)
if ((hora.hour==0)and(hora.minute<5)):  
    envia_correo("Daily report",log)



logfile=open("ultimo.html", "w")
print (log, file=logfile)
logfile.close()
logfile=open("lista_prefijos.txt", "a")
for prefijo in lista_prefijos_ahora:
    print(str(hora_fin)+" "+ str(prefijo), file=logfile)
logfile.close()

logfile=open("lista_cambios.txt", "a")
for prefijo in no_esta_ahora:
    print(str(hora_fin)+" - "+ str(prefijo), file=logfile)
for prefijo in no_estaba_antes:
    print(str(hora_fin)+" + "+ str(prefijo), file=logfile)

logfile.close()












