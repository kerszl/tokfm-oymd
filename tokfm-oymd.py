#!/usr/bin/python3
#audycje tok-fm
from bs4 import BeautifulSoup
from urllib.request import urlopen
from time import sleep
import re
import os
import sqlite3
from sqlite3 import Error
from random import randrange
from datetime import datetime
from shutil import copyfile
import json
import sys
from pathlib import Path


#przykladowy link
#page_link='https://audycje.tokfm.pl/audycja/87,Prawda-Nas-Zaboli?offset=8'
#page_link='file:///D:/temp/offczarek.html'
PROGRAM_WERSJA="0.2"
PROGRAM_DATA="11.06.2020"
PROGRAM_NAME="Tok-Fm-Crawler"

#database_file=r'D:\temp\tokfm\tokfm.db'

database_file='tokfm.db'

OFFSET_LINK="?offset="
MAIN_LINK='https://audycje.tokfm.pl/audycja/'


def zaladuj_audycje_json():    
    try:
        with open('tok-fm.json', 'r') as f:
            AUDYCJE_LINK_=json.load(f)            
    except ValueError as e:                
        print ("Problem z plikiem tok-fm.json lub formatem json")
        print (e)        
        exit()
    return AUDYCJE_LINK_
#-dane linków audycji są w json
AUDYCJE_LINK = zaladuj_audycje_json()



def max_ilosc_stron(audycja_ident):
    nr_site=randrange(13213432,93213439)
    
    page_link=MAIN_LINK+audycja_ident+OFFSET_LINK+str(nr_site)
    body=urlopen(page_link)
    soup = BeautifulSoup(body,'html.parser')
    naglowek=soup.find('head')
    max_strona=naglowek.find('link', rel="canonical").attrs['href']
    

    if re.search(r'=[0-9]*$', max_strona) is None:
        max_strona=1
    else:
        max_strona=max_strona.split("=")[-1]
                                     
    page_link=MAIN_LINK+audycja_ident+OFFSET_LINK+str(max_strona)
    print ("Maxymalny odnosnik to: "+page_link)    
    return max_strona    




def zgraj_strone_audycji (audycja_ident,nr_site):    
    AUDYCJA={}
    czekaj=randrange(1,8)
    page_link=MAIN_LINK+audycja_ident+OFFSET_LINK+str(nr_site)
    print ("")
    print (page_link+" "+str(czekaj)+" sekund przerwy")                
#   page_link='file:///D:/temp/offczarek.html'    

    body=urlopen(page_link)
    
    

    soup = BeautifulSoup(body,'html.parser')
    
    ANDROID_FILES_CLASS_ID="tok-podcasts__item tok-podcasts__item--name"

    audycje=soup.find('div',{"data-miejsce":"Strona: audycja"})
    audycje_metadane=audycje.findAll('div', class_=ANDROID_FILES_CLASS_ID)    

    DIG_CLASS_ID="tok-podcasts__row tok-podcasts__row--audition-time"
    LINK_CLASS_ID="tok-podcasts__row tok-podcasts__row--name"
    TRWANIE_AUDYCJI_CLASS_ID="tok-podcasts__row--time---hour"


    for i,fragment_strony in enumerate(audycje_metadane):
        podcast_data_i_czas=fragment_strony.find('div',class_=DIG_CLASS_ID).find('span').text.strip()
        audycja_opis=fragment_strony.find('div',class_=DIG_CLASS_ID).find('a').text
        audycja_short_link=fragment_strony.find('div',class_=DIG_CLASS_ID).find('a').attrs['href']
        audycja_short_link=audycja_short_link.replace(MAIN_LINK,"")
        audycja_id_link=re.search("([0-9]*)(,)(.*)",audycja_short_link).groups()
        audycja_id=audycja_id_link[0]
        audycja_nazwa=audycja_id_link[2]
        podcast_trwanie=fragment_strony.find('span',class_=TRWANIE_AUDYCJI_CLASS_ID).text.strip()        
        podcast_naglowek=fragment_strony.find('div',class_=LINK_CLASS_ID).find('a').attrs['href']
        podcast_naglowek_rozbity=re.search("(https.*podcast/)([0-9]*)(,)(.*)",podcast_naglowek).groups()
        podcast_id=podcast_naglowek_rozbity[1]
        podcast_nazwa=podcast_naglowek_rozbity[3]        
        data_index=datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        if podcast_nazwa[0]=='-':
            podcast_nazwa=podcast_nazwa[1:]        
        AUDYCJA[podcast_id]=[audycja_id,audycja_nazwa,audycja_opis,\
                              podcast_nazwa,\
                              podcast_data_i_czas,podcast_trwanie,\
                              data_index,\
                                ]        
    sleep (czekaj)
    return AUDYCJA




