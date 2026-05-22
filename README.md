# News Agent – Agentic hírösszefoglaló projekt

**Minden szükséges lépést egy helyen** tartalmaz: modell, telepítés, futtatás, példák, tipikus hibák.

A projekt **lokális LLM-et** használ az **Ollama** futtatókörnyezeten keresztül (nincs felhős API-kulcs, teljesen privát, online működésre nincs szükség az LLM után).

---

## 0) Gyors indulás (TL;DR)

### Windows PowerShell

```powershell
# 1) Ollama + modell telepítése
ollama --version
ollama pull mistral-nemo:12b
ollama run mistral-nemo:12b

# 2) Python környezet létrehozása
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3) Futtatás alapértelmezett topic-kal
python main.py

# 3b) Futtatás egyedi topic-kal
python main.py --topic "ChatGPT"

# 4) Korábbi futás visszajátszása
python replay_snapshot.py data/snapshots/2026-05-13_09-30-05.json
```

### macOS / Linux (Bash)

```bash
# 1) Ollama + modell telepítése
ollama --version
ollama pull mistral-nemo:12b
ollama run mistral-nemo:12b

# 2) Python környezet létrehozása
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3) Futtatás alapértelmezett topic-kal
python main.py

# 3b) Futtatás egyedi topic-kal
python main.py --topic "ChatGPT"

# 4) Korábbi futás visszajátszása
python replay_snapshot.py data/snapshots/2026-05-13_09-30-05.json
```

---

## 1) Mi is ez a News Agent?

### A koncepció: egy virtuális újságírói csapat

Képzeld el, hogy egy **5 tagú újságírói csapatod** van, akik egy adott témáról szóló híreket feldolgoznak:

