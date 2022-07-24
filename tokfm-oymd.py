#!/usr/bin/python3
#Zgraj audycje Tok-fm na swoj mp3/mp4 odtwarzacz z urządzenia Android.
#TAK SIĘ NIE PISZE PROGRAMÓW, do przerobienia!
#------------------------
#Program dziala na Linuxie (na Windowsie poprawic)
#Autor Szikers, 
#do poprawy wszystko z katalogami (pod win moze nie dzialac)
#do poprawy update, ulubione i 
#przerobić na klasy
#

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
from pathlib import Path, PureWindowsPath, PurePosixPath
sql_false=0

#system separator
SEP=os.sep


#przykladowy link
#page_link='https://audycje.tokfm.pl/audycja/87,Prawda-Nas-Zaboli?offset=8'
#page_link='file:///D:/temp/offczarek.html'
PROGRAM_WERSJA="0.12"
PROGRAM_DATA="10.06.2021"
PROGRAM_NAME="tokfm-on-your-mp3-device"


DATABASE_FILE="tokfm.db"
JSON_FILE_FULL="tok-fm-full.json"

JSON_FILE_FAV="tok-fm-fav.json"

OFFSET_LINK="?offset="
MAIN_LINK='https://audycje.tokfm.pl/audycja/'


def zaladuj_audycje_json(PLIK):    
    try:
        with open(PLIK, 'r') as f:
            audycje_link_=json.load(f)            
    except ValueError as e:                
        print ("Problem z plikiem "+PLIK+" lub formatem json")
        print (e)        
        exit()
    return audycje_link_
#-dane do linków audycji są w tok-fm.json

#poprawic to,audycje_link dac  do klasy
audycje_link = zaladuj_audycje_json(JSON_FILE_FULL)


# def max_ilosc_stron(audycja_ident):
#     nr_site=randrange(1321343,93213431)
    
#     page_link = MAIN_LINK+audycja_ident+OFFSET_LINK+str(nr_site)
#     body = urlopen(page_link)
#     soup = BeautifulSoup(body,'html.parser')
#     naglowek = soup.find('head')
#     max_strona = naglowek.find('link', rel="canonical").attrs['href']
    

#     if re.search(r'=[0-9]*$', max_strona) is None:
#         max_strona=1
#     else:
#         max_strona = max_strona.split("=")[-1]
                                     
#     page_link=MAIN_LINK+audycja_ident+OFFSET_LINK+str(max_strona)
#     print ("Maxymalny odnosnik to: "+page_link)    
#     return max_strona    

def czy_button_next_jest_osiagalny(audycja_ident, nr_strony):
    
    page_link = MAIN_LINK+audycja_ident+OFFSET_LINK+str(nr_strony)

    body = urlopen(page_link)
    soup = BeautifulSoup(body,'html.parser')
    pagination=soup.find('div',class_="tok-pagination")
        
    if pagination.find("a", {"class": "tok-pagination__button-next"}) is not None:        
        return True
    else:
        return False


def zgraj_strone_audycji (audycja_ident,nr_site):    
    audycje_wiersze={}
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


    for fragment_strony in audycje_metadane:
        podcast_data_i_czas=fragment_strony.find('div',class_=DIG_CLASS_ID).find('span').text.strip()
        w_studio=fragment_strony.find('span',class_=TRWANIE_AUDYCJI_CLASS_ID).findNext('span').findAll('a')
        w_studio=fragment_strony.find('span',class_=TRWANIE_AUDYCJI_CLASS_ID).findNext('span')
        if w_studio.find('a'):
            w_studio=w_studio.findAll('a')
        else:
            w_studio=w_studio.findNext('span').findAll('a')
        podcast_gosc=""
        if w_studio:        
            for j,gosc_baza in enumerate(w_studio):
                if j>0:
                    podcast_gosc=podcast_gosc+', '
                podcast_gosc=podcast_gosc+gosc_baza.text.replace(',','').replace('\t','').replace('\n',' ').strip()                     
        else:
            podcast_gosc="Brak"
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
        audycje_wiersze[podcast_id]=[audycja_id,audycja_nazwa,audycja_opis,\
                              podcast_nazwa,\
                              podcast_data_i_czas,podcast_trwanie,\
                              data_index,podcast_gosc,\
                                ]        
    sleep (czekaj)
    return audycje_wiersze


