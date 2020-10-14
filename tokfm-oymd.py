#!/usr/bin/python3
#Zgraj audycje Tok-fm na swoj mp3/mp4 odtwarzacz z urządzenia Android.
#------------------------
#Program dziala na Linuxie i Windowsie
#Autor Szikers
#Licencja typu Freeware albo co tam chcecie ;)

from bs4 import BeautifulSoup
from urllib.request import urlopen
from time import sleep
import re
import os
import sqlite3
from sqlite3 import Error
from random import randrange
from datetime import datetime
from shutil import copyfile,move as movefile
import json
import sys
from pathlib import Path, PureWindowsPath
SQL_FALSE=0
sep=os.sep

#przykladowy link
#page_link='https://audycje.tokfm.pl/audycja/87,Prawda-Nas-Zaboli?offset=8'
#page_link='file:///D:/temp/offczarek.html'
PROGRAM_WERSJA="0.8"
PROGRAM_DATA="15.10.2020"
PROGRAM_NAME="tokfm-on-your-mp3-device"

#database_file=r'D:\temp\tokfm\tokfm.db'

database_file='tokfm.db'
json_file="tok-fm-full.json"
json_file_fav="tok-fm-fav.json"

OFFSET_LINK="?offset="
MAIN_LINK='https://audycje.tokfm.pl/audycja/'


def zaladuj_audycje_json(plik):    
    try:
        with open(plik, 'r') as f:
            AUDYCJE_LINK_=json.load(f)            
    except ValueError as e:                
        print ("Problem z plikiem "+plik+" lub formatem json")
        print (e)        
        exit()
    return AUDYCJE_LINK_
#-dane do linków audycji są w tok-fm.json

AUDYCJE_LINK = zaladuj_audycje_json(json_file)


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
        data_index=datetime.now().strftime("%d-%m-%Y %H:%M:%S") #zmienic kiedys na %Y-%m-%d        
        
        #Czasami w podcastach jest podana tylko godzina
        #Trzeba przekonwertowac to na dzien pobrania audycji                    
        if re.search('^[0-2][0-9]:[0-5][0-9]',podcast_data_i_czas):
            dzis=datetime.now().strftime("%d.%m.%Y")
            TylkoGodzina=podcast_data_i_czas
            podcast_data_i_czas=dzis+" "+TylkoGodzina
        
        
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
def update_bazy():

#Updatuje tylko ulubione audycje
    AUDYCJE_LINK = zaladuj_audycje_json(json_file_fav)
    
    nowe_audycje_licznik=0


    sciezka=Path(database_file)
    if not sciezka.exists():
        print ("Nie ma pliku: "+database_file)
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
                cur.execute("SELECT id_podcast,date_podcast FROM tokfm where id_podcast = "+aud)
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
                    nowe_audycje_licznik+=1
                else:
                    print ("Not update: "+AUDYCJA[aud][1]+" "+AUDYCJA[aud][4]+" "+AUDYCJA[aud][3])
                    #Sprawdzmy czy to powtorka, jezeli tak, cofamy sie dalej                    
                    if AUDYCJA[aud][4]==rows[1]:
                        Update=False
                        break
    cur.close()
    conn.close()
    AUDYCJE_LINK = zaladuj_audycje_json(json_file)
    print ("Nowe audycje:",nowe_audycje_licznik)


#--Zgrywanie ze strony do bazy (full) Robi się tylko 1 audycje raz
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
#KATALOG_TOK_FM_PODCASTY_ANDROID_FILES=KATALOG_TOK_FM_PODCASTY_BASE+"Android\\data\\fm.tokfm.android\\files\\"
KATALOG_TOK_FM_PODCASTY_ANDROID_FILES=KATALOG_TOK_FM_PODCASTY_BASE+"e:\\audycje\\tok fm\\Android\\data\\fm.tokfm.android\\files\\"
#KATALOG_TOK_FM_PODCASTY_RESULT_DIR=KATALOG_TOK_FM_PODCASTY_BASE+"Result\\"
KATALOG_TOK_FM_PODCASTY_RESULT_DIR=KATALOG_TOK_FM_PODCASTY_BASE+"e:\\audycje\\tok fm\\Result\\"
KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE=KATALOG_TOK_FM_PODCASTY_RESULT_DIR+"Przesluchane\\"
KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE=KATALOG_TOK_FM_PODCASTY_RESULT_DIR+"Nieprzesluchane\\"

