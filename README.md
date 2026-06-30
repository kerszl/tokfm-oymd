# TOK FM on your MP3 Device (tokfm-oymd)

Aplikacja kliencka dla systemu **Linux / WSL** służąca do automatycznego zgrywania, katalogowania i porządkowania podcastów z aplikacji mobilnej TOK FM bezpośrednio z telefonu podłączonego pod USB (MTP).

Skrypt automatycznie odczytuje pliki `.mp3` pobrane na telefonie, odpytuje bazę danych i stronę TOK FM w celu odtworzenia oryginalnych nazw odcinków, po czym kopiuje je do uporządkowanej struktury katalogów na Twoim komputerze.

> [!NOTE]  
> Program został zoptymalizowany pod kątem działania w środowisku Linux (w tym WSL - Windows Subsystem for Linux).

---

## 🚀 Główne Funkcje

* **Logowanie w stylu `pwntools`:** przejrzyste, kolorowe i animowane komunikaty w konsoli informujące o postępie prac (`[*]`, `[+]`, `[-]`).
* **Automatyczne wykrywanie katalogów telefonu:** automatycznie rozpoznaje strukturę katalogów aplikacji TOK FM na telefonie (`/moved/` lub `/files/`).
* **Inteligentne połączenie WSL-USB (MTP):** weryfikuje połączenie telefonu przez USBIPD w WSL, a w razie potrzeby automatycznie montuje telefon przez `jmtpfs`.
* **Dynamiczny Fallback:** jeśli na telefonie znajduje się plik odcinka, którego nie ma w lokalnej bazie danych, program w locie pobierze metadane bezpośrednio z dedykowanej strony podcastu.
* **Wypełnianie luk w bazie:** zaawansowane parametry aktualizacji (`force` lub limit stron) ułatwiające odtworzenie brakującej historii podcastów.
* **Auto-konfiguracja:** wykrywa nowe audycje i generuje gotowy do wklejenia kod konfiguracyjny JSON.

---

## 🛠️ Instalacja i Wymagania

### 1. Wymagane pakiety systemowe (Linux/WSL)
Do montowania telefonu przez MTP wymagany jest pakiet `jmtpfs`:
```bash
sudo apt update
sudo apt install jmtpfs
```

### 2. Pobranie projektu i instalacja zależności
```bash
git clone https://github.com/kerszl/tokfm-oymd.git
cd tokfm-oymd
pip3 install -r requirements.txt
```

---

## 📖 Instrukcja Użycia

### 1. Kopiowanie i porządkowanie podcastów z telefonu
Podłącz telefon do portu USB (jeśli używasz WSL, upewnij się, że urządzenie MTP jest udostępnione do WSL przez `usbipd`). Następnie uruchom:
```bash
python tokfm-oymd.py kopiuj
```
Program automatycznie zweryfikuje połączenie, zamontuje pamięć telefonu, przeskanuje pliki, dopasuje ich nazwy i skopiuje je do odpowiednich katalogów według schematu:
`Result/Nieprzesluchane/[Nazwa Audycji]/[Rok - Miesiąc]/[Dzień] - [Tytuł odcinka].mp3`

![Podgląd działania procesu kopiowania](kopiowanie.png)

### 2. Aktualizacja lokalnej bazy danych podcastów
Aby zaktualizować lokalną bazę danych SQLite najnowszymi odcinkami ze strony internetowej TOK FM:
```bash
python tokfm-oymd.py update [full/lite] [force/liczba_stron]
```
* **`full`** – aktualizuje wszystkie audycje zdefiniowane w pliku `tok-fm-full.json`.
* **`lite`** – aktualizuje tylko wybrane audycje (ulubione) zdefiniowane w pliku `tok-fm-fav.json`.
* **`force`** – wyłącza domyślne szybkie zatrzymywanie na duplikatach i przeszukuje całą historię stron danej audycji.
* **`[liczba_stron]`** (np. `5`) – przeszukuje dokładnie zadeklarowaną liczbę stron wstecz, ignorując pojedyncze duplikaty (przydatne do uzupełniania niedawnych braków).

### 3. Zarządzanie przesłuchanymi audycjami
Weryfikuje stan odsłuchania podcastów i przenosi przesłuchane/nieprzesłuchane odcinki między odpowiednimi katalogami:
```bash
python tokfm-oymd.py move_heard
```

### 4. Wyszukiwanie podcastów w bazie danych
```bash
python tokfm-oymd.py search_podcast
```

---

## 📝 Pliki Konfiguracyjne
* **`tok-fm-fav.json`** – konfiguracja Twoich ulubionych audycji (dla opcji `update lite`).
* **`tok-fm-full.json`** – konfiguracja wszystkich śledzonych audycji (dla opcji `update full`).
* **`tokfm.db`** – lokalna baza SQLite przechowująca metadane wszystkich odcinków.