# Tokfm-oymd

## Instalacja
```bash
git clone https://github.com/kerszl/tokfm-oymd.git
cd tokfm-oymd.git
chmod +x tokfm-oymd
pip3 install --upgrade pip
pip3 install bs4
```

## Kopiowanie mp3 do czytelnej postaci (Z czasem ulepsze opis)
- Sprawdź gdzie są twoje podcasty z Tok-Fm (Zazwyczaj są w Android/data/fm.tokfm.android/files)
- Zgraj je sobie na dysk i dodaj odpowiednie sciezki w konfigu (Będzie to lepiej zrobione)
```python
tokfm-oymd.py fix_names
```
- podcasty będą zgrywane na twój dysk i będzie nadawana odpowiednia nazwa