1. **🔍 Hírgyűjtő (SourceAgent)**
   - Az első tag naponta végigmegy több RSS-forrás- és letölt friss cikkeket
   - Leszűri a túl régi híreket (alapból 24 órás „lookback")
   - Kinyeri az egyes cikkek szövegét az interneten

2. **🎯 Szűrő (RelevanceAgent)**
   - A második tag megnézi az összes cikket és eldönti: *„Ez a topic-hoz kapcsolódik-e?"*
   - Gyorsan ellenőrzi, hogy a keresett szó szerepel-e
   - Ha nem, mesterséges intelligencia segítségével értékeli a relevanciát
   - Kidobja az értelmetlen cikkeket

3. **📦 Csoportosító (ClusterAgent)**
   - A harmadik tag csoportokat alkot: *„Melyik cikkek ugyanarról a dologról szólnak?"*
   - Szavak számbavételén alapuló hasonlóságot számít (Jaccard-index)
   - Ha két cikk elég hasonló, egy klaszterbe kerülnek

4. **🔗 Összevonó (ClusterMergeAgent)**
   - A negyedik tag átgondolja az LLM segítségével: *„Ezek a klaszterek valójában egy dolog?"*
   - Összeadhat kis klasztereket, ha tényleg ugyanazokról szólnak
   - Csökkenti a végső csoportok számát az átfedéseknek

5. **📝 Összefoglalózó (SummaryAgent)**
   - Az ötödik tag minden klaszterhez rövid szöveges összefoglalót készít
   - Az LLM írja meg az összefoglalót az összes cikk alapján
   - Az eredmény magyar nyelvű, csak a lényeg

### Miért lokális LLM?

- **Privátság**: A cikkek nem mennek fel felhőbe
- **Sebesség**: Nincs hálózati késleltetés az API-hoz
- **Költség**: Ingyenes, saját szerver van telepítve (Ollama)
- **Offline működés**: Internet után nem szükséges az LLM működéséhez (csak a cikkek letöltéséhez)

---

## 2) Rendszerkövetelmények

### Operációs rendszerek

- ✅ **Windows 10+ / 11** (PowerShell 5.1+)
- ✅ **macOS 10.15+** (Intel vagy Apple Silicon)
- ✅ **Linux** (Ubuntu 20.04+, Debian, CentOS, stb.)

### Hardware

- **RAM**: Minimum 4 GB, ajánlott 8+ GB (az LLM modell nagy memória-igényes)
- **CPU**: Modern processz (Intel Core i5+, AMD Ryzen 5+, vagy Apple Silicon)
- **GPU**: Opcionális, de ajánlott gyorsulásért (NVIDIA CUDA, AMD ROCm, macOS Metal)
- **Lemezterület**: ~6 GB a modellhez + 1 GB a Python-hoz

### Internet

- ✅ RSS-ek letöltéséhez szükséges
- ✅ Cikkek webhelyeiről való letöltéshez szükséges
- ❌ Az LLM műk után nem szükséges (már lokálisan fut)

---

## 3) Telepítés

### 3.1 Ollama telepítése

#### Windows

1. Menjél a https://ollama.ai oldalra
2. Kattints a **Download** gombra (Windows verzió)
3. Futtasd az telepítőt
4. Indítsd újra a terminalt vagy PowerShell-t
5. Ellenőrizd az installációt:

```powershell
ollama --version
# Kimenet: ollama version X.Y.Z
```

#### macOS

```bash
# Letöltés és telepítés egy parancsban
curl -fsSL https://ollama.ai/install.sh | sh

# Ellenőrzés
ollama --version
```

#### Linux (Ubuntu/Debian)

```bash
# Repository hozzáadása
curl -fsSL https://ollama.ai/install.sh | sh

# Ellenőrzés
ollama --version

# Daemon indítása (szükséges)
sudo systemctl start ollama
sudo systemctl enable ollama
```

### 3.2 Mistral-nemo modell letöltése

Ez az első futáskor **hosszú időt vesz igénybe** (10-30 perc, az internetsebesség függvényében). A modell ~4-6 GB.

#### Windows PowerShell

```powershell
# Modell letöltése (első futás hosszú!)
ollama pull mistral-nemo:12b

# Tesztelés
ollama run mistral-nemo:12b
# A parancssorba írható szöveg után Enter - az LLM válaszol
# Kilépés: Ctrl+C

# Ollama daemon indítása háttérben (szükséges a projekthez)
# Általában automatikus, de ha nem megy: Restart PowerShell
```

#### macOS / Linux

```bash
# Modell letöltése (első futás hosszú!)
ollama pull mistral-nemo:12b

# Tesztelés
ollama run mistral-nemo:12b
# A parancssorba írható szöveg után Enter - az LLM válaszol
# Kilépés: Ctrl+C

# Ollama daemon indítása háttérben (Linux esetén)
ollama serve &
```

### 3.3 Python 3.8+ telepítése

#### Windows

1. Menjél a https://www.python.org/downloads/ oldalra
2. Töltsd le a **Python 3.11** vagy **3.12** verzióját (Windows Installer)
3. **Fontos**: Az installer során jelöld be a `Add Python to PATH` opciót!
4. Ellenőrizd az installációt:

```powershell
python --version
# Kimenet: Python 3.X.Y
```

#### macOS

```bash
# Homebrew-val
brew install python@3.11

# vagy macports-zal
sudo port install python311

# Ellenőrzés
python3 --version
# Kimenet: Python 3.X.Y
```

#### Linux (Ubuntu/Debian)

```bash
# Letöltés és telepítés
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Ellenőrzés
python3 --version
# Kimenet: Python 3.X.Y
```

### 3.4 Projekt telepítése

#### Windows PowerShell

```powershell
# 1) Projekt mappájába lépés (ha még nem vagy ott)
cd C:\Users\andras.elod.lenart\PycharmProjects\news_agent

# 2) Python virtuális környezet (venv) létrehozása
python -m venv .venv

# 3) Virtuális környezet aktiválása
.venv\Scripts\Activate.ps1

# Sikeres aktiválás jele: a prompt elejében megjelenik a (.venv)

# 4) Dependencies telepítése
pip install --upgrade pip
pip install -r requirements.txt

# 5) Ellenőrzés (ha nem jelenik meg hiba, OK)
pip list
```

#### macOS / Linux

```bash
# 1) Projekt mappájába lépés
cd ~/PycharmProjects/news_agent

# 2) Python virtuális környezet (venv) létrehozása
python3 -m venv .venv

# 3) Virtuális környezet aktiválása
source .venv/bin/activate

# Sikeres aktiválás jele: a prompt elejében megjelenik a (.venv)

# 4) Dependencies telepítése
pip install --upgrade pip
pip install -r requirements.txt

# 5) Ellenőrzés (ha nem jelenik meg hiba, OK)
pip list
```

---

## 4) Futtatás

### Előfeltételek

Minden futtatás előtt ellenőrizd:

1. **Ollama daemon fut-e?**
   - Windows: Általában háttérben automatikusan
   - macOS/Linux: Kézi indítás szükséges (`ollama serve &`)

2. **Python venv aktív-e?**
   - Ha a prompt elején nem látod a `(.venv)` szöveget, aktíváld újra!

### 4.1 Alapértelmezett futtatás

A projekt a `config/sources.yaml` fájlban beállított topic-kal fog futni (alapértelmezetten "OpenAI").

#### Windows

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

#### macOS / Linux

```bash
source .venv/bin/activate
python main.py
```

**Kimenet**: Az összes RSS-forrásból (Telex, HVG) letöltött cikkek, szűrés, klaszterezés, majd végül az összefoglalók.

### 4.2 Egyedi topic-kal futtatás

Egy adott téma miatt futtathatod a pipeline-t (pl. "ChatGPT", "Szél energia", stb.).

#### Windows

```powershell
.venv\Scripts\Activate.ps1
python main.py --topic "ChatGPT"
python main.py --topic "Szél energia"
python main.py --topic "Tesla"
```

#### macOS / Linux

```bash
source .venv/bin/activate
python main.py --topic "ChatGPT"
python main.py --topic "Szél energia"
python main.py --topic "Tesla"
```

A `--topic` paraméter felülírja a `config/sources.yaml` beállítást ideiglenesen.

---

### 4.3 Több kulcsszavas figyelés

A rendszer támogatja több kulcsszó egyidejű figyelését, amelyek alapján a releváns hírek kiválasztása történik.

#### Példa konfiguráció

A `config/sources.yaml` fájlban több kulcsszót adhatsz meg:

```yaml
topic:
  queries:
    - "AI"
    - "Tesla"
    - "OpenAI"
    - "robotika"
    - "játékfejlesztés"
```

### 4.4 Snapshot-ból való visszajátszás (Replay)

A projekt minden futás után menti a pillanatképet (`snapshot`) a `data/snapshots/` mappába (timestamp-kel).

A replay lehetővé teszi, hogy **ismét futtatd az LLM-et az ugyanazon cikkeken**, ha például módosítottál a modell-prompton.

#### Windows

```powershell
.venv\Scripts\Activate.ps1
python replay_snapshot.py data/snapshots/2026-05-13_09-30-05.json
```

#### macOS / Linux

```bash
source .venv/bin/activate
python replay_snapshot.py data/snapshots/2026-05-13_09-30-05.json
```

**Mit csinál a replay?**
1. Betölti a mentett cikkeket (nem tölt le újabbakat az RSS-ből)
2. Újra futtatja a szűrést, klaszterezést, összefoglalást
3. Az LLM újra feldolgozza az adatokat (hasznos a teszteléshez)

### 4.5 A futás kimenetei

A projekt futása alatt látni fogsz:

```
[Pipeline] Starting run 2026-05-13_14-30-22
[Pipeline] Topic: ChatGPT

[SourceAgent] Starting RSS fetch | lookback_hours=24, max_per_source=10, max_total=50
[SourceAgent] Processing source 'Telex' | RSS entries=15
  ✓ 5 cikk letöltve
[SourceAgent] Processing source 'HVG' | RSS entries=12
  ✓ 4 cikk letöltve

[Pipeline] Relevance filtering finished | relevant_articles=6

[Pipeline] Initial clusters | count=3
...
[Pipeline] Generating summaries
[SummaryAgent] Starting summary
  • ChatGPT API új updates...
  • OpenAI bejelentette...
  
[Pipeline] Snapshot saved: data/snapshots/2026-05-13_14-30-22.json
```

---

## 5) Projekts tuktúra – Az ügynökök szót szerűen

```
news_agent/
├── main.py                    # Belépési pont
├── requirements.txt           # Python dependencies
├── README.md                  # Ez a dokumentáció
│
├── config/
│   └── sources.yaml           # RSS-ek, topic, fetch paraméterek
│
├── agents/                    # Az 5 ügynök
│   ├── source_agent.py        # 🔍 Hírgyűjtő: RSS letöltés
│   ├── relevance_agent.py     # 🎯 Szűrő: relevancia-ellenőrzés
│   ├── cluster_agent.py       # 📦 Csoportosító: hasonlóság alapú
│   ├── cluster_merge_agent.py # 🔗 Összevonó: LLM-es döntés
│   ├── summary_agent.py       # 📝 Összefoglalózó: szöveges summary
│   ├── ollama_client.py       # 🤖 Ollama kapcsolat
│   └── base_client.py         # 🔌 Interfész
│
├── pipelines/
│   └── news_pipeline.py       # Az 5 ügynök koordinációja
│
├── models/
│   └── article.py             # Cikk adatstruktúra
│
├── utils/
│   └── snapshot.py            # Pillanatkép mentése
│
├── data/
│   └── snapshots/             # Mentett futások
│
└── llm/                       # LLM konfigurációk
```

### Az ügynökök részletesen

#### 🔍 **SourceAgent** (Hírgyűjtő)

```python
# Mit csinál?
- RSS-eket letölt
- RSS-entryből kinyeri az URL-t
- Az URL-ről letölti a teljes cikk-szöveget
- Szűrzi az időpontot (max 24 órás)
- Tekst normalizálás (max 8000 karakter)
```

**Bemenete**: `sources.yaml` RSS-linkek
**Kimenete**: `Article` objektumok (title, content, source, published_at, url)

---

#### 🎯 **RelevanceAgent** (Szűrő)

```python
# Mit csinál?
1. Gyors ellenőrzés: van-e benne a keresett szó?
   - Ha igen → YES (relevanta)
   - Ha nem → LLM kérdezi meg

2. LLM döntés: "Összefügg-e az ezzel a témával?"
   - LLM: "YES" vagy "NO"
   - Kimenet: boolean
```

**Bemenete**: cikk szövege + topic
**Kimenete**: true/false

---

#### 📦 **ClusterAgent** (Csoportosító)

```python
# Mit csinál?
- Szavak számbavétele (tokenizálás)
- Jaccard-indexszel hasonlóság számítás
- Ha hasonlóság >= 0.55 → egy klaszterbe
- Egyébként új klaszter
```

**Bemenete**: `Article` lista
**Kimenete**: `list[list[Article]]` (beágyazott lista = klaszterek)

---

#### 🔗 **ClusterMergeAgent** (Összevonó)

```python
# Mit csinál?
- LLM-nek felteszi: "Ezek a klaszterek ugyanarról szólnak-e?"
- Ha LLM azt mondja: YES → összevonja őket
- Csökkenti a végső klaszterek számát
```

**Bemenete**: klaszterek + topic
**Kimenete**: kevesebb, de nagyobb klaszterek

---

#### 📝 **SummaryAgent** (Összefoglalózó)

```python
# Mit csinál?
- Egy klaszter összes cikkét feldolgozza
- LLM-nek adja őket: "Összefoglalójuka ezt!"
- LLM magyar nyelvű, 5 pontot maximum alatt összefoglalót készít
- Kimenet: szöveges summary
```

**Bemenete**: cikkek egy klaszterből + topic
**Kimenete**: magyar nyelvű szöveges összefoglalón

---

## 6) Konfigurálás (`config/sources.yaml`)

A `sources.yaml` fájl tartalmazza az összes beállítást. Szerkesztsd ezt, ha más témára vagy más RSS-ből szeretnél letölteni.

```yaml
# Topic beállítása (ez lesz a keresett szó)
topic:
  query: "OpenAI"        # ← Módosítsd ezt a kívánt témára!

# Fetch paraméterek
fetch:
  max_articles_per_source: 10     # Egy RSS-ből max hány cikk?
  max_total_articles: 50           # Összesen max hány cikk?
  lookback_hours: 24               # Legfeljebb hány órás cikkek?

# RSS-ek listája
sources:
  - name: Telex
    rss: https://telex.hu/rss
  - name: HVG
    rss: https://hvg.hu/rss
  # - name: AP News      # Kommentálva: nem fut
  #   rss: https://...
```

### Paraméterek magyarázata

| Paraméter | Alapérték | Leírás |
|-----------|-----------|--------|
| `topic.query` | "OpenAI" | A keresett téma szava vagy szavai |
| `max_articles_per_source` | 10 | Max cikk egyetlen RSS-ből |
| `max_total_articles` | 50 | Max összesen feldolgozandó cikk |
| `lookback_hours` | 24 | Hány óránál régebbit figyelmen kívül hagyjon |

### RSS-ek módosítása

#### Új forrás hozzáadása

```yaml
sources:
  - name: Portfolio
    rss: https://www.portfolio.hu/feed/rss
  - name: BBC News
    rss: https://feeds.bbci.co.uk/news/rss.xml
```

#### Forrás eltávolítása

Egyszerűen kommentáld ki az `#` jellel:

```yaml
# - name: HVG
#   rss: https://hvg.hu/rss
```

---

## 7) Snapshot és Replay

### Mi a Snapshot?

Minden futás után a projekt menti a **pillanatképet** (snapshot) egy JSON fájlként. Ez egy teljes archiváció a futásról:

- Letöltött cikkek
- Szűrt cikkek
- Klaszterek
- Összefoglalók
- LLM modell verzió
- Timestamp

### Hol tárolódik?

```
data/snapshots/
├── 2026-05-13_09-30-05.json
├── 2026-05-13_14-22-18.json
└── 2026-05-13_16-45-30.json
```

Az időbélyeg (YYYY-MM-DD_HH-MM-SS) a futás ideje.

### Miért hasznos a Snapshot?

1. **Reprodukálhatóság**: Ismét lefuthatsz ugyanazon az adaton
2. **Debugging**: Ha az LLM válasza furcsa, a snapshot lehetővé teszi a tesztelést
3. **Audit trail**: Megvan, hogy mit csinált a rendszer egy adott időpontban
4. **Offline tesztelés**: Nem kell újra RSS-t letölteni

### Replay használata

Egy korábbi snapshot újrafuttatása az összes ügynökkel:

```powershell
# Windows
python replay_snapshot.py data/snapshots/2026-05-13_14-22-18.json
```

```bash
# macOS/Linux
python replay_snapshot.py data/snapshots/2026-05-13_14-22-18.json
```

A replay **nem** tölti le az RSS-eket, csak feldolgozza az adatokat (szűrés, klaszterezés, összefoglalás).

---

## 8) Troubleshooting

### ❌ "Csatlakozási hiba: nem tudok az Ollama szerverre kapcsolódni"

**Okok**: Az Ollama daemon nem fut, vagy a port zárolva van.

**Megoldás Windows-on**:

```powershell
# 1) Ellenőrizd, hogy az Ollama fut-e
netstat -ano | findstr :11434
# Ha nem jelenik meg: az Ollama nem fut

# 2) Indítsd az Ollamát manuálisan
C:\Users\YOUR_USERNAME\AppData\Local\Programs\Ollama\ollama.exe serve

# 3) Nyíss másik PowerShell ablakot és próbáld újra
```

**Megoldás macOS/Linux-on**:

```bash
# 1) Ellenőrizz, hogy az Ollama fut
lsof -i :11434
# Ha nem jelenik meg: az Ollama nem fut

# 2) Indítsd az Ollamát
ollama serve &

# 3) Próbáld újra
python main.py
```

---

### ❌ "CUDA hiba / GPU nem működik"

**Okok**: NVIDIA GPU driver hiányzik vagy az Ollama nem találja meg a GPU-t.

**Megoldás**:

Az Ollama alapban CPU-módban fut. Ez is teljesen jó (csak lassabb).

Ha GPU-t szeretnél, győződj meg, hogy:
- NVIDIA GPU-d van
- Az Ollama Intel/AMD/Apple Metal támogatottá
- A GPU driverek frissek (GeForce Experience vagy AMD Adrenalin)

**De valójában**: A projekt működik CPU-n is, csak lassabb.

---

### ❌ "RSS hiba / nem tudok feladata betölteni"

**Okok**: Az RSS URL nem érvényes, vagy a weboldal letiltó.

**Megoldás**:

```powershell
# 1) Ellenőrizd az RSS URL-t a böngészőben
# Nyiss meg egy URL-t az sources.yaml-ból: https://telex.hu/rss

# 2) Ha semmit nem lát: az oldal letilthatja a bot-okat
# Próbálj másik RSS-t vagy a Telex helyett más forrátt

# 3) Ha privat RSS: Lehet, hogy autentikáció kell
# Egyelőre nem támogatott ez a projekt
```

---

### ❌ "LLM széörületes válaszokat ad / nem értem a kimenetét"

**Okok**: A modell gyengébben teljesít, vagy a prompt nem értelmezhető.

**Megoldás**:

1. **Próbálj más modellt**: A `mistral-nemo:12b` helyett:
   ```powershell
   ollama pull llama2:7b
   # Módosítsd: config/agents/base_client.py vagy modify_ollama_client.py
   ```

2. **Nézd meg a promptot**: `agents/relevance_agent.py`, `agents/summary_agent.py`
   - Talán a prompt nem tiszta vagy nem magyar

3. **Timeout-hiba?** Növeld a várakozási időt:
   ```python
   # agents/ollama_client.py: timeout=300 (vagy nagyobb)
   ```

---

### ❌ "TypeError / ModuleNotFoundError"

**Okok**: Hiányzó dependency vagy inkompatibilis Python verzió.

**Megoldás**:

```powershell
# Windows
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# Vagy újratelepítés
python -m pip install --force-reinstall -r requirements.txt
```

```bash
# macOS/Linux
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### ❌ "Snapshot mentés hibás / PermissionError"

**Okok**: A `data/snapshots/` mappa nem írható vagy teljesen megtelhet a lemez.

**Megoldás**:

```powershell
# Windows
# 1) Ellenőrizd a lemezterületet
Get-Volume

# 2) Ha nincs hely: töröld az réigi snapshot-okat
Remove-Item data/snapshots/*.json

# 3) Ellenőrizz, hogy a mappa létezik-e
Test-Path data/snapshots
```

```bash
# macOS/Linux
# 1) Ellenőrizd a lemezterületet
df -h

# 2) Ha nincs hely: töröld az réiki snapshot-okat
rm data/snapshots/*.json

# 3) Ellenőrizz, hogy a mappa létezik-e
test -d data/snapshots && echo "OK" || mkdir -p data/snapshots
```

---

### ❌ "Venv nem aktiválódik / (.venv) nem jelenik meg"

**Windows**:

```powershell
# 1) Ellenőrizd a venv-et
.venv\Scripts\Activate.ps1

# 2) Ha "nem fut" hiba: engedélyre lehet szükség
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3) Próbáld újra
.venv\Scripts\Activate.ps1
```

**macOS/Linux**:

```bash
# 1) Ellenőrizd a venv-et
source .venv/bin/activate

# 2) Ha nem működik, hozd létre újra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 9) Gyakran ismételt kérdések (FAQ)

### ❓ **Működik-e internet nélkül?**

**Részben**:
- ✅ Az LLM működik offline (helyi Ollama)
- ✅ A replay működik offline (mentett snapshot-ből)
- ❌ Az RSS letöltés internet nélkül nem működik
- ❌ A cikkek szövegének letöltése internete kell

**Egyszerűen**: Az LLM után jelölten, de az **adatgyűjtéshez** internet szükséges.

---

### ❓ **Megváltoztathatom a modellt?**

**Igen**!

```powershell
# Másik modell letöltése (például Llama 2)
ollama pull llama2:7b

# Konfigurálás módosítása
# agents/ollama_client.py: model_id() módosítá "llama2:7b"-re
```

**Modell-javaslatok**:
- `mistral-nemo:12b` - Jó egyensúly (sebesség vs minőség)
- `llama2:7b` - Gyorsabb, de gyengébb
- `mistral:7b` - Jó minőség, közepes sebesség
- `neural-chat` - Magyarország-optimalizált

---

### ❓ **Hány cikket lehet feldolgozni maximálisan?**

A `sources.yaml`-ban beállítható:
- `max_total_articles: 50` - Max 50 cikk egy futásban
- Ezt növelheted: 100, 200, vagy akár több

**De figyelem**: Több cikk = hosszabb futás az LLM-nél!

---

### ❓ **Bekapcsolhatom-e a GPU-t a gyorsulásért?**

Jelenleg az Ollama automatikusan használja a GPU-t, ha van. De ellenőrizheted:

```powershell
# GPU kihasználtság
ollama run mistral-nemo:12b "test"
# Watch a GPU memory-t (nvidia-smi windowson WDDM jelez)
```

---

### ❓ **Hogyan módosítom az LLM promptot?**

Az egyes prompts az ügynök-fájlokban vannak:

- **Relevancia prompt**: `agents/relevance_agent.py` - `_build_prompt()` módszer
- **Summary prompt**: `agents/summary_agent.py` - `_build_prompt()` módszer

Módosítsd a szöveget és próbáld újra (replay-val teszteld!)

---

### ❓ **Működik-e más RSS-ből (nem magyar)?**

**Igen!** Egyszerűen add hozzá a `sources.yaml`-hoz:

```yaml
sources:
  - name: BBC News
    rss: https://feeds.bbci.co.uk/news/rss.xml
  - name: Reuters
    rss: https://www.reutersagency.com/feed...
```

---

### ❓ **Milyen nyelvű az output?**

A `summary_agent.py` specifikusan **magyar**-ra van konfigurálva:

```python
# - The summary MUST be written in Hungarian.
```

De ezt módosíthatod más nyesevle (angol, német, stb.).

---

## 10) Sürgős segítség

### Nem működik semmi!

**Step-by-step:**

```powershell
# 1) Ollama renderint futtat?
ollama --version
ollama run mistral-nemo:12b

# 2) Python OK?
python --version

# 3) Venv OK?
.venv\Scripts\Activate.ps1

# 4) Dependencies OK?
pip list | grep feedparser
pip list | grep pydantic

# 5) Project OK?
python main.py --topic "test"
```

Ha valami nem működik, az 5. lépésben marad el, ott valami hiba van.

---

### Hova küldjem az error üzeneteket?

Ha hibára futtalálsz, tartalmazza:
1. **Teljes error üzenet** (outputot)
2. **Parancs, amit lefuttattál**
3. **OS és Python verzió** (`python --version`)
4. **Ollama verzió** (`ollama --version`)

---

## 11) Hasznos linkek

- 🦙 Ollama: https://ollama.ai
- 🐍 Python: https://www.python.org/downloads
- 📚 Mistral-nemo: https://mistral.ai/news/mistral-nemo/
- 📖 RSS szabvány: https://www.rssboard.org/

---

**Sikeresen telepítettél? Gratulálunk! 🎉**

Kezdj a `python main.py` paranccsal, és nézd meg az első futást!

