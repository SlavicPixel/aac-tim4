# AAC Tim 4

Aplikacija za evidenciju sastanaka s AAC, prilagodbu studiranja i praćenje studenata.

## Tehnologije

- **Backend:** Django (Python)
- **Frontend:** Django templating + Bootstrap 5 (preko crispy-forms)
- **Baza podataka:** PostgreSQL 17 (Docker)
- **Generiranje dokumenata:** WeasyPrint, ReportLab, openpyxl

## Preduvjeti

Prije pokretanja projekta provjeri da imaš instalirano:

- Python 3.10 ili noviji
- pip
- Docker i Docker Compose
- Git

## Pokretanje projekta

### 1. Kloniraj repozitorij

```bash
git clone https://github.com/SlavicPixel/aac-tim4.git
cd aac-tim4
```

### 2. Kreiraj i aktiviraj virtualno okruženje

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instaliraj dependencije

```bash
pip install -r requirements.txt
```

### 4. Pokreni PostgreSQL bazu

```bash
docker compose up -d
```

Provjeri da je kontejner gore:
```bash
docker ps
```

Trebaš vidjet nešto poput:

`CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS          PORTS                                         NAMES
b2199de1879f   postgres:17   "docker-entrypoint.s…"   13 minutes ago   Up 13 minutes   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp   aac_tim4_db`

### 5. Pokreni migracije

```bash
python manage.py migrate
```

### 6. Kreiraj superusera

```bash
python manage.py createsuperuser
```

Prati upute za unos username-a, email-a i lozinke.

### 7. Pokreni development server

```bash
python manage.py runserver
```

Aplikacija je dostupna na `http://localhost:8000`, a admin panel na `http://localhost:8000/admin`.

## Struktura projekta

```
aac-tim4/
├── aac_tim4/           # glavni Django projekt (settings, urls)
├── users/              # autentifikacija, User model, peer support
├── core/               # Student, Accommodation, Disability, Document
├── meetings/           # sastanci, kalendar
├── templates/          # globalni templates (base.html, partials)
├── static/             # globalni static fileovi
├── media/              # uploadane datoteke
├── docker-compose.yml  # PostgreSQL setup
├── requirements.txt    # Python dependencije
└── manage.py
```

## Korisne komande

**Zaustavljanje baze:**
```bash
docker compose down
```

**Zaustavljanje baze i brisanje podataka:**
```bash
docker compose down -v
```

**Pristup PostgreSQL-u kroz psql:**
```bash
docker exec -it aac_tim4_db psql -U aac_user -d aac_tim4
```

**Generiranje migracija nakon promjena u modelima:**
```bash
python manage.py makemigrations
python manage.py migrate
```