class _baza():
    DATABASE_FILE=DATABASE_FILE
    sql_create_tokfm_table = """ CREATE TABLE IF NOT EXISTS tokfm (
                                        id_podcast integer PRIMARY KEY,
                                        name_podcast text NOT NULL,
                                        id_audition integer NOT NULL,
                                        name_audition text NOT NULL,                                                                                
                                        date_podcast date NOT NULL,
                                        during_podcast time NOT NULL,                                        
                                        date_index date NOT NULL,
                                        podcast_heard interger,
                                        guest_podcast text NOT NULL                                        
                                    ); """
    
    conn = None
    cursorObj= None
    dane_tok_fm={}

    def __init__(self,dane_tok_fm):
        self.dane_tok_fm=dane_tok_fm
        pass
    
    def create_connection(self):
        DATABASE_FILE=self.DATABASE_FILE
        try:
            conn = sqlite3.connect(self.DATABASE_FILE)
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
        for i in self.dane_tok_fm:            
            id_podcast_=i
            id_audition_=self.dane_tok_fm[i][0]
            name_audition_=self.dane_tok_fm[i][1]
            name_podcast_=self.dane_tok_fm[i][3]
            date_podcast_=self.dane_tok_fm[i][4]
            during_podcast_=self.dane_tok_fm[i][5]
            date_index_=self.dane_tok_fm[i][6]
            podcast_heard_=sql_false
            guest_podcast_=self.dane_tok_fm[i][7]
            self.cursorObj.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                    date_podcast,during_podcast,date_index,podcast_heard,guest_podcast) VALUES(?,?,?,?,?,?,?,?,?)",\
                    (id_podcast_,name_podcast_,id_audition_,name_audition_,date_podcast_,during_podcast_,date_index_,podcast_heard_,guest_podcast_))


#------update bazy ze strony-----
def update_bazy(update_file):

    if (update_file=="full"):
        update_file_=JSON_FILE_FULL

    if (update_file=="lite"):
        update_file_=JSON_FILE_FAV  
        
    audycje_link = zaladuj_audycje_json(update_file_)
    
    nowe_audycje_licznik=0


    sciezka=Path(DATABASE_FILE)
    if not sciezka.exists():
        print ("Nie ma pliku: "+DATABASE_FILE)
        exit()
        
    
    conn = sqlite3.connect(DATABASE_FILE)    
    cur = conn.cursor()

    for audycja in audycje_link:
        Update=True
        i=1        
        while Update:            
            audycje_wiersze=zgraj_strone_audycji(audycje_link[audycja][0],i)                        
            i+=1
            for aud in audycje_wiersze:                        
                cur.execute("SELECT id_podcast,date_podcast FROM tokfm where id_podcast = "+aud)
                rows = cur.fetchone()
                if not rows:
                    print ("Update: "+audycje_wiersze[aud][1]+" "+audycje_wiersze[aud][4]+" "+audycje_wiersze[aud][3])                     
                    sql_false=0                
                    id_podcast_=aud                                
                    id_audition_=audycje_wiersze[aud][0]
                    name_audition_=audycje_wiersze[aud][1]
                    name_podcast_=audycje_wiersze[aud][3]
                    date_podcast_=audycje_wiersze[aud][4]
                    during_podcast_=audycje_wiersze[aud][5]
                    date_index_=audycje_wiersze[aud][6]
                    podcast_heard_=sql_false
                    guest_podcast_=audycje_wiersze[aud][7]
                    #cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,
                    cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                            date_podcast,during_podcast,date_index,podcast_heard,guest_podcast) VALUES(?,?,?,?,?,?,?,?,?)",\
                            (id_podcast_,name_podcast_,id_audition_,name_audition_,date_podcast_,during_podcast_,date_index_,podcast_heard_,guest_podcast_))
                    conn.commit()                
                    nowe_audycje_licznik+=1
                else:
                    print ("Not update: "+audycje_wiersze[aud][1]+" "+audycje_wiersze[aud][4]+" "+audycje_wiersze[aud][3])
                    #Sprawdzmy czy to powtorka, jezeli tak, cofamy sie dalej                    
                    if audycje_wiersze[aud][4]==rows[1]:
                        Update=False
                        break
    cur.close()
    conn.close()
#idioctwo, dac do klasy    
    audycje_link = zaladuj_audycje_json(JSON_FILE_FULL)
    print ("Nowe audycje:",nowe_audycje_licznik)


