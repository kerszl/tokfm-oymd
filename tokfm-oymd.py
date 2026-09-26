#!/usr/bin/python3
#Zgraj audycje Tok-fm na swoj mp3/mp4 odtwarzacz z urządzenia Android.
#TAK SIĘ NIE PISZE PROGRAMÓW, do przerobienia!
#------------------------
#Program dziala na Linuxie (na Windowsie poprawic)
#Autor Szikers, 
#do poprawy wszystko z katalogami (pod win moze nie dzialac)
#do poprawy update, ulubione i 
#przerobić na klasy

#2024.07.12 - Nie dziala, duzo trzeba przerobić 
#2026.03.25 - (claude gemini poprawił)

from bs4 import BeautifulSoup
from urllib.request import urlopen, Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from time import sleep
import re
import os
import sqlite3
from sqlite3 import Error
from random import randrange
from datetime import datetime, timedelta
from shutil import copyfile,move as movefile
import json
import sys
import html
from pathlib import Path
sql_false=0

class PreserveQueryRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old_parsed = urlparse(req.full_url)
        new_parsed = urlparse(newurl)
        if old_parsed.query and not new_parsed.query:
            new_url_with_query = urlunparse((
                new_parsed.scheme,
                new_parsed.netloc,
                new_parsed.path,
                new_parsed.params,
                old_parsed.query,
                new_parsed.fragment
            ))
            return Request(new_url_with_query, headers=req.headers)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

custom_opener = build_opener(PreserveQueryRedirectHandler)

#system separator
SEP=os.sep


#przykladowy link
#page_link='https://audycje.tokfm.pl/audycja/87,Prawda-Nas-Zaboli?offset=8'
#page_link='file:///D:/temp/offczarek.html'
PROGRAM_WERSJA="0.27"
PROGRAM_DATA="26.09.2026"
PROGRAM_NAME="tokfm-on-your-mp3-device"

# Ścieżka bazowa do pamięci telefonu zamontowanej w WSL
SCIEZKA_TELEFONU_BASE = "/mnt/s23/Pamięć wewnętrzna/Android/data/fm.tokfm.android/"


DATABASE_FILE="tokfm.db"
JSON_FILE_FAVORITE="tok-fm-favorite.json"
JSON_FILE_ALL="tok-fm-full.json"

OFFSET_LINK="?offset="
MAIN_LINK='https://audycje.tokfm.pl/audycja/'

def znormalizuj_date(data_str):
    if not data_str:
        return datetime.now().strftime("%d.%m.%Y %H:%M")
    
    data_str_lower = data_str.lower()
    teraz = datetime.now()
    
    if "dziś" in data_str_lower or "dzis" in data_str_lower:
        godzina = re.search(r"(\d{2}:\d{2})", data_str)
        return teraz.strftime("%d.%m.%Y") + (f" {godzina.group(1)}" if godzina else " 12:00")
    elif "wczoraj" in data_str_lower:
        wczoraj = teraz - timedelta(days=1)
        godzina = re.search(r"(\d{2}:\d{2})", data_str)
        return wczoraj.strftime("%d.%m.%Y") + (f" {godzina.group(1)}" if godzina else " 12:00")
    
    return data_str.strip()


def log_info(msg):
    print(f"\033[1;34m[*]\033[0m {msg}")

def log_success(msg):
    print(f"\033[1;32m[+]\033[0m {msg}")

def log_error(msg):
    print(f"\033[1;31m[-]\033[0m {msg}")




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
audycje_link = zaladuj_audycje_json(JSON_FILE_FAVORITE)


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

def pobierz_soup_strony(audycja_ident, nr_site, max_retries=3):
    page_link = MAIN_LINK + audycja_ident + OFFSET_LINK + str(nr_site)
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(page_link, headers={'User-Agent': 'Mozilla/5.0'})
            body = custom_opener.open(req, timeout=15).read()
            html_str = body.decode('utf-8', errors='ignore')
            
            # Sprawdzamy czy na stronie znajduje się Astro Server Island dla podcastów
            match = re.search(r"(/_server-islands/PodcastsIsland\?[^'\"]+)", html_str)
            if match:
                island_path = html.unescape(match.group(1))
                island_url = "https://audycje.tokfm.pl" + island_path
                req_island = Request(island_url, headers={'User-Agent': 'Mozilla/5.0'})
                body_island = custom_opener.open(req_island, timeout=15)
                return BeautifulSoup(body_island, 'html.parser')
            
            return BeautifulSoup(body, 'html.parser')
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                sleep(2)
    raise last_err