class _baza():
    database_file=database_file
    sql_create_tokfm_table = """ CREATE TABLE IF NOT EXISTS tokfm (
                                        id_podcast integer PRIMARY KEY,
                                        name_podcast text NOT NULL,
                                        id_audition integer NOT NULL,
                                        name_audition text NOT NULL,                                        
                                        date_podcast date NOT NULL,
                                        during_podcast time NOT NULL,                                        
                                        date_index date NOT NULL,
                                        podcast_heard interger                                        
                                    ); """
    
    conn = None
    cursorObj= None
    DANE_TOK_FM={}

    def __init__(self,DANE_TOK_FM):
        self.DANE_TOK_FM=DANE_TOK_FM
        pass
    
    def create_connection(self):
        database_file=self.database_file
        try:
            conn = sqlite3.connect(self.database_file)
            return conn
        except Error as e:
            print(e)
        return conn

    def create_table(self,conn, create_table_sql):
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)
    def create_cursor(self):
        self.cursorObj = self.conn.cursor()
        return self.cursorObj
    
    def insert_date(self):
        for i in self.DANE_TOK_FM:
            SQL_FALSE=0
            id_podcast_=i
            id_audition_=self.DANE_TOK_FM[i][0]
            name_audition_=self.DANE_TOK_FM[i][1]
            name_podcast_=self.DANE_TOK_FM[i][3]
            date_podcast_=self.DANE_TOK_FM[i][4]
            during_podcast_=self.DANE_TOK_FM[i][5]
            date_index_=self.DANE_TOK_FM[i][6]
            podcast_heard_=SQL_FALSE
            self.cursorObj.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                    date_podcast,during_podcast,date_index,podcast_heard) VALUES(?,?,?,?,?,?,?,?)",\
                    (id_podcast_,name_podcast_,id_audition_,name_audition_,date_podcast_,during_podcast_,date_index_,podcast_heard_))



#------update bazy ze strony-----
#tez poprawic
def update_bazy():
    sciezka=Path(database_file)
    if not sciezka.exists():
        print ("nie ma pliku: "+database_file)
        exit()
        
    
    conn = sqlite3.connect(database_file)    
    cur = conn.cursor()

    for audycja in AUDYCJE_LINK:
        Update=True
        i=1        
        while Update:            
            AUDYCJA=zgraj_strone_audycji(AUDYCJE_LINK[audycja][0],i)                        
            i+=1
            for aud in AUDYCJA:                        
                cur.execute("SELECT id_podcast FROM tokfm where id_podcast = "+aud)
                rows = cur.fetchone()
                if not rows:
                    print ("Update: "+AUDYCJA[aud][1]+" "+AUDYCJA[aud][4]+" "+AUDYCJA[aud][3])                     
                    SQL_FALSE=0                
                    id_podcast_=aud                                
                    id_audition_=AUDYCJA[aud][0]
                    name_audition_=AUDYCJA[aud][1]
                    name_podcast_=AUDYCJA[aud][3]
                    date_podcast_=AUDYCJA[aud][4]
                    during_podcast_=AUDYCJA[aud][5]
                    date_index_=AUDYCJA[aud][6]
                    podcast_heard_=SQL_FALSE
                    #cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,
                    cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                            date_podcast,during_podcast,date_index,podcast_heard) VALUES(?,?,?,?,?,?,?,?)",\
                            (id_podcast_,name_podcast_,id_audition_,name_audition_,date_podcast_,during_podcast_,date_index_,podcast_heard_))
                    conn.commit()                
                else:
                    print ("Not update: "+AUDYCJA[aud][1]+" "+AUDYCJA[aud][4]+" "+AUDYCJA[aud][3])
                    Update=False
                    break
    cur.close()
    conn.close()


#--Zgrywanie ze strony do bazy (full)

#poprawic
#mniej polaczen zrobic, zaktualizować

def zgraj_wszystkie_audycje_do_bazy():
    for audycja in AUDYCJE_LINK:        
    #AUDYCJA={}
    #   ile_stron=AUDYCJE_LINK[audycja][1]
    #   if ile_stron==0:
        ile_stron=int(max_ilosc_stron(AUDYCJE_LINK[audycja][0]))            
        print ("Zgrywam audycje "+str(audycja)+" do: "+database_file)
        for i in range(1,ile_stron+1):
            AUDYCJA=zgraj_strone_audycji (AUDYCJE_LINK[audycja][0],i)        
            baza=_baza(AUDYCJA)
            baza.conn=baza.create_connection()
            if baza.conn is not None:
                baza.create_table(baza.conn,baza.sql_create_tokfm_table)
                baza.cursorObj=baza.create_cursor()
                baza.insert_date()            
                baza.conn.commit()
                baza.cursorObj.close()
                baza.conn.close()
            else:
                    print("Błąd! Nie mogę się połączyć!")






#---przeszukiwanie katalogow na dysku w celu znalezienia plików z audycji
#-Wrzucenie je do slownika?
PODCAST_FILE={}
KATALOG_TOK_FM_PODCASTY_BASE=""
KATALOG_TOK_FM_PODCASTY_ANDROID_FILES=KATALOG_TOK_FM_PODCASTY_BASE+"Android\\data\\fm.tokfm.android\\files\\"
KATALOG_TOK_FM_PODCASTY_RESULT_DIR=KATALOG_TOK_FM_PODCASTY_BASE+"Result\\"