#--Zgrywanie ze strony do bazy (full) Robi się tylko 1 audycje raz
#mniej polaczen zrobic, zaktualizować


def zgraj_audycje_do_bazy(audycje):
    for audycja in audycje:        


    #AUDYCJA={}
    #   ile_stron=audycje_link[audycja][1]
    #   if ile_stron==0:
        #ile_stron=int(max_ilosc_stron(audycje_link[audycja][0]))        
        print ("Zgrywam audycje "+str(audycja)+" do: "+DATABASE_FILE)
        i=1
                
        while czy_button_next_jest_osiagalny(audycje_link[audycja][0],i):                            
            audycje_wiersze=zgraj_strone_audycji (audycje_link[audycja][0],i)                    
            i+=1
            baza=_baza(audycje_wiersze)
            baza.conn=baza.create_connection()
            #do poprawki!!
            if baza.conn is not None:
                baza.create_table(baza.conn,baza.sql_create_tokfm_table)
                baza.cursorObj=baza.create_cursor()
                baza.insert_date()            
                baza.conn.commit()
                baza.cursorObj.close()
                baza.conn.close()
            else:
                    print("Błąd! Nie mogę się połączyć!")
#--zgrywam stronę gdzie jest button next--- do poprawki
        audycje_wiersze=zgraj_strone_audycji (audycje_link[audycja][0],i)        
        baza=_baza(audycje_wiersze)
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
            
#         audycje_wiersze=zgraj_strone_audycji (audycje_link[audycja][0],i)        



#---przeszukiwanie katalogow na dysku w celu znalezienia plików z audycji
#-Wrzucenie je do slownika?
podcast_file={}
katalog_tok_fm_podcasty_base=""
#katalog_tok_fm_podcasty_android_files=katalog_tok_fm_podcasty_base+"e:\\audycje\\tok fm\\Android\\data\\fm.tokfm.android\\files\\"
katalog_tok_fm_podcasty_android_files=katalog_tok_fm_podcasty_base+"/mnt/e/audycje/tok fm/Android/data/fm.tokfm.android/files"+SEP
katalog_tok_fm_podcasty_result_dir=katalog_tok_fm_podcasty_base+"/mnt/e/audycje/tok fm/Result"+SEP
katalog_tok_fm_podcasty_result_dir_przesluchane=katalog_tok_fm_podcasty_result_dir+SEP+"Przesluchane"+SEP
katalog_tok_fm_podcasty_result_dir_nieprzesluchane=katalog_tok_fm_podcasty_result_dir+SEP+"Nieprzesluchane"+SEP


#Dziala pod Linuxem i Windowsem (do poprawy windows)
def szukaj_na_dysku():


    filenameAndroid = PurePosixPath(katalog_tok_fm_podcasty_android_files)
    if sys.platform == "win32":
        p1Android=Path(PureWindowsPath(filenameAndroid))
        p1Result=Path(PureWindowsPath(katalog_tok_fm_podcasty_result_dir))        
        p2Result=Path(PureWindowsPath(katalog_tok_fm_podcasty_result_dir_przesluchane))        
        p3Result=Path(PureWindowsPath(katalog_tok_fm_podcasty_result_dir_nieprzesluchane))
    elif sys.platform == "linux":    
        p1Android=Path(PurePosixPath(filenameAndroid))
        p1Result=Path(PurePosixPath(katalog_tok_fm_podcasty_result_dir))        
        p2Result=Path(PurePosixPath(katalog_tok_fm_podcasty_result_dir_przesluchane))        
        p3Result=Path(PurePosixPath(katalog_tok_fm_podcasty_result_dir_nieprzesluchane))
    else:
        print ("Niewspierany system")
        exit ()
    

    if not p1Android.exists():
        print ("Brak zgranego katalogu z plikami mp3 z Androida")
        print ("Powinno to mniej wiecej tak wygladac: "+str(p1Android)+"...00.mp3")
        exit()
            
    if not p1Result.exists():
        p1Result.mkdir()
    if not p2Result.exists():
        p2Result.mkdir()
    if not p3Result.exists():
        p3Result.mkdir()
            
