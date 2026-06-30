# Changelog

## [0.25] - 2026-06-30

### Naprawiono
- **Formatowanie JSON dla nowych audycji:** Usunięto nadmiarowy przecinek po ostatnim elemencie w wygenerowanym słowniku JSON nowych audycji, co czyni go w pełni poprawnym i gotowym do bezpośredniego wklejenia.

## [0.24] - 2026-06-30

### Dodano
- **Generowanie wpisu konfiguracyjnego JSON dla nowych audycji:** Jeśli podczas kopiowania program zidentyfikuje nową audycję, której nie ma w plikach konfiguracyjnych JSON (`tok-fm-fav.json` lub `tok-fm-full.json`), na samym końcu raportu wygeneruje gotowy do skopiowania wpis w formacie JSON (zawierający ID audycji, jej techniczną nazwę oraz czytelną nazwę przyjazną dla katalogu). Ułatwia to dodawanie nowo odkrytych audycji do stałej konfiguracji.

## [0.23] - 2026-06-30

### Dodano
- **Wymuszenie głębokiego skanowania i limit stron w `update`:** Wprowadzono opcjonalny trzeci argument dla komendy `update` umożliwiający ominięcie wczesnego zatrzymywania na duplikatach w celu uzupełnienia luk w bazie danych:
  - `python tokfm-oymd.py update [full/lite] force` - skanuje bezwarunkowo wszystkie dostępne strony dla każdej audycji.
  - `python tokfm-oymd.py update [full/lite] [liczba]` - skanuje bezwarunkowo zadeklarowaną liczbę stron (np. `5`), co pozwala szybko wypełnić niedawne braki.
- Wypisanie informacji o nowych przełącznikach w pomocy programu (`help`).

## [0.22] - 2026-06-30

### Dodano
- **Automatyczne pobieranie brakujących podcastów (Dynamiczny Fallback):** Jeśli podczas uruchamiania opcji `kopiuj` skrypt znajdzie plik na telefonie (np. stary odcinek z lutego), którego nie ma w lokalnej bazie danych SQLite (ponieważ został pobrany na telefonie przed zaktualizowaniem bazy lub baza miała luki), program nie wyrzuca już błędu. Zamiast tego automatycznie pobiera w locie metadane bezpośrednio z dedykowanej strony podcastu `https://audycje.tokfm.pl/podcast/[ID]`, poprawnie parsuje jego nazwę, audycję, datę dodania, prowadzących, gości, czas trwania, a następnie zapisuje go w bazie i bez problemu kontynuuje operację kopiowania.

## [0.21] - 2026-06-30

### Dodano
- **Logowanie pwntools w komendzie `update`:** Dostosowano również komendę `update` do kolorowego logowania w stylu `pwntools`. Zastąpiono surowe printy eleganckimi i czytelnymi komunikatami:
  - `[*]` przy rozpoczęciu aktualizacji i sprawdzaniu nowości dla poszczególnych audycji.
  - `[+]` przy dodawaniu nowego odcinka do bazy danych oraz przy podsumowaniu zakończenia aktualizacji.
  - `[-]` w przypadku błędów pliku bazy danych.

### Zmieniono
- **Wyciszenie komunikatów `Not update`:** Usunięto wypisywanie informacji `Not update: ...` dla odcinków, które są już obecne w bazie. Dzięki temu aktualizacja jest znacznie bardziej przejrzysta i nie zapełnia okna terminala niepotrzebnym tekstem.

## [0.20] - 2026-06-30

### Dodano
- **Automatyczne wykrywanie folderów (`moved` / `files`):** Program nie wymaga już ręcznego przestawiania ścieżki w kodzie w zależności od wersji aplikacji TOK FM. Skrypt automatycznie sprawdza, czy na telefonie istnieje folder `moved` czy `files` i używa tego, który jest dostępny. W przypadku braku obu folderów wyświetla precyzyjną informację o błędzie.

## [0.19] - 2026-06-30

### Dodano
- **Logowanie w stylu pwntools:** Zaadaptowano schemat kolorowania i logowania konsolowego z biblioteki `pwntools`. Zdefiniowano czytelne, kolorowe prefiksy:
  - `[*]` w kolorze niebieskim dla informacji i trwających operacji.
  - `[+]` w kolorze zielonym dla sukcesów (wykrycie USB, pomyślny mount, skopiowanie lub usunięcie pliku).
  - `[-]` w kolorze czerwonym dla błędów.
- **Dynamiczny licznik weryfikacji:** Podczas dopasowywania plików z bazą danych wyświetlany jest na bieżąco licznik sprawdzonych plików (np. `[*] Sprawdzono 120 / 534 plików...`), który automatycznie znika po zakończeniu zadania.

### Zmieniono
- **Wyciszenie komunikatów o istniejących plikach:** Skrypt nie zasypuje już konsoli setkami linii `Plik istnieje: ...`. Wypisywane są wyłącznie informacje o faktycznie kopiowanych lub kasowanych plikach, co czyni wynik przejrzystym i przyspiesza działanie programu.

## [0.18] - 2026-06-30

### Dodano
- **Wyczerpujące komunikaty postępu (kopiuj):** Wprowadzono szczegółowe logowanie etapów w konsoli podczas uruchamiania opcji `kopiuj`. Użytkownik widzi dokładnie co się dzieje:
  - Weryfikacja wykrycia USB w WSL.
  - Sprawdzenie statusu zamontowania katalogu.
  - Licznik przeskanowanych plików na żywo podczas skanowania pamięci MTP (które przy dużych wolumenach może chwilę trwać).
  - Rozpoczęcie procesu dopasowywania i kopiowania.