#Dziala pod Linuxem i Windowsem
def szukaj_na_dysku():
    
    p1=Path(KATALOG_TOK_FM_PODCASTY_ANDROID_FILES)
    if not p1.exists():
        print ("Brak katalogu z plikami mp3 z Androida")
        print ("Powinno to tak wygladac: "+str(p1))
        exit()

    p1=Path(KATALOG_TOK_FM_PODCASTY_RESULT_DIR)
        

    if not p1.exists():
        os.mkdir(KATALOG_TOK_FM_PODCASTY_RESULT_DIR)

    for root, dirs, files in os.walk(KATALOG_TOK_FM_PODCASTY_ANDROID_FILES):
        for file in files:
            if file.endswith(".mp3"):
                CALY_PLIK_SCIEZKA=os.path.join(root, file)
                iD_PODSCAST="\\"+CALY_PLIK_SCIEZKA.lstrip(KATALOG_TOK_FM_PODCASTY_ANDROID_FILES)
                #Na unixy linijka
                iD_PODSCAST=iD_PODSCAST.replace("/","\\")
                iD_PODSCAST=iD_PODSCAST.rstrip('mp3')
                iD_PODSCAST=iD_PODSCAST.rstrip('.')
                #trzeba 2 razy obcinac, bo za jednym razem ".mp3" zle kasuje
                iD_PODSCAST=iD_PODSCAST.replace("\\","").lstrip("0")
                iD_PODSCAST=iD_PODSCAST.replace("\\","")
                PODCAST_FILE[iD_PODSCAST]=CALY_PLIK_SCIEZKA



#print(PODCAST_FILE)
#for key,value in PODCAST_FILE.items():
#    print (key,value)

#00\00\09\00\79 - fakt nie mit
#0000090079 90079

#
#----przeszukiwanie w bazie i zgrywanie z inna nazwa do katalogu

#Dziala pod Linuxem i Windowsem
def szukaj_w_bazie_i_zgraj():    
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()

    for i in PODCAST_FILE:
        cur.execute("SELECT id_podcast, name_audition, name_podcast, date_podcast FROM tokfm where id_podcast = "+i)
        rows = cur.fetchone()
        if not rows:
            print("Nie znaleziono audycji: "+i)
        else:
            #KATALOG_PODCAST=rows[1].replace("-"," ")
            KATALOG_PODCAST=AUDYCJE_LINK[rows[1]][1]
            DATA_AUDYCJI=datetime.strptime(rows[3],"%d.%m.%Y %H:%M")
            #ROK=str(DATA_AUDYCJI.year)
            ROK_MIESIAC=DATA_AUDYCJI.strftime("%Y - %m")
            DZIEN=DATA_AUDYCJI.strftime("%d")

            KATALOG=KATALOG_TOK_FM_PODCASTY_RESULT_DIR+KATALOG_PODCAST                
            p1=Path(KATALOG)
            if not p1.exists():
                os.mkdir(p1)            
            KATALOG=KATALOG+"\\"+ROK_MIESIAC
            p1=Path(KATALOG)
            if not p1.exists():
                os.mkdir(p1)
            FILENAME_NO_DASH=rows[2].replace('-', ' ')
            FILENAME=DZIEN+" - "+FILENAME_NO_DASH+".mp3"
                        
            KATALOG_FILENAME=KATALOG+"\\"+FILENAME
            p1=Path(KATALOG_FILENAME)
            if not p1.exists():
                copyfile(PODCAST_FILE[i],p1)
                print ("Skopiowano: "+str(p1))
            else:
                print ("Plik istnieje: "+str(p1))
            #FILENAME_SHORT=rows[2].split("-")[0:6]
            #print (FILENAME_SHORT)
     
    cur.close()
    conn.close()

#-------------------------
#poprawic baze, bez sprawdzania directory
#update bazy sprawdzic
#Jeszcze nazwe katalogu zmienic

def DRUKUJ_NAZWE_PROGRAMU ():
    print (PROGRAM_NAME+" "+PROGRAM_WERSJA+" ("+PROGRAM_DATA+")")

def nazwa_parametru():
    #PARAMETRY=[]
    total = len(sys.argv)
    cmdargs = sys.argv

    if total != 2:                    
        PARAMETRY=""
    else:
        PARAMETRY=cmdargs[1:]    
    return PARAMETRY

#-----Poczatek
DRUKUJ_NAZWE_PROGRAMU()
PARAMETR_NAME=nazwa_parametru()

if not PARAMETR_NAME:
    print ("Proszę podać 1 parametr [update][search]")
else:
    if PARAMETR_NAME[0] =="update":
        update_bazy()
    if PARAMETR_NAME[0] =="search":
        szukaj_na_dysku()
        szukaj_w_bazie_i_zgraj()
    if PARAMETR_NAME[0] =="full":
        zgraj_wszystkie_audycje_do_bazy()        



    
    
    
    