def czy_button_next_jest_osiagalny(audycja_ident, nr_strony):
    try:
        soup = pobierz_soup_strony(audycja_ident, nr_strony)
        pagination = soup.find('div', class_="tok-pagination")
        if pagination:
            next_btn = pagination.find(["a", "button"], class_=re.compile(r"tok-pagination__button-next"))
            if next_btn:
                classes = next_btn.get("class", [])
                if "opacity-30" not in classes and "cursor-default" not in classes and not next_btn.has_attr("disabled"):
                    return True
    except Exception as e:
        print(f"Błąd w czy_button_next_jest_osiagalny: {e}")
    return False


def zgraj_strone_audycji (audycja_ident,nr_site):    
    audycje_wiersze={}
    czekaj=randrange(1,8)
    #czekaj=randrange(1,3)
    page_link=MAIN_LINK+audycja_ident+OFFSET_LINK+str(nr_site)
    print ("")
    print (page_link+" "+str(czekaj)+" sekund przerwy")                

    try:
        soup = pobierz_soup_strony(audycja_ident, nr_site)
    except Exception as e:
        print(f"Błąd pobierania strony: {e}")
        return audycje_wiersze
    
    # Próbujemy znaleźć listę podcastów na różne sposoby (nowy layout Astro, stary layout, itp.)
    audycje = soup.find('div', class_='tok-podcasts-wrapper') or soup.find('div', {"data-miejsce": re.compile(r'^Strona:\s*audycja', re.IGNORECASE)}) or soup.find('div', {"data-miejsce": "Strona: audycja"}) or soup
    if audycje is None:
        return audycje_wiersze
    audycje_metadane=audycje.find_all('li', class_='tok-podcasts__podcast')

    for fragment_strony in audycje_metadane:
        # podcast link -> podcast_id, podcast_nazwa
        podcast_link_tag=fragment_strony.find('a', href=re.compile(r'/podcast/'))
        if not podcast_link_tag:
            continue
        podcast_naglowek=podcast_link_tag['href']
        podcast_naglowek_rozbity=re.search(r"(podcast/)([0-9]*)(,)(.*)",podcast_naglowek)
        if not podcast_naglowek_rozbity:
            continue
        podcast_naglowek_rozbity=podcast_naglowek_rozbity.groups()
        podcast_id=podcast_naglowek_rozbity[1]
        podcast_nazwa=podcast_naglowek_rozbity[3]
        if podcast_nazwa and podcast_nazwa[0]=='-':
            podcast_nazwa=podcast_nazwa[1:]

        # audycja link -> audycja_id, audycja_nazwa
        audycja_link_tag=fragment_strony.find('a', href=re.compile(r'/audycja/'))
        if not audycja_link_tag:
            continue
        audycja_short_link=audycja_link_tag['href'].replace("https://audycje.tokfm.pl","")
        audycja_short_link=re.sub(r"^/?audycja/?", "", audycja_short_link)
        
        audycja_id_link=re.search(r"([0-9]*)(,)(.*)",audycja_short_link)
        if not audycja_id_link:
            continue
        audycja_id_link=audycja_id_link.groups()
        audycja_id=audycja_id_link[0]
        audycja_nazwa=audycja_id_link[2]
        audycja_opis=audycja_nazwa

        # data
        date_span=fragment_strony.find('span', class_='text-primary-dark-gray')
        podcast_data_i_czas=date_span.text.strip() if date_span else ""

        # czas trwania - szukamy "X min" w tekście
        li_text=fragment_strony.get_text()
        normalized_text = re.sub(r'\s+', ' ', li_text)
        m=re.search(r'(\d+)\s*min', normalized_text)
        podcast_trwanie=(m.group(1)+" min").strip() if m else "0 min"

        # goscie/prowadzacy
        w_studio = fragment_strony.find_all('a', href=re.compile(r'/gosc/'))
        if not w_studio:
            leaders_span=fragment_strony.find('span', class_='tok-podcasts__row--audition-leaders')
            w_studio=leaders_span.find_all('a') if leaders_span else []
            
        podcast_gosc=""
        if w_studio:
            for j,gosc_baza in enumerate(w_studio):
                if j>0:
                    podcast_gosc=podcast_gosc+', '
                podcast_gosc=podcast_gosc+gosc_baza.text.replace(',','').replace('\t','').replace('\n',' ').strip()
        else:
            podcast_gosc="Brak"

        data_index=datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Czasami w podcastach jest podana tylko godzina lub słowa kluczowe typu "Dziś" / "Wczoraj"
        if re.search(r'^[0-2][0-9]:[0-5][0-9]',podcast_data_i_czas):
            dzis=datetime.now().strftime("%d.%m.%Y")
            podcast_data_i_czas=dzis+" "+podcast_data_i_czas
        elif "Dziś" in podcast_data_i_czas:
            dzis=datetime.now().strftime("%d.%m.%Y")
            podcast_data_i_czas=podcast_data_i_czas.replace("Dziś", dzis)
        elif "Wczoraj" in podcast_data_i_czas:
            wczoraj=(datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
            podcast_data_i_czas=podcast_data_i_czas.replace("Wczoraj", wczoraj)

        audycje_wiersze[podcast_id]=[audycja_id,audycja_nazwa,audycja_opis,\
                              podcast_nazwa,\
                              podcast_data_i_czas,podcast_trwanie,\
                              data_index,podcast_gosc,\
                                ]
    sleep(czekaj)
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
def update_bazy(max_pages=None):
    audycje_link = zaladuj_audycje_json(JSON_FILE_FAVORITE)
    nowe_audycje_licznik = 0

    sciezka = Path(DATABASE_FILE)
    if not sciezka.exists():
        log_error("Brak pliku bazy danych: " + DATABASE_FILE)
        exit()
        
    conn = sqlite3.connect(DATABASE_FILE)    
    cur = conn.cursor()

    log_info("Rozpoczynam aktualizację bazy danych (tok-fm-favorite.json)...")

    for audycja in audycje_link:
        log_info(f"Sprawdzam nowości w audycji: {audycje_link[audycja][1]}...")
        Update=True
        i=1        
        while Update:            
            if max_pages is not None and i > max_pages:
                break
            audycje_wiersze=zgraj_strone_audycji(audycje_link[audycja][0],i)
            i+=1
            if not audycje_wiersze:
                break
            
            all_exist_on_page = True
            for aud in audycje_wiersze:                        
                cur.execute("SELECT id_podcast, date_podcast FROM tokfm WHERE id_podcast = ?", (int(aud),))
                rows = cur.fetchone()
                if not rows:
                    all_exist_on_page = False
                    log_success(f"Dodano do bazy: {audycje_wiersze[aud][1]} | {audycje_wiersze[aud][4]} | {audycje_wiersze[aud][3]}")
                    sql_false=0                
                    id_podcast_=int(aud)                                
                    id_audition_=int(audycje_wiersze[aud][0])
                    name_audition_=audycje_wiersze[aud][1]
                    name_podcast_=audycje_wiersze[aud][3]
                    date_podcast_=audycje_wiersze[aud][4]
                    during_podcast_=audycje_wiersze[aud][5]
                    date_index_=audycje_wiersze[aud][6]
                    podcast_heard_=sql_false
                    guest_podcast_=audycje_wiersze[aud][7]
                    cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                            date_podcast,during_podcast,date_index,podcast_heard,guest_podcast) VALUES(?,?,?,?,?,?,?,?,?)",\
                            (id_podcast_,name_podcast_,id_audition_,name_audition_,date_podcast_,during_podcast_,date_index_,podcast_heard_,guest_podcast_))
                    conn.commit()                
                    nowe_audycje_licznik+=1
            
            # W trybie standardowym (bez force i bez limitu stron) przerywamy przeszukiwanie danej audycji,
            # gdy CAŁA strona zawiera wyłącznie odcinki, które już były zapisane w bazie
            if max_pages is None and all_exist_on_page:
                Update = False
    cur.close()
    conn.close()
