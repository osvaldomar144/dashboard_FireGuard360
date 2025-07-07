import cv2, time
from ultralytics import YOLO
import numpy as np
from djitellopy import Tello
from PIL import Image, ImageOps

import sys
import math
import threading
import requests


#---------------------------------------------------------------------------------------------------------- VARIABILI GLOBALI

drone = Tello()     #Tello

#Definisco variabili globali aruco

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

parameters = cv2.aruco.DetectorParameters()

detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

numero_aruco_base = 5; #numero di aruco da cercare

# Carica il modello con i pesi salvati
static_path = "/Users/AlexisMartinez/Documents/Uni/CPS/repository/FireGuard360/drone/Modello_Incendio"
path_to_image = static_path + "/verifica_incendio.jpg"
path_to_model = static_path + "/best.pt"

url = 'http://localhost:5001/fire_detection'

model = YOLO(path_to_model)

#---------------------------------------------------------------------------------------------------------- MAIN


def __main__(arg):
   if(int(arg) < 5 and int(arg) > 0):
      ##RICERCA E RAGGIUNGIMENTO DELL'ARUCO
      #numero_target = 1          #debug
       numero_target = int(arg)         #numero di cui fare la detection
   
       print("Argomento ricevuto: ")
   
       print(numero_target)
   
       drone.connect()
   
       print(f"Batteria: {drone.get_battery()}%")
   
       time.sleep(5)
   
       #cam = cv2.VideoCapture(0)
   
       drone.streamon()    #attivo la telecamera
   
       
       drone.takeoff()     #alzo il drone in volo
   
       go_to_position(numero_target)
    
       #avvio il riconoscimento dell'immagine in multithreading
       take_photo()    #faccio una foto con il drone
       time.sleep(2)
       thread = threading.Thread(target=yolo_model_testing)    #verifico la presenza dell'incendio in un test
       thread.start()     #avvio il secondo processo 
   
   
       go_home()   #torno a casa nel mentre
   
       drone.streamoff()
   else:
      print("Error in main: argument out of range 1-4")


#---------------------------------------------------------------------------------------------- UTILS

#funzione che fa una foto per il riconoscimento del drone
def take_photo():
    print("Faccio una foto all'ambiente per verificare l'incendio")
    img=leggi_immagine()
    cv2.imwrite(path_to_image, img)


#funzione che riporta il drone a casa
def go_home():
    print("Torno a casa")
    
    go_to_position(numero_aruco_base)  #torno alla posizione di partenza

    time.sleep(3)

    print("Tornato alla base, atterro")
    
    drone.land()

#funzione che muove il drone verso una posizione specifica
def go_to_position(target_code):

    print("Volo verso la posizione: ", target_code)

    trovato = False     #ha trovato aruco?

    posizionato = False     #aruco perfettamente centrato?

    arrivato = False

    while not trovato:

        #result, image = cam.read()

        image=leggi_immagine()

        trovato = is_detected_aruco(target_code, image)

        if not trovato:

            drone.rotate_clockwise(30)  #se non ho trovato l'aruco ruoto il drone di 15 gradi
            image=leggi_immagine()
            show_image(image)
            time.sleep(1)
            
        image=leggi_immagine()
        show_image(image)

    time.sleep(3)

    print("Fase 2")

    while not posizionato:

        image=leggi_immagine()

        x_center = is_centered(target_code, image)

        print(x_center)

        if(x_center>470 and x_center<490):  #nota riduci di 5 l'ho modificato

            posizionato=True

        elif(x_center>485):

            drone.rotate_clockwise(5)
            image=leggi_immagine()
            show_image(image)

        else:

            drone.rotate_counter_clockwise(5)
            image=leggi_immagine()
            show_image(image)

        show_image(image)

        time.sleep(1)

    arucosegment = 0

    soglia = 70 #soglia minima di grandezza dell'aruco

    #cm_backward = 0 #Quanto tornare indietro (quanto sono andato avanti, per algoritmo ancora più scrauso)

    img=leggi_immagine()

    arucosegment=aruco_segment(img, target_code)

    while(arucosegment < soglia): #continua ad andare avanti finchè vede aruco e tale aruco non è abbastanza grande

        if(is_detected_aruco(target_code, img)):

            #x_center = is_centered(numero, img)

            #if(x_center>465 and x_center<495):

            #    print("aruco segment")

            #    print(arucosegment)

            drone.move_forward(20)
            image=leggi_immagine()
            show_image(image)
            #cm_backward += 20

            #elif(x_center>485):

            #    drone.rotate_clockwise(5)

            #    print("Giro clockwise")

            #elif(x_center<485):

            #    drone.rotate_counter_clockwise(5)

            #    print("Giro counter clockwise")

        img=leggi_immagine()

        arucosegment=aruco_segment(img, target_code)

        show_image(img)
 
 
    print("Arrivato a destinazione")

    time.sleep(1)

def yolo_model_testing():
    
    im = Image.open(path_to_image)
    im_invert = ImageOps.invert(im)
    im_invert.save(path_to_image, quality=95)
    # Usa il modello per fare predizioni su un'immagine
    results = model(path_to_image)
    result = results[0]

    #effettuo la detection e la invio sull'endpoint
    detection = False
    if len(result.boxes) > 0:               #Se c'è almeno un riconoscimento
        print("Incendio rilevato: True")
        detection = True
    else:
        print("Incendio rilevato: False")
        detection = False
    
    send_detection(detection)

    # Stampa i risultati o salvali
    for result in results:
        result.show()
        result.save(filename='result.jpg')

#funzione che legge l'immagine dal drone

def leggi_immagine():

    image_read = drone.get_frame_read()

    return image_read.frame

#funzione che controlla se c'è il codice richiesto nell'immagine

def is_detected_aruco(numero, image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:

        if numero in ids:

            cv2.aruco.drawDetectedMarkers(image, corners, ids)

            return True

        else:

            return False

def is_centered(numero, image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(gray)

    x_centerPixel=0

    #y_centerPixel=0;

    if ids is not None:

        if numero in ids:

            cv2.aruco.drawDetectedMarkers(image, corners, ids)

            x_sum = corners[0][0][0][0]+ corners[0][0][1][0]+ corners[0][0][2][0]+ corners[0][0][3][0]

            #y_sum = corners[0][0][0][1]+ corners[0][0][1][1]+ corners[0][0][2][1]+ corners[0][0][3][1]

            x_centerPixel = x_sum*.25

            #y_centerPixel = y_sum*.25

            print(x_centerPixel)

            cv2.line(image, (int(x_centerPixel), 0), (int(x_centerPixel), 720), (0, 255, 0), 5)

    return x_centerPixel

def show_image(image):

    cv2.imshow('Detected Markers', image)

    cv2.waitKey(1)

#Calcola il lato di un aruco per avere una misura di quanto aumenta

#invia all'end point il risultato value
def send_detection(detection):
    payload = {'detection': detection} 
    response = requests.post(url, json=payload)
    print(response.status_code)

def aruco_segment(image, numero):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = detector.detectMarkers(gray)

    segment=0

    if ids is not None:

        if numero in ids:

            #area=cv2.contourArea(corners[0])

            segment = math.sqrt(math.pow((corners[0][0][1][0]- corners[0][0][0][0]), 2) + math.pow((corners[0][0][1][1]- corners[0][0][0][1]), 2))

    return segment

if __name__ == "__main__":

    if len(sys.argv) > 1:
        __main__(sys.argv[1])
    else:
        __main__(0)  # o un valore di default
 