#Dziala pod Linuxem i Windowsem
def szukaj_na_dysku():
    filenameAndroid = PureWindowsPath(KATALOG_TOK_FM_PODCASTY_ANDROID_FILES)
    p1Android=Path(filenameAndroid)
    if not p1Android.exists():
        print ("Brak zgranego katalogu z plikami mp3 z Androida")
        print ("Powinno to mniej wiecej tak wygladac: "+str(p1Android)+"...00.mp3")
        exit()
    
    filenameResult = PureWindowsPath(KATALOG_TOK_FM_PODCASTY_RESULT_DIR)
    p1Result=Path(filenameResult)
    filenameResult = PureWindowsPath(KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE)
    p2Result=Path(filenameResult)
    filenameResult = PureWindowsPath(KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE)
    p3Result=Path(filenameResult)
        

    if not p1Result.exists():
        p1Result.mkdir()
    if not p2Result.exists():
        p2Result.mkdir()
    if not p3Result.exists():
        p3Result.mkdir()
        
    

#systemowy separator katalogow
    #sep=os.sep
    for root, dirs, files in os.walk(str(p1Android)):
        for file in files:            
            if re.search(r'^[0-9][0-9]\.mp3$', file):
            #if file.endswith(".mp3"):
                CALY_PLIK_SCIEZKA=os.path.join(root, file)                
                iD_PODSCAST=sep+CALY_PLIK_SCIEZKA.lstrip(str(p1Android))
                iD_PODSCAST=iD_PODSCAST.rstrip('mp3')
                iD_PODSCAST=iD_PODSCAST.rstrip('.')                
                #trzeba 2 razy obcinac, bo za jednym razem ".mp3" zle kasuje
                iD_PODSCAST=iD_PODSCAST.replace(sep,"").lstrip("0")                
                iD_PODSCAST=iD_PODSCAST.replace(sep,"")
                PODCAST_FILE[iD_PODSCAST]=CALY_PLIK_SCIEZKA

#----przeszukiwanie w bazie i sprawdzanie czy audycja przesluchana czy nie
#----jezeli jest inaczej niz trzeba to przerzuca sie ja automatycznie

def szukaj_w_bazie_i_katalogu(KATALOG_Z,KATALOG_DO):    

    conn = sqlite3.connect(database_file)
    cur = conn.cursor()

    KAT_PRZESLUCHANE=PureWindowsPath(KATALOG_Z)
    KAT_PRZESLUCHANE_=str(KAT_PRZESLUCHANE)+str(sep)

    KAT_NIEPRZESLUCHANE=PureWindowsPath(KATALOG_DO)
    KAT_NIEPRZESLUCHANE_=str(KAT_NIEPRZESLUCHANE)+str(sep)

    podcast_heard_val=0

    if (KATALOG_Z==KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE):
        podcast_heard_val="0"
    else:
        podcast_heard_val="1"
    
    Ilosc_przenosin=0        