#idioctwo, dac do klasy    
    audycje_link = zaladuj_audycje_json(JSON_FILE_FAVORITE)
    log_success(f"Aktualizacja zakończona. Dodano nowych odcinków: {nowe_audycje_licznik}")


def zapisz_katalog_full(full):
    sorted_items = sorted(full.items(), key=lambda item: int(item[1][0].split(',')[0]))
    lines = ['{']
    for i, (k, v) in enumerate(sorted_items):
        sep = ',' if i < len(sorted_items) - 1 else ''
        line = f'{json.dumps(k, ensure_ascii=False)}:[{json.dumps(v[0], ensure_ascii=False)},{json.dumps(v[1], ensure_ascii=False)}]{sep}'
        lines.append(line)
    lines.append('}\n')
    with open(JSON_FILE_ALL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def update_katalogu():
    log_info(f"Wczytuję katalog audycji z {JSON_FILE_ALL}...")
    full = zaladuj_audycje_json(JSON_FILE_ALL)
    
    # Znajdź najwyższy numer ID w pliku
    id_list = []
    for k, v in full.items():
        try:
            aid = int(v[0].split(',')[0])
            id_list.append(aid)
        except Exception:
            pass
            
    if not id_list:
        max_id = 0
    else:
        max_id = max(id_list)
        
    log_info(f"Najwyższy znany numer audycji w {JSON_FILE_ALL}: {max_id}")
    log_info("Sprawdzam czy na stronie TOK FM pojawiły się nowe audycje...")
    
    curr_id = max_id + 1
    consecutive_404 = 0
    max_consecutive_404 = 5
    nowe_audycje = []
    
    while consecutive_404 < max_consecutive_404:
        print(f"\r[*] Sprawdzam ID {curr_id} (oczekiwanie na koniec: {consecutive_404}/{max_consecutive_404} pustych)...", end="", flush=True)
        url = f"{MAIN_LINK}{curr_id}"
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            resp = custom_opener.open(req, timeout=12)
            final_url = resp.geturl()
            m_slug = re.search(r'/audycja/(\d+),([^/?#]+)', final_url)
            if m_slug:
                aid_found = int(m_slug.group(1))
                slug = m_slug.group(2)
                raw = resp.read(15000).decode('utf-8', errors='ignore')
                m_title = re.search(r'<title>([^<]+)</title>', raw)
                title = slug
                if m_title:
                    t = html.unescape(m_title.group(1))
                    t = re.sub(r'^(?:Audycja|Podcast):\s*', '', t, flags=re.I)
                    t = re.sub(r'\s*-\s*słuchaj podcastów TOK FM.*', '', t, flags=re.I)
                    t = re.sub(r'\s*[|\-]\s*TOK FM.*', '', t, flags=re.I)
                    title = t.strip()
                
                key = slug
                if key in full:
                    key = f"{slug}-{aid_found}"
                    
                wpis = [f"{aid_found},{slug}", title]
                full[key] = wpis
                nowe_audycje.append((key, wpis))
                zapisz_katalog_full(full)
                print()
                log_success(f"Znaleziono i dopisano do {JSON_FILE_ALL}: ID {aid_found} - '{title}' (klucz: {key})")
                consecutive_404 = 0
            else:
                consecutive_404 += 1
        except HTTPError as e:
            if e.code == 404:
                consecutive_404 += 1
            else:
                consecutive_404 += 1
        except Exception:
            consecutive_404 += 1
            
        curr_id += 1
        sleep(1)
        
    print()
    if nowe_audycje:
        log_success(f"Zakończono sprawdzanie katalogu. Łącznie dopisano {len(nowe_audycje)} nowych audycji.")
        log_info("Możesz teraz skopiować interesujące Cię linie do pliku tok-fm-favorite.json.")
    else:
        log_info(f"Brak nowych audycji w serwisie TOK FM (sprawdzono do ID {curr_id - 1}). Katalog jest aktualny.")
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
# Ścieżka do wyników (na dysku E)
katalog_tok_fm_podcasty_result_dir=katalog_tok_fm_podcasty_base+"/mnt/e/audycje/tok fm/Result"+SEP
katalog_tok_fm_podcasty_result_dir_przesluchane=katalog_tok_fm_podcasty_result_dir+SEP+"Przesluchane"+SEP
katalog_tok_fm_podcasty_result_dir_nieprzesluchane=katalog_tok_fm_podcasty_result_dir+SEP+"Nieprzesluchane"+SEP

# Ścieżka na telefonie (ustawiana dynamicznie)
katalog_tok_fm_podcasty_android_files=""


def szukaj_na_dysku():
    global katalog_tok_fm_podcasty_android_files
    
    log_info("Sprawdzam połączenie USB...")
    # 1. Sprawdzamy czy jakiekolwiek urządzenie Android/MTP jest podpięte pod USB w WSL
    mtp_connected = False
    import glob
    keywords = ["android", "mtp", "ptp", "samsung", "galaxy", "pixel", "phone", "mobile", "tablet"]
    for path in glob.glob("/sys/bus/usb/devices/*/product") + glob.glob("/sys/bus/usb/devices/*/*/interface"):
        try:
            with open(path, "r") as f:
                name = f.read().lower()
            if any(kw in name for kw in keywords):
                mtp_connected = True
                break
        except Exception:
            pass

    # Dynamicznie określamy punkt montowania z ścieżki bazowej
    mount_point = "/mnt/s23"
    for name in ["Pamięć wewnętrzna", "Internal shared storage"]:
        if name in SCIEZKA_TELEFONU_BASE:
            mount_point = SCIEZKA_TELEFONU_BASE.split(name)[0].rstrip("/")
            break

    if not mtp_connected:
        log_error("Telefon (MTP) nie jest podłączony do WSL za pomocą usbipd!")
        print("\nAby podłączyć telefon do WSL, wykonaj:")
        print("1. W Windows PowerShell (jako Administrator) sprawdź listę urządzeń:")
        print("   usbipd list")
        print("2. Udostępnij telefon (jeśli robisz to po raz pierwszy):")
        print("   usbipd bind --force --busid <BUSID_TELEFONU>")
        print("3. Podłącz telefon do WSL:")
        print("   usbipd attach --wsl --busid <BUSID_TELEFONU>")
        exit()

    log_success("Telefon podłączony pod USB.")
    log_info("Sprawdzam montowanie telefonu w WSL...")
    path_moved = Path(SCIEZKA_TELEFONU_BASE) / "moved"
    path_files = Path(SCIEZKA_TELEFONU_BASE) / "files"
    
    if path_moved.exists():
        path_telefon = path_moved
    elif path_files.exists():
        path_telefon = path_files
    else:
        log_error("Telefon (MTP) jest podłączony przez USB do WSL, ale nie jest zamontowany lub ścieżka jest niepoprawna!")
        print(f"Nie znaleziono katalogu 'moved' ani 'files' pod '{SCIEZKA_TELEFONU_BASE}'")
        print("\nAby zamontować telefon, wykonaj w WSL:")
        print("1. Upewnij się, że ekran telefonu jest odblokowany.")
        print(f"2. Zamontuj telefon komendą (bez sudo):")
        print(f"   jmtpfs {mount_point}")
        exit()
        
    log_success("Telefon zamontowany pomyślnie.")
    log_info(f"Katalog z plikami telefonu: {path_telefon}")
    log_info("Skanuję pliki na telefonie (MTP) - to może chwilę potrwać...")
        
    katalog_tok_fm_podcasty_android_files = str(path_telefon) + SEP
    p1Android = Path(katalog_tok_fm_podcasty_android_files)
    p1Result = Path(katalog_tok_fm_podcasty_result_dir)        
    p2Result = Path(katalog_tok_fm_podcasty_result_dir_przesluchane)        
    p3Result = Path(katalog_tok_fm_podcasty_result_dir_nieprzesluchane)
            
    if not p1Result.exists():
        p1Result.mkdir()
    if not p2Result.exists():
        p2Result.mkdir()
    if not p3Result.exists():
        p3Result.mkdir()
            
    # Skanowanie
    znaleziono_plikow = 0
    for root, dirs, files in os.walk(str(p1Android)):
        for file in files:            
            if re.search(r'^[0-9][0-9]\.mp3$', file):
                caly_plik_sciezka=os.path.join(root, file)                
                id_podcast=SEP+caly_plik_sciezka.replace(str(p1Android), "")
                id_podcast=id_podcast.rstrip('mp3')
                id_podcast=id_podcast.rstrip('.')                
                id_podcast=id_podcast.replace(SEP,"").lstrip("0")                
                id_podcast=id_podcast.replace(SEP,"")
                podcast_file[id_podcast]=caly_plik_sciezka
                znaleziono_plikow += 1
                if znaleziono_plikow % 10 == 0:
                    print(f" \033[1;34m[*]\033[0m Przeskanowano {znaleziono_plikow} plików na telefonie...", end="\r", flush=True)
                    
    log_success(f"Skanowanie zakończone. Znaleziono {znaleziono_plikow} plików podcastów na telefonie.")



#----przeszukiwanie w bazie i sprawdzanie czy audycja jest przesluchana czy nie
#----jezeli jest inaczej niz trzeba to przerzuca sie ja automatycznie

def szukaj_w_bazie_i_katalogu(katalog_z,katalog_do):    

#-do poprawki
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()

    kat_przesluchane_=str(katalog_z)+str(SEP)
    kat_nieprzesluchane_=str(katalog_do)+str(SEP)

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
                        p = Path(katalog)
                        if not p.exists():                      
                            p.mkdir()                    
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
    

    if re.search(r"\+aud",parametry):
        PARAM_NAME['AUD']=re.search(r"(\+aud) (\S*)",parametry).groups()[1]
        no_par=False

    if re.search(r"\+date",parametry):
        PARAM_NAME['DATE']=re.search(r"(\+date) (\S*)",parametry).groups()[1]
        no_par=False

    if re.search(r"\+guest",parametry):
        PARAM_NAME['GUEST']=re.search(r"(\+guest) (\S*)",parametry).groups()[1]
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
                nazwa_audycji = audycje_link[i[1]][1] if i[1] in audycje_link else str(i[1]).replace("-", " ")
                print (str(j)+".",i[0],"|",nazwa_audycji,"|",str(i[2]).replace("-"," "),"|",i[3])


        cur.close()
        conn.close()
    else:
        print ("parametry to +aud (audycja) lub/i +date (data)")        



def pobierz_i_zgraj_podcast_indywidualny(id_podcast, conn):
    url = f"https://audycje.tokfm.pl/podcast/{id_podcast}"
    log_info(f"Nie znaleziono podcastu {id_podcast} w bazie. Próbuję pobrać metadane bezpośrednio ze strony...")
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req)
        final_url = resp.geturl()
        body = resp.read()
        soup = BeautifulSoup(body, 'html.parser')
        
        # 1. Title (name_podcast) from og:url or redirected URL
        url_meta = soup.find('meta', property='og:url')
        podcast_nazwa = ""
        target_url = url_meta['content'] if url_meta else ""
        match = re.search(r"podcast/[0-9]+,(.*)", target_url) or re.search(r"podcast/[0-9]+,(.*)", final_url)
        if match:
            podcast_nazwa = match.group(1)
        if not podcast_nazwa:
            # Fallback to og:title
            title_meta = soup.find('meta', property='og:title')
            title = title_meta['content'] if title_meta else ''
            if title.startswith('Posłuchaj podcastu: '):
                title = title[len('Posłuchaj podcastu: '):]
            if title.endswith(' - TOK FM'):
                title = title[:-len(' - TOK FM')]
            podcast_nazwa = title.replace(' ', '-')

        # 2. Audition (id_audition and name_audition)
        audition_link = soup.find('a', href=re.compile(r'/audycja/'))
        audition_id = "0"
        audition_nazwa = "Nieznana"
        if audition_link:
            href = audition_link['href']
            slug = href.split('/')[-1]
            if ',' in slug:
                parts = slug.split(',')
                audition_id = parts[0]
                audition_nazwa = parts[1]
            else:
                audition_nazwa = slug

        # 3. Date
        date_div = soup.find('div', class_=re.compile('text-base text-arsenic'))
        date_str = ""
        if date_div:
            date_text = date_div.get_text()
            match = re.search(r'Data dodania:\s*([\d\-\.\s:]+)', date_text)
            if match:
                date_raw = match.group(1).strip()
                if '-' in date_raw:
                    parts = date_raw.split()
                    ymd = parts[0].split('-')
                    date_str = f"{ymd[2]}.{ymd[1]}.{ymd[0]}"
                    if len(parts) > 1:
                        date_str += f" {parts[1]}"
                else:
                    date_str = date_raw
        if not date_str:
            date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        # 4. Duration and guests from the button
        duration = "0 min"
        guests = "Brak"
        play_btn = soup.find('button', {'data-id': str(id_podcast)})
        if not play_btn:
            play_btn = soup.find('button', class_=re.compile('tok-podcasts__button--play'))
        if play_btn:
            btn_text = play_btn.get_text()
            dur_match = re.search(r'(\d+\s*min)', btn_text)
            if dur_match:
                duration = dur_match.group(1).strip()
            # Guests
            data_guests = play_btn.get('data-guests')
            if data_guests:
                guests = data_guests.strip('\'\"')
            else:
                gosc_links = soup.find_all('a', href=re.compile(r'/gosc/'))
                if gosc_links:
                    guests = ", ".join([g.get_text().strip() for g in gosc_links])

        # Write to database
        cur = conn.cursor()
        sql_false = 0
        date_index = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cur.execute("INSERT OR IGNORE INTO tokfm (id_podcast,name_podcast,id_audition,name_audition,\
                date_podcast,during_podcast,date_index,podcast_heard,guest_podcast) VALUES(?,?,?,?,?,?,?,?,?)",\
                (int(id_podcast), podcast_nazwa, int(audition_id), audition_nazwa, date_str, duration, date_index, sql_false, guests))
        conn.commit()
        cur.close()
        
        log_success(f"Pomyślnie pobrano metadane dla podcastu {id_podcast} ({podcast_nazwa}) i zapisano w bazie.")
        return (int(id_podcast), audition_nazwa, podcast_nazwa, date_str, sql_false, int(audition_id))
    except Exception as e:
        log_error(f"Nie udało się automatycznie pobrać podcastu {id_podcast} ze strony: {e}")
        return None