#systemowy separator katalogow
    
    for root, dirs, files in os.walk(str(p1Android)):
        for file in files:            
            if re.search(r'^[0-9][0-9]\.mp3$', file):
            #if file.endswith(".mp3"):
                caly_plik_sciezka=os.path.join(root, file)                
                id_podcast=SEP+caly_plik_sciezka.lstrip(str(p1Android))
                id_podcast=id_podcast.rstrip('mp3')
                id_podcast=id_podcast.rstrip('.')                
                #trzeba 2 razy obcinac, bo za jednym razem ".mp3" zle kasuje
                id_podcast=id_podcast.replace(SEP,"").lstrip("0")                
                id_podcast=id_podcast.replace(SEP,"")
                podcast_file[id_podcast]=caly_plik_sciezka



#----przeszukiwanie w bazie i sprawdzanie czy audycja jest przesluchana czy nie
#----jezeli jest inaczej niz trzeba to przerzuca sie ja automatycznie

def szukaj_w_bazie_i_katalogu(katalog_z,katalog_do):    

#-do poprawki
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()

    kat_przesluchane=PurePosixPath(katalog_z)
    kat_przesluchane_=str(kat_przesluchane)+str(SEP)

    kat_nieprzesluchane=PurePosixPath(katalog_do)
    kat_nieprzesluchane_=str(kat_nieprzesluchane)+str(SEP)

    podcast_heard_val=0

    if (katalog_z==katalog_tok_fm_podcasty_result_dir_przesluchane):
        podcast_heard_val="0"
    else:
        podcast_heard_val="1"
    
    Ilosc_przenosin=0        
#Porzadek w katalogu "NIE/PRZESLUCHANE" - uwaga zmienia sie zaleznosc
    for root, dirs, files in os.walk(str(kat_przesluchane_)):
        for file in files:                                    
            if re.search(r'^[0-3][0-9] - [0-9A-Za-z ]*.mp3$', file):            
                caly_plik_sciezka=os.path.join(root, file)                
                #lstrip zle dziala!!!
                kat_p2_=caly_plik_sciezka.replace(kat_przesluchane_,"",1)

                #kat_p2=re.search("([a-z A-Z0-9.-]*).([0-9 -]*).([0-3][0-9] - *)([0-9a-z A-Z]*)(\.mp3)",kat_p2_).groups()
                kat_p2=re.search("([a-z A-Z0-9.-]*).([0-9 -]*).([0-3][0-9] - *)([0-9a-zA-Z ]*)",kat_p2_).groups()
                
                kat_p2_name_aud_db=""
                for i in audycje_link:
                    if audycje_link[i][1].lower()==kat_p2[0].strip().lower():
                        kat_p2_name_aud_db=i                        
                if not kat_p2_name_aud_db:
                    print ("Blad w nazwie katalogu:",r'"'+kat_p2[0]+r'"')
                    exit ()
                

                kat_p2_name_date_db=kat_p2[1]+"-"+kat_p2[2].rstrip("- ")                                
                kat_p2_NAME_DATE_DB=datetime.strptime(kat_p2_name_date_db,"%Y - %m-%d").strftime("%d.%m.%Y")
                kat_p2_NAME_POD_DB=kat_p2[3].replace(" ","-")
                rok_miesiac=datetime.strptime(kat_p2_NAME_DATE_DB,"%d.%m.%Y").strftime("%Y - %m")      
                kat_nieprzesluchane_audycja=kat_nieprzesluchane_+audycje_link[kat_p2_name_aud_db][1]                                                
                kat_nieprzesluchane_audycja_data=kat_nieprzesluchane_audycja+SEP+rok_miesiac                
                katalogi_nieprzesluchane=[kat_nieprzesluchane_,kat_nieprzesluchane_audycja,kat_nieprzesluchane_audycja_data]
                
                if kat_p2_name_aud_db:                                    
                    cur.execute("SELECT name_audition, date_podcast, name_podcast FROM tokfm WHERE name_audition LIKE "
                    +"'%"+kat_p2_name_aud_db+"%'"\
                    +" AND date_podcast LIKE "+"'%"+kat_p2_NAME_DATE_DB+"%'"\
                    +" AND name_podcast LIKE "+"'%"+kat_p2_NAME_POD_DB+"%'"\
                    +" AND podcast_heard = "+podcast_heard_val\
                    )                
                rows = cur.fetchone()
                if rows:                    
                    for katalog in katalogi_nieprzesluchane:
                        filenameResult = PurePosixPath(katalog)                        
                        if not Path(filenameResult).exists():                      
                            Path(filenameResult).mkdir()                    
                    movefile (caly_plik_sciezka,kat_nieprzesluchane_audycja_data)
                    print ("Przenioslem \""+file+"\" do "+kat_nieprzesluchane_audycja_data+SEP)
                    Ilosc_przenosin+=1
                                                
    cur.close()
    conn.close()
    print ("Ilosc przenosin:",Ilosc_przenosin)
    

