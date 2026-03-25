# Projekt: Tarot App (Flask + HTMX)

## 1. Core Concept
- Webová aplikácia na výklad tarotových kariet.
- Žiadne zložité JS frameworky (len HTMX pre dynamiku).
- Backend: Flask (Python), WSGI: Gunicorn.

## 2. Business Logic (Constraints)
- uzivatel dostava aj vizualny zazitok
- Používateľ si vyberie 3 karty (Minulosť, Prítomnosť, Budúcnosť).
- Výklad generuje LLM Gemini API 
- Žiadna registrácia (Session-based).
- jedna stranka s vykladom
- dalsie stranky, o Tarote, vyklad jednotlivych kariet, nejaka karta o aplikacii
- miesto na google adssense, reklama pocas komunikacie s LLM

## 3. Tech Stack & Architecture
- **Frontend:** Server-Side Rendering (Jinja2) + Tailwind CSS.
- **Interaktivita:** HTMX (AJAX requests vracajú HTML fragmenty).
- **Data:** JSON súbor s definíciami 78 kariet (názov, archetyp).
- jednoducha konverzia na APP, Capacitor alebo PWA
- jazykove verzie stranky aj kariet.

## 4. UI/UX Flow
0. zameranie na vizualny zazitok
1. Landing page (Tlačidlo "Začať výklad").
2. miesanie kariet, rozdelenie balika na 2-3 kopky
3. Výber kariet (Klikateľné divy, HTMX swap po vybratí 3. karty).
4. Loading state (HTMX indicator).
5. Result page (Renderovaný výklad).


## 5. datovy model a logika
- trieda cards obsahuje balik tarotovych kariet id, meno, vyznam, vyznam pri obrateni, obrazok, 
- trieda balik obsahuje zoznam vsetkych kariet, ich poradie kariet z triedy cards, kazda karta je tam len raz, vratene otocenia, ma metody zamiesat a reset balika
- trieda card sa pouzije na tvorenie stranok na popis kariet a zobrazenie
- trieda deck uchovava aktualny balik, v procese vestenia a pouzije triedu cards na zobrazenie