def szukaj_w_bazie_i_zgraj():
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    licznik_skopiowane=0
    licznik_skasowane=0
    skopiowane_pliki = []
    nowe_audycje_zapis = {}

    log_info("Dopasowuję pliki z bazą danych i kopiuję nowe audycje...")

    licznik_sprawdzonych = 0
    for i in podcast_file:
        licznik_sprawdzonych += 1
        if licznik_sprawdzonych % 10 == 0:
            print(f" \033[1;34m[*]\033[0m Sprawdzono {licznik_sprawdzonych} / {len(podcast_file)} plików...", end="\r", flush=True)

        cur.execute("SELECT id_podcast, name_audition, name_podcast, date_podcast, podcast_heard, id_audition FROM tokfm where id_podcast = "+i)
        rows = cur.fetchone()
        if not rows:
            rows = pobierz_i_zgraj_podcast_indywidualny(i, conn)

        if not rows:
            log_error("Nie znaleziono audycji w bazie: "+i)
        else:
            #katalog_podcast=rows[1].replace("-"," ")
            if rows[1] in audycje_link:
                katalog_podcast=audycje_link[rows[1]][1]
            else:
                katalog_podcast=rows[1].replace("-", " ")
                friendly_name = rows[1].replace("-", " ")
                id_audition = rows[5] if (len(rows) > 5 and rows[5] is not None) else "0"
                nowe_audycje_zapis[rows[1]] = (id_audition, friendly_name)
            date_str = znormalizuj_date(rows[3])
            try:
                data_audycji=datetime.strptime(date_str,"%d.%m.%Y %H:%M")
            except ValueError:
                try:
                    data_audycji=datetime.strptime(date_str.split()[0],"%d.%m.%Y")
                except ValueError:
                    data_audycji=datetime.now()
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
            p1=Path(katalog)

            if not p1.exists():
                p1.mkdir()


            katalog=katalog+SEP+rok_miesiac
            katalog_opozycyjny=katalog_opozycyjny+SEP+rok_miesiac
            
            p1=Path(katalog)

            if not p1.exists():
                p1.mkdir()
            filename_no_dash=rows[2].replace('-', ' ')
            filename=dzien+" - "+filename_no_dash+".mp3"
                        
            katalog_filename=katalog+SEP+filename
            katalog_filename_opozycyjny=katalog_opozycyjny+SEP+filename
            p1=Path(katalog_filename)
            if not p1.exists():                
                copyfile(podcast_file[i],str(p1))
                # Czyszczenie wiersza przed wypisaniem sukcesu, aby usunąć licznik \r
                print(" " * 60, end="\r")
                log_success(f"Skopiowano: {katalog_podcast}/{rok_miesiac}/{filename}")
                skopiowane_pliki.append(f"{katalog_podcast}/{rok_miesiac}/{filename}")
                licznik_skopiowane+=1
            #Kasujemy pozostalosci jezeli byl w dawnym katalogu
            p1=Path(katalog_filename_opozycyjny)
            if p1.exists():
                p1.unlink()
                print(" " * 60, end="\r")
                log_success(f"Skasowałem z przeciwnego katalogu: {katalog_podcast}/{rok_miesiac}/{filename}")
                licznik_skasowane+=1
     
    # Czyszczenie linii postępu na końcu
    print(" " * 60, end="\r")
    cur.close()
    conn.close()
    
    print("\n--- RAPORT ZGRYWANIA ---")
    print(f"Skopiowano nowych audycji: {licznik_skopiowane}")
    if skopiowane_pliki:
        print("Nowe pliki:")
        for plik in skopiowane_pliki:
            print(f" - {plik}")
    else:
        print("Brak nowych plików do skopiowania (wszystkie były już zgrane).")
    if licznik_skasowane > 0:
        print(f"Skasowano przestarzałych plików: {licznik_skasowane}")

    if nowe_audycje_zapis:
        print("\n\033[1;32m[+]\033[0m Wykryto nowe audycje. Możesz dodać je do pliku konfiguracyjnego JSON:")
        print("{")
        items = list(nowe_audycje_zapis.items())
        for idx, (key, (id_aud, friendly)) in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""
            print(f'  "{key}": ["{id_aud},{key}", "{friendly}"]{comma}')
        print("}")