#Porzadek w katalogu "NIE/PRZESLUCHANE" - uwaga zmienia sie zaleznosc
    for root, dirs, files in os.walk(str(KAT_PRZESLUCHANE_)):
        for file in files:                                    
            if re.search(r'^[0-3][0-9] - [0-9A-Za-z ]*.mp3$', file):            
                CALY_PLIK_SCIEZKA=os.path.join(root, file)                
                #lstrip zle dziala!!!
                KAT_P2_=CALY_PLIK_SCIEZKA.replace(KAT_PRZESLUCHANE_,"",1)


                #KAT_P2=re.search("([a-z A-Z0-9.-]*).([0-9 -]*).([0-3][0-9] - *)([0-9a-z A-Z]*)(\.mp3)",KAT_P2_).groups()
                KAT_P2=re.search("([a-z A-Z0-9.-]*).([0-9 -]*).([0-3][0-9] - *)([0-9a-zA-Z ]*)",KAT_P2_).groups()
                
                

                

                KAT_P2_NAME_AUD_DB=""
                for i in AUDYCJE_LINK:
                    if AUDYCJE_LINK[i][1].lower()==KAT_P2[0].strip().lower():
                        KAT_P2_NAME_AUD_DB=i                        
                if not KAT_P2_NAME_AUD_DB:
                    print ("Blad w nazwie katalogu:",r'"'+KAT_P2[0]+r'"')
                    exit ()
                

                KAT_P2_NAME_DATE_DB_=KAT_P2[1]+"-"+KAT_P2[2].rstrip("- ")                                
                KAT_P2_NAME_DATE_DB=datetime.strptime(KAT_P2_NAME_DATE_DB_,"%Y - %m-%d").strftime("%d.%m.%Y")
                KAT_P2_NAME_POD_DB=KAT_P2[3].replace(" ","-")
                ROK_MIESIAC=datetime.strptime(KAT_P2_NAME_DATE_DB,"%d.%m.%Y").strftime("%Y - %m")      
                KAT_NIEPRZESLUCHANE_AUDYCJA=KAT_NIEPRZESLUCHANE_+AUDYCJE_LINK[KAT_P2_NAME_AUD_DB][1]                                                
                KAT_NIEPRZESLUCHANE_AUDYCJA_DATA=KAT_NIEPRZESLUCHANE_AUDYCJA+sep+ROK_MIESIAC                
                KATALOGI_NIEPRZESLUCHANE=[KAT_NIEPRZESLUCHANE_,KAT_NIEPRZESLUCHANE_AUDYCJA,KAT_NIEPRZESLUCHANE_AUDYCJA_DATA]
                
                if KAT_P2_NAME_AUD_DB:                                    
                    cur.execute("SELECT name_audition, date_podcast, name_podcast FROM tokfm WHERE name_audition LIKE "
                    +"'%"+KAT_P2_NAME_AUD_DB+"%'"\
                    +" AND date_podcast LIKE "+"'%"+KAT_P2_NAME_DATE_DB+"%'"\
                    +" AND name_podcast LIKE "+"'%"+KAT_P2_NAME_POD_DB+"%'"\
                    +" AND podcast_heard = "+podcast_heard_val\
                    )                
                rows = cur.fetchone()
                if rows:                    
                    for katalog in KATALOGI_NIEPRZESLUCHANE:
                        filenameResult = PureWindowsPath(katalog)                        
                        if not Path(filenameResult).exists():                      
                            Path(filenameResult).mkdir()                    
                    movefile (CALY_PLIK_SCIEZKA,KAT_NIEPRZESLUCHANE_AUDYCJA_DATA)
                    print ("Przenioslem \""+file+"\" do "+KAT_NIEPRZESLUCHANE_AUDYCJA_DATA+sep)
                    Ilosc_przenosin+=1
                
                    

                
    cur.close()
    conn.close()
    print ("Ilosc przenosin:",Ilosc_przenosin)
    

#----przeszukiwanie w bazie i zgrywanie z inna nazwa do katalogu


#Przeszukiwanie dziala pod Linuxem i Windowsem
def SZUKAJ (PARAMETRY):
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    #+aud
    #PARAMETRY="+aud off +data   2020    "
    #Usun biale znaki
    
    #PAR=re.sub("\s+"," ",PARAMETRY)
    AUD=""; DATA=""

    if re.search("\+aud",PARAMETRY):
        AUD=re.search("(\+aud) (\S*)",PARAMETRY).groups()[1]

    if re.search("\+data",PARAMETRY):
        DATA=re.search("(\+data) (\S*)",PARAMETRY).groups()[1]
    
    if not AUD and not DATA:
        print ("Parametry to +aud (audycja) lub/i +data (data)")
        return
        



    cur.execute("SELECT date_podcast, name_audition,  name_podcast FROM tokfm WHERE name_audition LIKE "
    +"'%"+AUD+"%'"\
    +" AND date_podcast LIKE "+"'%"+DATA+"%'"\
    +" LIMIT 9"\
    )                
    #rows = cur.fetchone()
    rows = cur.fetchall()
    if rows:
        for j,i in enumerate(rows,1):
            print (str(j)+".",i[0],"|",AUDYCJE_LINK [i[1]][1],"|",str(i[2]).replace("-"," "))


    cur.close()
    conn.close()