#----przeszukiwanie w bazie i zgrywanie z inna nazwa do katalogu


#Przeszukiwanie dziala pod Linuxem i Windowsem (Poprawic windows)
def szukaj_i_wyswietl (parametry):
    
    #+aud
    #parametry="+aud off +date   2020    "
    #Usun biale znaki    
    #PAR=re.sub("\s+"," ",parametry)
    PARAM_NAME={'AUD':"",'DATE':"",'GUEST':""}
    no_par=True
    

    if re.search("\+aud",parametry):        
        PARAM_NAME['AUD']=re.search("(\+aud) (\S*)",parametry).groups()[1]
        no_par=False

    if re.search("\+date",parametry):
        PARAM_NAME['DATE']=re.search("(\+date) (\S*)",parametry).groups()[1]
        no_par=False
    
    if re.search("\+guest",parametry):
        PARAM_NAME['GUEST']=re.search("(\+guest) (\S*)",parametry).groups()[1]
        no_par=False
    

    if not no_par:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute("SELECT date_podcast, name_audition,  name_podcast, guest_podcast FROM tokfm WHERE name_audition LIKE "
        +"'%"+PARAM_NAME['AUD']+"%'"\
        +" AND date_podcast LIKE "+"'%"+PARAM_NAME['DATE']+"%'"\
        +" AND guest_podcast LIKE "+"'%"+PARAM_NAME['GUEST']+"%'"\
        +" LIMIT 9"\
        )                
        #rows = cur.fetchone()
        rows = cur.fetchall()
        if rows:        
            for j,i in enumerate(rows,1):
                print (str(j)+".",i[0],"|",audycje_link [i[1]][1],"|",str(i[2]).replace("-"," "),"|",i[3])


        cur.close()
        conn.close()
    else:
        print ("parametry to +aud (audycja) lub/i +date (data)")        



def szukaj_w_bazie_i_zgraj():
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    licznik_skopiowane=0
    licznik_skasowane=0

    for i in podcast_file:
        cur.execute("SELECT id_podcast, name_audition, name_podcast, date_podcast, podcast_heard FROM tokfm where id_podcast = "+i)
        rows = cur.fetchone()
        if not rows:
            print("Nie znaleziono audycji: "+i)
        else:
            #katalog_podcast=rows[1].replace("-"," ")
            katalog_podcast=audycje_link[rows[1]][1]
            data_audycji=datetime.strptime(rows[3],"%d.%m.%Y %H:%M")
            #ROK=str(data_audycji.year)
            rok_miesiac=data_audycji.strftime("%Y - %m")
            dzien=data_audycji.strftime("%d")
            
            sql_false=0
            if rows[4]==sql_false:
                kat=katalog_tok_fm_podcasty_result_dir_nieprzesluchane
                kat_opozycyjny=katalog_tok_fm_podcasty_result_dir_przesluchane
            else:
                kat=katalog_tok_fm_podcasty_result_dir_przesluchane
                kat_opozycyjny=katalog_tok_fm_podcasty_result_dir_nieprzesluchane

            katalog=kat+katalog_podcast
            katalog_opozycyjny=kat_opozycyjny+katalog_podcast
            filename = PurePosixPath(katalog)
            #filename_OPOZYCYJNY=PureWindowsPath(katalog_opozycyjny)

            #print (filename)
            p1=Path(filename)

            if not p1.exists():
                p1.mkdir()
                #os.mkdir(p1)            


            katalog=katalog+SEP+rok_miesiac
            katalog_opozycyjny=katalog_opozycyjny+SEP+rok_miesiac
            
            filename = PurePosixPath(katalog)
            #filename_opozycyjny = PureWindowsPath(katalog_opozycyjny)

            p1=Path(filename)

            if not p1.exists():
                p1.mkdir()
                #os.mkdir(p1)
            filename_no_dash=rows[2].replace('-', ' ')
            filename=dzien+" - "+filename_no_dash+".mp3"
                        
            katalog_filename=katalog+SEP+filename
            katalog_filename_opozycyjny=katalog_opozycyjny+SEP+filename
            filename=PurePosixPath(katalog_filename)
            p1=Path(filename)
            if not p1.exists():                
                copyfile(podcast_file[i],str(p1))
                print ("Skopiowano: "+str(p1))
                licznik_skopiowane+=1
            else:
                print ("Plik istnieje: "+str(p1))
            #Kasujemy pozostalosci jezeli byl w dawnym katalogu
            filename=PurePosixPath(katalog_filename_opozycyjny)
            p1=Path(filename)
            if p1.exists():
                p1.unlink()
                print ("Skasowalem: "+str(p1))
                licznik_skasowane+=1
     
    cur.close()
    conn.close()
    print ("Skopiowano:",licznik_skopiowane)
    print ("Skasowano:",licznik_skasowane)


