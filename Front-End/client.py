import os
import gi
import sys
import time
import threading
import requests
import json

from tkinter import *
from tkinter.filedialog import askopenfilename

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

class Application(Frame):

    def getNameFromPath(self,element):
        counter=len(element)-1
        result=""
        while(counter>0):
            if(element[counter]=='/'):
                break
            result=element[counter]+result
            counter=counter-1
        aux=""
        counter=0
        while(counter<(len(result)-1)):
            if(result[counter]=='.'):
                break
            aux=aux+result[counter]
            counter=counter+1
        return aux

    def request(self, command, add):
        url = "http://localhost:4200/"+str(command)+"/"+str(self.entrada.get())+add
        print (url)
        r=""
        try:
            r = requests.post(url,"")
            #print (r.text)
        finally:
            print ("Consulta completa")
        return r

    def login(self):
        self.msgUserValue.set("Usuario establecido: "+str(self.entrada.get()))
        self.getMusicFromuser()
        self.state="stop"
        #self.msgUser.config(text=str(1))

    def play(self):
        if(self.state=="pause"):
            self.request("play","")
            self.state="play"
        elif(self.state=="stop"):
            print("=================INICIO==========================================")
            #Detener hilo de ejecucion
            #Ver cual cancion es
            #enviar por peticion la cancion
            self.request("dispatcher","/"+self.listbox.get(self.listbox.curselection()[0])+".mp3") #activar dispatcher
            resp= self.request("connection","") #obtener puerto
            data=resp.json()
            puerto=data['port']
            ThreadedPlayMusic(puerto).start()
            print(self.request("play",""))
            self.state="play"
            print("===========================================================")
        print (self.state)

    def pause(self):
        self.state="pause"
        self.request("pause","")
        print (self.state)

    def stop(self):
        self.state="stop"
        self.request("stop","")
        print (self.state)

    def add(self):
        file_name = askopenfilename(title = "Selecciona cancion",defaultextension = ".mp3", filetypes=[("MP3", ".mp3")])
        url = "http://localhost:5001/"+str(self.entrada.get())+"/"+self.getNameFromPath(file_name)
        data = {'timeDuration':10}
        mp3_fd = open(file_name, 'rb')
        files = {'file': mp3_fd}
        try:
            r = requests.post(url, files=files, json=data)
        finally:
            mp3_fd.close()
            self.getMusicFromuser()

    def refresh(self):
        self.getMusicFromuser()

    def getMusicFromuser(self):
        url = "http://localhost:5001/"+str(self.entrada.get())
        data = {'timeDuration':10}
        r=""
        try:
            r = requests.get(url, json=data)
        finally:
            print ("Termino de cargar canciones")
            self.listbox.delete(0, END)#clean listbox
            values=r.json()
            counter=0
            while (counter< len(values['msg'])):
                self.listbox.insert(END,values['msg'][counter]["songname"])
                counter=counter+1





    def createWidgets(self):
        self.window.geometry("700x600+0+0")
        self.window.title("JukebOS")

        self.lblMaterias= Label(self.window, text  = "Ingrese usuario").place(x=50,y=30)
        self.entrada=StringVar()
        self.txtUser= Entry(self.window,textvariable=self.entrada,width=30).place(x=50,y=60)
        self.btnLogin= Button(self.window, text="Establecer",height=2,width=10,command=self.login).place(x=50,y=90)
        self.msgUserValue=StringVar()
        self.msgUser= Label(self.window, textvariable  = self.msgUserValue).place(x=200,y=90)

        self.labelframe = LabelFrame(self.window, text="Lista de canciones",width=400, height=400)
        self.labelframe.place(x=50,y=150)

        self.scrollbar = Scrollbar(self.labelframe)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox = Listbox(self.labelframe, bd=0, yscrollcommand=self.scrollbar.set)
        self.listbox.pack()
        self.scrollbar.config(command=self.listbox.yview)

        self.btnPlay= Button(self.window, text="Play",height=2,width=10,command=self.play).place(x=230,y=170)
        self.btnPause= Button(self.window, text="Pause",height=2,width=10,command=self.pause).place(x=230,y=220)
        self.btnStop= Button(self.window, text="Stop",height=2,width=10,command=self.stop).place(x=230,y=270)

        self.btnAddMusic= Button(self.window, text="Añadir Cancion",height=2,width=10,command=self.add).place(x=50,y=320)
        self.btnStop= Button(self.window, text="Refrescar Lista",height=2,width=10,command=self.refresh).place(x=150,y=320)

    def __init__(self, master=None):
        self.state="stop"
        self.userName="default"

        self.window=master
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

#self.music_thread=ThreadedPlayMusic(self.puerto).start()
class ThreadedPlayMusic(threading.Thread):
    def __init__(self,puerto):
        threading.Thread.__init__(self)
        self.puerto=str(puerto)
    def run(self):
        print("Puerto Obtenido en thread:"+self.puerto)
        os.system ('gst-launch-1.0 tcpclientsrc port='+str(self.puerto)+' host=127.0.0.1 ! decodebin ! autoaudiosink sync=false')
        #pipeline.set_state(Gst.State.NULL)

root = Tk()
Gst.init(None)
GObject.threads_init()

app = Application(master=root)
app.mainloop()
root.destroy()
