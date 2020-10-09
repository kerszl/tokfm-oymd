tablica =["PIEies filemon","kot","zaba"]
slownik = {"klucz1":"wartosc1"
          ,"Klucz2":"wartosc2"
          ,"klucz3":"wartosc3"}

#print (tablica[1])

for i,j in slownik.items():
    print (i,j)

"""
for i in tablica:
    print (i[0:4].lower())
"""

"""
from datetime import datetime
import re

TylkoGodzina="10:00"

if re.search('^[0-2][0-9]:[0-5][0-9]',TylkoGodzina):
    dzis=datetime.now().strftime("%d.%m.%Y")
    print (dzis+" "+TylkoGodzina)

    print ("jest dzien")
"""
"""
if datetime()
data_index=datetime.now().strftime("%d-%m-%Y %H:%M:%S")

DATA_AUDYCJI=datetime.strptime(rows[3],"%d.%m.%Y %H:%M")
"""