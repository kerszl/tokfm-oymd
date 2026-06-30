# Tokfm-oymd (Wersja bardzo beta)

## Instalacja
```bash
git clone https://github.com/kerszl/tokfm-oymd.git
cd tokfm-oymd.git
chmod +x tokfm-oymd
pip3 install --upgrade pip
pip3 install bs4
```

## Kopiowanie mp3 do czytelnej postaci
- Sprawdź gdzie są Twoje podcasty z Tok-Fm (zazwyczaj są w `Android/data/fm.tokfm.android/moved/`)
- Podłącz telefon do WSL i zamontuj go, a następnie uruchom polecenie:
```bash
python tokfm-oymd.py kopiuj
```
- Podcasty zostaną skopiowane na Twój dysk i zostaną im nadane odpowiednie nazwy.

![alt text](kopiowanie.png)