### Naprawiono
- **Błąd wycinania znaków w ścieżce (lstrip):** Zastąpiono błędną metodę `.lstrip()` na ścieżce bezwzględnej bezpieczną metodą `.replace()`. Zapobiega to przypadkowemu ucięciu początkowych znaków w nazwach podkatalogów, jeśli pokrywały się z literami w ścieżce montowania.

## [0.17] - 2026-06-30

### Dodano
- **Generowanie raportu po kopiowaniu:** Po zakończeniu operacji kopiowania wyświetlany jest szczegółowy, czytelny raport podsumowujący ile nowych odcinków zostało skopiowanych oraz wypisujący listę ich ścieżek docelowych (lub informację o braku nowych plików do skopiowania).

### Zmieniono
- **Ogólne wykrywanie telefonów USB (MTP):** Sprawdzanie fizycznego podłączenia telefonu w WSL zostało uogólnione. Zamiast szukać konkretnego Vendor ID i Product ID dla Samsunga S23, program skanuje opisy wszystkich urządzeń USB pod kątem słów kluczowych (`android`, `mtp`, `ptp`, `samsung`, `galaxy`, `pixel` itp.). Od teraz detekcja USBIPD działa dla dowolnego telefonu podłączonego w trybie przesyłania plików.
- **Zmiana nazwy komendy na `kopiuj`:** Główna komenda odpowiedzialna za zgrywanie została przemianowana na `kopiuj` (z zachowaniem aliasu `fix_names` dla kompatybilności wstecznej).

## [0.16] - 2026-06-30

### Dodano
- **Bezpośrednie kopiowanie z telefonu:** Dodano pełną obsługę kopiowania i automatycznego nazywania plików `.mp3` bezpośrednio z zamontowanego telefonu w WSL przy użyciu zmiennej `SCIEZKA_TELEFONU_BASE` (domyślnie `/mnt/s23/Pamięć wewnętrzna/Android/data/fm.tokfm.android/`).
- **Inteligentne sprawdzanie połączenia (Dwuetapowe):** Program weryfikuje teraz przy uruchomieniu:
  1. Czy urządzenie USB telefonu jest podpięte pod USBIPD w WSL (na podstawie VID:PID `04e8:6860`). Jeśli nie, wyświetla czytelną instrukcję z komendami dla Windows PowerShell.
  2. Czy telefon jest zamontowany w systemie plików WSL za pomocą `jmtpfs` na wyliczonym punkcie montowania. Jeśli nie, wyświetla instrukcję montowania.

### Zmieniono
- **Uporządkowanie i usunięcie nieużywanych funkcji:**
  - Usunięto nieużywaną i zbędną opcję/metodę `fix_podcast`.
  - Zaktualizowano ekrany pomocy (`wyswietl_pomoc()`), aby odzwierciedlały nową funkcjonalność.

### Naprawiono
- **Błąd KeyError przy starych/nieznanych audycjach:** Zaimplementowano bezpieczne wyszukiwanie nazw audycji w słowniku `audycje_link` dla starych i usuniętych programów w bazie (np. `U-TOKtora`). W przypadku braku dopasowania program bezpiecznie używa surowej nazwy z bazy danych, zamiast rzucać błędem `KeyError` i przerywać pracę.

## [0.15] - 2026-06-30

### Dodano
- **Obsługa Astro Server Islands:** Dostosowano parser do nowej architektury strony TOK FM (Astro). Skrypt dynamicznie pobiera i analizuje asynchroniczne komponenty (tzw. "serwerowe wyspy") pod adresem `/_server-islands/PodcastsIsland`, w których renderowana jest lista podcastów.
- **Konwersja dat względnych:** Dodano automatyczne tłumaczenie względnych określeń czasu ("Dziś", "Wczoraj") na standardowy format daty (`DD.MM.YYYY`), co zapewnia spójność bazy danych SQLite i zapobiega niepotrzebnemu pobieraniu starych stron przy kolejnych aktualizacjach.

### Zmieniono
- **Usunięto wsparcie dla Windowsa:** Uproszczono program pod kątem działania wyłącznie w środowisku Linux (oraz WSL). Usunięto ścieżki windowsowe (użycie `PureWindowsPath` i platformowe instrukcje warunkowe `sys.platform == "win32"`), a całość kodu ujednolicono na standardową obsługę ścieżek POSIX (`pathlib.Path`).
- **Obsługa linków względnych:** Zaktualizowano wyrażenia regularne parsujące linki audycji oraz podcastów, aby poprawnie obsługiwały zarówno linki względne (nowy format TOK FM), jak i bezwzględne.
- **Dopasowanie do nowego kodu HTML:**
  - Zaktualizowano wyszukiwanie gości odcinka na podstawie linków z prefiksem `/gosc/` (nowy układ zamiast klasy `tok-podcasts__row--audition-leaders`).
  - Dodano oczyszczanie białych znaków i znaków nowej linii przy parsowaniu czasu trwania odcinka.

### Naprawiono
- **Literówka w pliku konfiguracyjnym:** Usunięto zbędny nawias kwadratowy w nazwie audycji *"Otwarta Kuchnia"* w pliku `tok-fm-full.json` (`"510,Otwarta-Kuchnia]"` -> `"510,Otwarta-Kuchnia"`).