#-------------------------

def drukuj_nazwe_programu ():
    print (PROGRAM_NAME+" "+PROGRAM_WERSJA+" ("+PROGRAM_DATA+")")

def wyswietl_pomoc ():
    print ("Proszę podać parametr \n")
    print ("update [liczba_stron] - Aktualizuje bazę podcastów ze strony (plik tok-fm-favorite.json, opcjonalna liczba ogranicza ilość sprawdzanych stron)")
    print ("update_catalog - Sprawdza czy w serwisie TOK FM pojawiły się nowe audycje i dopisuje je do pliku tok-fm-full.json")
    print ('kopiuj - Kopiuje nowe podcasty z podłączonego telefonu, zmienia nazwy i kataloguje na dysku')
    print ("search_podcast - Szuka podcasty")    
    print ("move_heard - Sprawdza czy audycje były przesłuchane i je przenosi")
    print ("help - Wyswietla tą pomoc")
    print ("\n* Pamiętaj, aby po zakończeniu pracy odmontować telefon komendą:")
    print ("  fusermount -u /mnt/s23")



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
if __name__ == '__main__':
    drukuj_nazwe_programu()
    parametr_name=nazwa_parametru()

    if not parametr_name:
        wyswietl_pomoc()
    else:
        if parametr_name[0] in ["update_catalog", "update-catalog", "update_katalog"]:
            update_katalogu()

        elif parametr_name[0] =="update":
            if len(parametr_name) > 1 and parametr_name[1] in ["catalog", "katalog"]:
                update_katalogu()
            else:
                max_pages = None
                args = parametr_name[1:]
                
                for arg in args:
                    if arg.isdigit():
                        max_pages = int(arg)
                    else:
                        print(f"Błędny parametr '{arg}'. Użyj: update [liczba_stron] lub update_catalog")
                        exit()
                
                update_bazy(max_pages)


        if parametr_name[0] in ["kopiuj", "fix_names"]:        
            szukaj_na_dysku()        
            szukaj_w_bazie_i_zgraj()

        if parametr_name[0] =="search_podcast":
            szukaj_i_wyswietl(" ".join(parametr_name))        
                
        if parametr_name[0] =="move_heard":
            print ("Sprawdzam w podkastach: Przesluchane")
            szukaj_w_bazie_i_katalogu(katalog_tok_fm_podcasty_result_dir_przesluchane,katalog_tok_fm_podcasty_result_dir_nieprzesluchane)
            print ("Sprawdzam w podkastach: NiePrzesluchane")
            szukaj_w_bazie_i_katalogu(katalog_tok_fm_podcasty_result_dir_nieprzesluchane,katalog_tok_fm_podcasty_result_dir_przesluchane)


        
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



    
    
    
    