#-------------------------

def drukuj_nazwe_programu ():
    print (PROGRAM_NAME+" "+PROGRAM_WERSJA+" ("+PROGRAM_DATA+")")

def wyswietl_pomoc ():
    print ("Proszę podać parametr \n")
    print ("update [full/lite] - Aktualizuje baze podcastów ze strony")
    print ('fix_names - Kopiuje ściągniete mp3 ze smartfona, zmienia na nazwy podcastów i je kopiuje do katalogów')
    print ("search_podcast - Szuka podcasty")    
    print ("move_heard - Sprawdza czy audycje były przesłuchane i je przenosi")
    print ("fix_podcast [nazwa] - Ściąga wszystkie podcasty do podanej kolumny name_audition")    
    print ("help - Wyswietla tą pomoc")



def nazwa_parametru():
    #parametry=[]
    total = len(sys.argv)
    cmdargs = sys.argv

    if total < 2:                    
        parametry=""
    else:
        parametry=cmdargs[1:]    
    return parametry

#-----Poczatek programu----
drukuj_nazwe_programu()
parametr_name=nazwa_parametru()



if not parametr_name:
    wyswietl_pomoc()
else:
    if parametr_name[0] =="update":
        if len(parametr_name)>1:
            if parametr_name[1] =="full":
                update_bazy("full")
            elif parametr_name[1] =="lite":
                update_bazy("lite")
            else:
                print ("Wybierz: full lub lite")
                exit()
        else:
                print ("Wybierz: full lub lite")
                exit()


    if parametr_name[0] =="fix_names":
        
        szukaj_na_dysku()        
        szukaj_w_bazie_i_zgraj()

    if parametr_name[0] =="search_podcast":
        szukaj_i_wyswietl(" ".join(parametr_name))        
            
    if parametr_name[0] =="move_heard":
        print ("Sprawdzam w podkastach: Przesluchane")
        szukaj_w_bazie_i_katalogu(katalog_tok_fm_podcasty_result_dir_przesluchane,katalog_tok_fm_podcasty_result_dir_nieprzesluchane)
        print ("Sprawdzam w podkastach: NiePrzesluchane")
        szukaj_w_bazie_i_katalogu(katalog_tok_fm_podcasty_result_dir_nieprzesluchane,katalog_tok_fm_podcasty_result_dir_przesluchane)

    if parametr_name[0] =="fix_podcast":
        if len(parametr_name)>1:
            if parametr_name[1] not in audycje_link:
                print ("Nie mam w bazie audycji",parametr_name[1],"Proszę podać nazwę audycji z dostepnych poniżej:")
                for i in audycje_link:
                    print (i)
            else:
                audycje_link_tmp={parametr_name[1]:audycje_link[parametr_name[1]]}
                zgraj_audycje_do_bazy(audycje_link_tmp)        
                #audycje_link
        else:
            print ("Proszę podać nazwę audycji z dostepnych poniżej:")
            for i in audycje_link:
                print (i)
    
    if parametr_name[0] =="help":
        wyswietl_pomoc()
                

#Parametr dla doswiadczonych, zgrywa wszystkie podcasty z audycji
#podane w pliku tok-fm.json, lub tok-fm.jsonbak
#    if parametr_name[0] =="full":
#        zgraj_audycje_do_bazy(audycje_link)        

#---tu kod pomocniczy
#szukaj_na_dysku()
#print (podcast_file)
#szukaj("+aud off  +aud aa    +data   2020    ")



    
    
    
    