def szukaj_w_bazie_i_zgraj():
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()

    for i in PODCAST_FILE:
        cur.execute("SELECT id_podcast, name_audition, name_podcast, date_podcast, podcast_heard FROM tokfm where id_podcast = "+i)
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
            
            SQL_FALSE=0
            if rows[4]==SQL_FALSE:
                KAT=KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE
                KAT_OPOZYCYJNY=KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE
            else:
                KAT=KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE
                KAT_OPOZYCYJNY=KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE

            KATALOG=KAT+KATALOG_PODCAST
            KATALOG_OPOZYCYJNY=KAT_OPOZYCYJNY+KATALOG_PODCAST
            filename = PureWindowsPath(KATALOG)
            #filename_OPOZYCYJNY=PureWindowsPath(KATALOG_OPOZYCYJNY)

            #print (filename)
            p1=Path(filename)

            if not p1.exists():
                p1.mkdir()
                #os.mkdir(p1)            


            KATALOG=KATALOG+"\\"+ROK_MIESIAC
            KATALOG_OPOZYCYJNY=KATALOG_OPOZYCYJNY+"\\"+ROK_MIESIAC
            
            filename = PureWindowsPath(KATALOG)
            filename_OPOZYCYJNY = PureWindowsPath(KATALOG_OPOZYCYJNY)

            p1=Path(filename)

            if not p1.exists():
                p1.mkdir()
                #os.mkdir(p1)
            FILENAME_NO_DASH=rows[2].replace('-', ' ')
            FILENAME=DZIEN+" - "+FILENAME_NO_DASH+".mp3"
                        
            KATALOG_FILENAME=KATALOG+"\\"+FILENAME
            KATALOG_FILENAME_OPOZYCYJNY=KATALOG_OPOZYCYJNY+"\\"+FILENAME
            filename=PureWindowsPath(KATALOG_FILENAME)
            p1=Path(filename)
            if not p1.exists():                
                copyfile(PODCAST_FILE[i],str(p1))
                print ("Skopiowano: "+str(p1))
            else:
                print ("Plik istnieje: "+str(p1))
            #Kasujemy pozostalosci jezeli byl dawnym katalogu
            filename=PureWindowsPath(KATALOG_FILENAME_OPOZYCYJNY)
            p1=Path(filename)
            if p1.exists():
                p1.unlink()
                print ("Skasowalem: "+str(p1))


            #FILENAME_SHORT=rows[2].split("-")[0:6]
            #print (FILENAME_SHORT)
     
    cur.close()
    conn.close()

#-------------------------

def DRUKUJ_NAZWE_PROGRAMU ():
    print (PROGRAM_NAME+" "+PROGRAM_WERSJA+" ("+PROGRAM_DATA+")")

def WYSWIETL_POMOC ():
    print ("Proszę podać parametr \n")
    print ("update - Aktualizuje baze podcastów")
    print (r'copy - Przeszukuje "surowe" podcasty na dysku i je odpowiednio kopiuje')
    print ("fix - Przenosi audycje wg bazy do przesluchane lub nie")
    print ("search - Szuka podcastów")
    print ("help - Wyswietla te pomoc")



def nazwa_parametru():
    #PARAMETRY=[]
    total = len(sys.argv)
    cmdargs = sys.argv

    if total < 2:                    
        PARAMETRY=""
    else:
        PARAMETRY=cmdargs[1:]    
    return PARAMETRY

#-----Poczatek programu----
DRUKUJ_NAZWE_PROGRAMU()
PARAMETR_NAME=nazwa_parametru()

if not PARAMETR_NAME:
    WYSWIETL_POMOC()
else:
    if PARAMETR_NAME[0] =="update":
        update_bazy()
    if PARAMETR_NAME[0] =="copy":
        szukaj_na_dysku()
        szukaj_w_bazie_i_zgraj()
    if PARAMETR_NAME[0] =="search":
        SZUKAJ(" ".join(PARAMETR_NAME))        
        
    if PARAMETR_NAME[0] =="help":
        WYSWIETL_POMOC()
    if PARAMETR_NAME[0] =="fix":
        print ("Sprawdzam w podkasty: Przesluchane")
        szukaj_w_bazie_i_katalogu(KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE,KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE)
        print ("Sprawdzam w podkasty: NiePrzesluchane")
        szukaj_w_bazie_i_katalogu(KATALOG_TOK_FM_PODCASTY_RESULT_DIR_NIEPRZESLUCHANE,KATALOG_TOK_FM_PODCASTY_RESULT_DIR_PRZESLUCHANE)

#Parametr dla doswiadczonych, zgrywa wszystkie podcasty z audycji
#podane w pliku tok-fm.json, lub tok-fm.jsonbak
    if PARAMETR_NAME[0] =="full":
        zgraj_wszystkie_audycje_do_bazy()        

#---tu kod pomocniczy
#szukaj_na_dysku()
#print (PODCAST_FILE)
#SZUKAJ("+aud off  +aud aa    +data   2020    ")



    
    
    
    
