# main.py
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import openai
import json
import os
import base64
import re
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURAZIONE
# ==========================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ERRORE: Non ho trovato la OPENAI_API_KEY nel file .env!")

openai.api_key = api_key

# Configurazione JWT
SECRET_KEY = os.getenv("SECRET_KEY", "chiave_segreta_default_cambiala_subito_12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Security
security = HTTPBearer()

# ==========================================
# 2. PERCORSI
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "utenti.json")
CRONOLOGIA_FILE = os.path.join(BASE_DIR, "cronologia_analisi.json")

# ==========================================
# 3. FASTAPI
# ==========================================

app = FastAPI(
    title="FiscoHunter AI Backend",
    description="Il motore di ragionamento fiscale.",
    version="2.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. FUNZIONI UTENTI
# ==========================================

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    users = load_users()
    user = users.get(email)
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# 5. MODELLI
# ==========================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nome: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfiloUtente(BaseModel):
    regime_fiscale: str
    reddito_complessivo: float
    aliquota_marginale: float

class RichiestaAnalisi(BaseModel):
    profilo: ProfiloUtente
    spesa_descrizione: str
    importo_spesa: float

class RispostaFiscale(BaseModel):
    obiettivo: str
    vantaggio_economico: str
    riferimento_normativo: str
    cavillo_strategia: str
    rischi_controlli: str
    azione_immediata: str

class AnalisiCompleta(BaseModel):
    profilo: ProfiloUtente
    spesa_descrizione: str
    importo_spesa: float
    obiettivo: str
    vantaggio_economico: str
    riferimento_normativo: str
    cavillo_strategia: str
    rischi_controlli: str
    azione_immediata: str

class DatiISEE(BaseModel):
    reddito_complessivo: float
    patrimonio_immobiliare: float
    patrimonio_mobiliare: float
    componenti_familiari: int

# ==========================================
# 6. DATABASE BONUS COMPLETO 
# ==========================================

BONUS_DATABASE = [
    # ==========================================
    # CATEGORIA: CASA ED ENERGIA
    # ==========================================
    {
        "id": "ecobonus_65_climatizzatori",
        "documento": "Ecobonus 65% per climatizzatori e pompe di calore. Detrazione del 65% delle spese sostenute per l'installazione di climatizzatori con pompa di calore ad alta efficienza energetica. Riferimento: Art. 1, commi 345-347, Legge 296/2006. Massimale: 100.000 euro. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "climatizzatore", "climatizzatori", "condizionatore", "condizionatori",
            "aria condizionata", "ariacondizionata", "ac", "split", "inverter",
            "pompa calore", "pompe calore", "pdc", "geotermico", "geotermia",
            "ecobonus", "efficiente", "efficienza", "energetico", "energia",
            "risparmio energetico", "riscaldamento", "raffrescamento", "termico",
            "calore", "65%", "sessantacinque", "detrazione 65", "bonus clima",
            "pompa di calore", "condizionatore inverter", "aria", "fresco", "freddo"
        ],
        "metadati": {"categoria": "casa", "aliquota": "65%"}
    },
    {
        "id": "ecobonus_65_infissi",
        "documento": "Ecobonus 50% per sostituzione infissi e serramenti. Detrazione del 50% per la sostituzione di finestre, portefinestre e schermature solari con prodotti che migliorano l'efficienza energetica. Riferimento: Art. 14, Legge 296/2006. Massimale: 60.000 euro. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "infissi", "finestre", "serramenti", " portefinestre", "vetrate",
            "doppi vetri", "triplo vetro", "isolamento termico", "isolamento acustico",
            "schermature solari", "tende", "persiane", "avvolgibili",
            "ecobonus infissi", "sostituzione finestre", "cambio infissi",
            "50%", "cinquanta", "detrazione 50", "bonus infissi",
            "efficiente", "efficienza energetica", "dispersione termica",
            "spifferi", "freddo", "caldo", "isolare", "coibentazione"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "ecobonus_65_caldaie",
        "documento": "Ecobonus 65% per sostituzione caldaie con caldaie a condensazione o sistemi ibridi. Detrazione del 65% per la sostituzione di impianti di climatizzazione invernale con caldaie a condensazione di classe A o sistemi ibridi pompa di calore + caldaia. Riferimento: Art. 1, comma 347, Legge 296/2006. Massimale: 30.000 euro.",
        "parole_chiave": [
            "caldaia", "caldaie", "caldaia a condensazione", "condensazione",
            "sistema ibrido", "ibrido", "riscaldamento", "termosifoni",
            "radiatori", "impianto termico", "sostituzione caldaia",
            "nuova caldaia", "caldaia a gas", "caldaia a pellet",
            "65%", "sessantacinque", "detrazione 65", "bonus caldaia",
            "efficiente", "efficienza energetica", "classe a",
            "inverno", "freddo", "riscaldare", "termico"
        ],
        "metadati": {"categoria": "casa", "aliquota": "65%"}
    },
    {
        "id": "ecobonus_50_pannelli_solari",
        "documento": "Ecobonus 50% per pannelli solari termici e fotovoltaici. Detrazione del 50% per l'installazione di pannelli solari termici per produzione acqua calda e pannelli fotovoltaici per produzione energia elettrica. Riferimento: Art. 16-bis, TUIR. Massimale: 96.000 euro. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "pannelli solari", "solare", "fotovoltaico", "fotovoltaici",
            "energia solare", "energia rinnovabile", "rinnovabile",
            "pannelli fotovoltaici", "impianto fotovoltaico", "solare termico",
            "acqua calda solare", "produzione energia", "autoproduzione",
            "inverter fotovoltaico", "batterie accumulo", "storage",
            "50%", "cinquanta", "detrazione 50", "bonus solare", "bonus fotovoltaico",
            "bolletta", "risparmio energetico", "sostenibile", "green",
            "tetto", "tetto", "copertura", "installazione pannelli"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "bonus_ristrutturazioni_50",
        "documento": "Bonus Ristrutturazioni 50% per interventi di manutenzione straordinaria, restauro, risanamento conservativo e ristrutturazione edilizia. Detrazione IRPEF del 50%. Riferimento: Art. 16-bis del TUIR. Massimale: 96.000 euro. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "ristrutturazione", "ristrutturare", "ristrutturo", "lavori casa", "lavori edili",
            "ristrutturazione edilizia", "ristrutturazione immobile", "ristrutturazione appartamento",
            "manutenzione", "manutenzione straordinaria", "straordinaria", "interventi", "intervento",
            "restauro", "risanamento", "conservativo", "ristrutturazione bagno", "ristrutturazione cucina",
            "ristrutturazione casa", "demolizione", "ricostruzione", "ampliamento", "ampliare",
            "muri", "pareti", "pavimenti", "impianti", "impianto elettrico", "impianto idraulico",
            "casa", "appartamento", "immobile", "abitazione", "villa", "attico",
            "bonus", "bonus casa", "ristrutturazioni", "50%", "cinquanta", "detrazione 50",
            "cila", "scia", "permesso costruire", "bonifico parlante", "lavori",
            "rinnovare", "rinnovamento", "ristrutturare casa", "ristrutturare appartamento",
            "bagno", "cucina", "soggiorno", "camera", "tetto", "facciata", "balcone"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "bonus_mobili_50",
        "documento": "Bonus Mobili ed Elettrodomestici 50% per l'acquisto di mobili nuovi e grandi elettrodomestici in classe energetica A o superiore. Detrazione IRPEF del 50%. Riferimento: Art. 16-bis, comma 3, del TUIR. Massimale: 5.000 euro. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "mobili", "mobile", "arredamento", "arredare", "arredo", "arredi",
            "divano", "letto", "armadio", "cucina", "tavolo", "sedie", "sedia",
            "comò", "cassettiera", "scrivania", "libreria", "scaffale",
            "mobili nuovi", "mobilio", "fornitura mobili",
            "elettrodomestici", "elettrodomestico", "frigorifero", "frigo", "lavatrice",
            "lavastoviglie", "forno", "forno elettrico", "piano cottura", "capa aspirante",
            "congelatore", "asciugatrice", "condizionatore portatile", "televisore", "tv",
            "classe energetica", "classe a", "a+", "a++", "a+++",
            "bonus mobili", "bonus elettrodomestici", "mobili e elettrodomestici",
            "50%", "cinquanta", "detrazione 50", "ristrutturazione", "in corso", "lavori",
            "comprare mobili", "acquisto mobili", "arredare casa", "arredare appartamento"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "sismabonus",
        "documento": "Sismabonus: detrazioni dal 50% all'85% per interventi di riduzione del rischio sismico. Detrazione IRPEF/IRES per interventi antisismici su edifici in zona sismica 1, 2 e 3. Riferimento: Art. 16-bis, TUIR. Massimale: 96.000 euro. Recupero: 5 o 10 quote annuali.",
        "parole_chiave": [
            "sismabonus", "antisismico", "antisismica", "rischio sismico", "terremoto",
            "zona sismica", "zona 1", "zona 2", "zona 3", "zona 4",
            "interventi antisismici", "miglioramento sismico", "adeguamento sismico",
            "rinforzo strutturale", "consolidamento", "struttura", "fondamenta",
            "ingegnere strutturista", "perizia sismica", "classificazione sismica",
            "detrazione sismica", "50%", "70%", "75%", "80%", "85%",
            "bonus sisma", "sicurezza sismica", "protezione terremoto",
            "edificio", "condominio", "palazzo", "stabile"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50-85%"}
    },
    {
        "id": "superbonus_65",
        "documento": "Superbonus 65% per condomini (ex 110%): detrazione del 65% per interventi di efficientamento energetico e antisismici su parti comuni di edifici condominiali. Riferimento: Art. 119, Decreto Rilancio. Massimale variabile per tipologia intervento.",
        "parole_chiave": [
            "superbonus", "super bonus", "110%", "sessantacinque", "65%",
            "condominio", "condominiale", "parti comuni", "spese condominiali",
            "cappotto termico", "isolamento a cappotto", "coibentazione",
            "efficientamento energetico", "trainante", "trainato",
            "intervento trainante", "intervento trainato", "cambio destinazione",
            "bonus condomini", "detrazione condominio", "lavori condominio",
            "amministratore", "assemblea condominiale", "delibera",
            "efficientamento", "energetico", "classe energetica", "ape"
        ],
        "metadati": {"categoria": "casa", "aliquota": "65%"}
    },
    {
        "id": "bonus_verde",
        "documento": "Bonus Verde: detrazione del 36% per sistemazione a verde di aree scoperte private. Detrazione IRPEF per interventi di giardinaggio, creazione di giardini, impianti di irrigazione, coperture a verde e verde pensile. Riferimento: Art. 1, comma 14, Legge 232/2016. Massimale: 5.000 euro.",
        "parole_chiave": [
            "bonus verde", "giardino", "giardinaggio", "verde", "aree verdi",
            "sistemazione a verde", "prato", "erba", "piante", "alberi",
            "siepi", "arbusti", "fiori", "aiuole", "verde pensile",
            "tetto verde", "copertura a verde", "irrigazione", "impianto irrigazione",
            "36%", "trentasei", "detrazione 36", "bonus giardino",
            "terrazzo", "balcone verde", "cortile", "area scoperta",
            "paesaggistico", "architettura del paesaggio", "green"
        ],
        "metadati": {"categoria": "casa", "aliquota": "36%"}
    },
    {
        "id": "bonus_facciate_90",
        "documento": "Bonus Facciate 90%: detrazione del 90% per interventi di recupero o restauro della facciata esterna di edifici. Riferimento: Art. 1, commi 219-223, Legge 160/2019. Massimale: non previsto limite specifico. Recupero: 10 quote annuali.",
        "parole_chiave": [
            "bonus facciate", "facciata", "facciate", "esterno edificio",
            "restauro facciata", "recupero facciata", "rifacimento facciata",
            "intonaco", "intonaci", "pittura esterna", "decoro",
            "90%", "novanta", "detrazione 90", "bonus esterno",
            "edificio", "palazzo", "condominio", "facciata esterna",
            "abbellimento", "decoro urbano", "riqualificazione",
            "ponteggi", "impalcature", "lavori esterni"
        ],
        "metadati": {"categoria": "casa", "aliquota": "90%"}
    },
    {
        "id": "bonus_acqua",
        "documento": "Bonus Acqua: detrazione del 50% per acquisto e installazione di dispositivi di riduzione del consumo di acqua. Detrazione per rubinetteria, soffioni doccia e colonne doccia ad alta efficienza idrica. Riferimento: Art. 1, comma 288, Legge 205/2017. Massimale: 1.000 euro per unità immobiliare.",
        "parole_chiave": [
            "bonus acqua", "rubinetteria", "rubinetto", "rubinetti",
            "soffione doccia", "doccia", "colonna doccia", "miscelatore",
            "riduzione consumo acqua", "risparmio idrico", "efficienza idrica",
            "acqua", "consumo acqua", "bolletta acqua", "idrico",
            "50%", "cinquanta", "detrazione 50", "bonus idrico",
            "bagno", "cucina", "installazione", "sostituzione rubinetti",
            "sostenibile", "ambiente", "ecologico", "green"
        ],
        "metadati": {"categoria": "casa", "aliquota": "50%"}
    },
    {
        "id": "bonus_barriere_architettoniche_75",
        "documento": "Bonus Barriere Architettoniche 75%: detrazione del 75% per eliminazione barriere architettoniche. Interventi per ascensori, montascale, piattaforme elevatrici, rampe, bagni accessibili. Riferimento: Art. 119-ter, Decreto Rilancio. Massimale: 50.000 euro.",
        "parole_chiave": [
            "barriere architettoniche", "accessibilità", "disabilità", "handicap",
            "ascensore", "montascale", "piattaforma elevatrice", "servoscala",
            "rampe", "scivoli", "bagno accessibile", "wc disabili",
            "eliminare barriere", "abbattimento barriere", "accessibile",
            "75%", "detrazione 75", "bonus barriere", "bonus accessibilità",
            "anziani", "mobilità ridotta", "sedia a rotelle", "carrozzina",
            "domotica", "automazione", "comandi vocali", "smart home disabili"
        ],
        "metadati": {"categoria": "casa", "aliquota": "75%"}
    },

    # ==========================================
    # CATEGORIA: SALUTE E BENESSERE
    # ==========================================
    {
        "id": "detrazioni_sanitarie_19",
        "documento": "Detrazioni spese sanitarie 19% per spese mediche, chirurgiche, specialistiche, diagnostiche e di laboratorio. Detrazione IRPEF del 19% sulla parte che eccede la franchigia di 129,11 euro. Riferimento: Art. 15, comma 1, lettera c), del TUIR.",
        "parole_chiave": [
            "medico", "medici", "visita medica", "visita specialistica", "specialista",
            "dottore", "dottoressa", "cura", "cure", "terapia", "terapie",
            "cardiologo", "dermatologo", "oculista", "ortopedico", "ginecologo",
            "pediatra", "dentista", "odontoiatra", "chirurgo", "chirurgia",
            "psicologo", "psicoterapeuta", "psichiatra", "neurologo", "fisiatri",
            "fisioterapista", "osteopata", "chiropratico", "logopedista",
            "ospedale", "clinica", "poliambulatorio", "ambulatorio", "laboratorio",
            "laboratorio analisi", "centro medico", "studio medico",
            "analisi", "esame", "esami", "radiografia", "rx", "tac", "risonanza",
            "mri", "ecografia", "eco", "mammografia", "pap test", "prelievo",
            "visita cardiologica", "visita dermatologica", "visita oculistica",
            "farmacia", "farmaci", "farmaco", "medicine", "medicinali", "medicinale",
            "prescrizione", "ricetta", "ricetta medica", "scontrino parlante",
            "salute", "sanitario", "sanità", "spese sanitarie", "spese mediche",
            "malattia", "patologia", "19%", "diciannove", "detrazione 19",
            "detrazione sanitaria", "franchigia", "129,11", "codice fiscale",
            "dentista", "oculista", "cardiologo", "visita", "controllo", "check-up"
        ],
        "metadati": {"categoria": "salute", "aliquota": "19%"}
    },
    {
        "id": "bonus_psicologo",
        "documento": "Bonus Psicologo: contributo fino a 1.500 euro per sedute di supporto psicologico. L'importo varia in base all'ISEE (fino a 1.500€ per ISEE sotto 15.000€, fino a 600€ per ISEE 15.000-30.000€, fino a 300€ per ISEE 30.000-50.000€). Riferimento: Art. 1, comma 12, Legge 234/2021.",
        "parole_chiave": [
            "psicologo", "psicoterapeuta", "psicoterapia", "supporto psicologico",
            "salute mentale", "ansia", "depressione", "terapia", "sedute",
            "bonus psicologo", "1500", "600", "300", "benessere", "mente",
            "psicologo", "terapia", "consulenza", "supporto emotivo",
            "stress", "burnout", "disturbi alimentari", "dipendenze",
            "psicologia", "psichiatra", "salute psicologica", "mentale"
        ],
        "metadati": {"categoria": "salute", "massimale": 1500}
    },
    {
        "id": "detrazioni_spese_veterinarie",
        "documento": "Detrazioni spese veterinarie 19% per spese sanitarie per animali domestici. Detrazione IRPEF del 19% per spese veterinarie sostenute per cani, gatti e altri animali domestici. Riferimento: Art. 15, comma 1, lettera c-quater), TUIR. Franchigia: 129,11 euro annui.",
        "parole_chiave": [
            "veterinario", "veterinaria", "spese veterinarie", "animale domestico",
            "cane", "gatto", "cucciolo", "cagnolino", "gattino", "pet",
            "visita veterinaria", "vaccino", "vaccinazione", "sterilizzazione",
            "castrazione", "microchip", "chip animale", "cura animale",
            "19%", "detrazione 19", "detrazione veterinaria", "bonus animali",
            "clinica veterinaria", "ospedale veterinario", "farmacia veterinaria",
            "animali", "domestico", "compagnia", "cure animali"
        ],
        "metadati": {"categoria": "salute", "aliquota": "19%"}
    },

    # ==========================================
    # CATEGORIA: FAMIGLIA E ISTRUZIONE
    # ==========================================
    {
        "id": "bonus_nido_3000",
        "documento": "Bonus Nido: rimborso fino a 3.000 euro annui per rette di asili nido pubblici e privati o per servizi di baby-sitting. Riferimento: Art. 1, comma 355, Legge 232/2016. Requisiti: domanda all'INPS entro il 31 dicembre, ISEE non superiore a 40.000 euro.",
        "parole_chiave": [
            "asilo nido", "nido", "asilo", "nido infanzia", "nido d'infanzia",
            "asilo nido pubblico", "asilo nido privato", "nido privato",
            "scuola infanzia", "scuola materna", "materna",
            "bambini", "bambino", "bambina", "figli", "figlio", "figlia",
            "neonati", "neonato", "piccoli", "infanzia",
            "baby sitting", "babysitter", "baby sitter", "tata", "aiuto bambini",
            "assistenza bambini", "cura bambini",
            "retta", "retta asilo", "retta nido", "pagamento asilo", "contributo",
            "bonus nido", "bonus asilo", "rimborso nido", "contributo nido",
            "3000", "tremila", "3.000 euro", "inps", "domanda inps",
            "isee", "40000", "isee 40000", "isee 25000", "figli piccoli",
            "ludoteca", "centro bambini", "assistenza infanzia"
        ],
        "metadati": {"categoria": "famiglia", "massimale": 3000}
    },
    {
        "id": "assegno_unico",
        "documento": "Assegno Unico e Universale per i figli a carico: prestazione mensile per tutti i figli minorenni, maggiorenni fino a 21 anni (con specifiche condizioni) e figli con disabilità. L'importo varia in base all'ISEE. Riferimento: D.Lgs. 230/2021.",
        "parole_chiave": [
            "assegno unico", "assegno universale", "figli a carico", "figli minorenni",
            "figli maggiorenni", "famiglia", "genitori", "mensile", "inps",
            "isee", "bonus figli", "aiuto famiglia", "nucleo familiare",
            "figli", "bambini", "adozione", "disabilità",
            "genitorialità", "crescita figli", "mantenimento figli",
            "contributo mensile", "prestazione familiare"
        ],
        "metadati": {"categoria": "famiglia", "tipo": "mensile"}
    },
    {
        "id": "istruzione_19",
        "documento": "Detrazioni spese istruzione 19% per spese di frequenza di scuole dell'infanzia, primarie, secondarie e universitarie. Riferimento: Art. 15, comma 1, lettera g), del TUIR. Massimale: 786 euro per alunno/studente.",
        "parole_chiave": [
            "scuola", "scuole", "asilo", "materna", "infanzia", "elementari",
            "primaria", "medie", "secondaria", "superiori", "liceo",
            "istituto", "collegio", "convitto",
            "università", "universitario", "ateneo", "facoltà", "corso laurea",
            "laurea", "laurea triennale", "laurea magistrale", "dottorato",
            "master", "master universitario", "post laurea",
            "studente", "studenti", "alunno", "alunni", "scolarizzazione",
            "iscrizione", "immatricolazione", "frequenza",
            "retta", "retta scolastica", "retta universitaria", "tasse universitarie",
            "contributo", "contributi", "tassa iscrizione",
            "libri", "libri di testo", "materiale didattico",
            "mensa", "trasporto scolastico", "servizi scolastici",
            "19%", "diciannove", "detrazione 19", "detrazione istruzione",
            "786", "massimale", "limite", "figli", "figlio", "figlia", "a carico",
            "famiglia", "formazione", "educazione", "corsi", "formazione professionale"
        ],
        "metadati": {"categoria": "famiglia", "aliquota": "19%"}
    },
    {
        "id": "bonus_cultura_18app",
        "documento": "Bonus Cultura (18app / Carta della Cultura): contributo di 500 euro per giovani che compiono 18 anni per acquisto di libri, biglietti teatro, cinema, musei, concerti, corsi di formazione. Riferimento: Art. 1, comma 956, Legge 208/2015.",
        "parole_chiave": [
            "bonus cultura", "18app", "carta cultura", "carta del merito",
            "giovani", "18 anni", "neomaggiorenni", "cultura",
            "libri", "libreria", "lettura", "teatro", "cinema", "film",
            "musei", "mostre", "concerti", "musica", "spettacoli",
            "formazione", "corsi", "lingue", "inglese", "francese",
            "500", "cinquecento", "bonus giovani", "bonus 18",
            "crescita culturale", "istruzione", "apprendimento"
        ],
        "metadati": {"categoria": "famiglia", "massimale": 500}
    },
    {
        "id": "bonus_trasporti",
        "documento": "Bonus Trasporti: contributo per abbonamenti mezzi pubblici. Detrazione o rimborso per abbonamenti annuali a mezzi di trasporto pubblico locale e regionale. Riferimento: varie leggi di bilancio annuali.",
        "parole_chiave": [
            "bonus trasporti", "mezzi pubblici", "trasporto pubblico", "abbonamento",
            "abbonamento annuale", "abbonamento mensile", "bus", "autobus",
            "metro", "metropolitana", "tram", "treno", "ferrovia",
            "biglietto", "titolo di viaggio", "trasporti", "mobilità",
            "pendolare", "commuting", "spostamenti", "lavoro casa",
            "sostenibilità", "ambiente", "green mobility", "bike sharing",
            "monopattino", "bicicletta", "mobilità sostenibile"
        ],
        "metadati": {"categoria": "famiglia", "tipo": "contributo"}
    },

    # ==========================================
    # CATEGORIA: LAVORO E REDDITO
    # ==========================================
    {
        "id": "trattamento_integrativo",
        "documento": "Trattamento integrativo (ex Bonus 80€ / Bonus Renzi): importo fino a 1.200 euro annui (100€ al mese) per redditi da lavoro dipendente fino a 15.000 euro, e con specifiche condizioni fino a 28.000 euro. Riferimento: Art. 13, comma 1-bis, TUIR.",
        "parole_chiave": [
            "bonus 80", "bonus renzi", "trattamento integrativo", "100 euro", "1200",
            "lavoro dipendente", "dipendente", "busta paga", "stipendio", "salario",
            "15000", "28000", "reddito basso", "integrazione", "ex bonus",
            "lavoratore", "impiegato", "operaio", "contratto", "ccnl"
        ],
        "metadati": {"categoria": "lavoro", "massimale": 1200}
    },
    {
        "id": "regime_forfettario",
        "documento": "Regime Forfettario: tassazione agevolata al 5% (primi 5 anni) o 15% per piccoli imprenditori e professionisti con ricavi sotto 85.000 euro. Esenzione IVA, esenzione IRAP, esenzione ritenuta d'acconto. Riferimento: Art. 1, commi 54-89, Legge 190/2014.",
        "parole_chiave": [
            "regime forfettario", "forfettario", "partita iva forfettaria", "forfettari",
            "5%", "quindici", "15%", "tassazione agevolata", "flat tax",
            "piccoli imprenditori", "professionisti", "freelance", "libero professionista",
            "85000", "ricavi", "fatturato", "partita iva", "p.iva",
            "esenzione iva", "no iva", "senza iva", "esenzione irap",
            "start up", "nuova attività", "apertura partita iva",
            "coefficiente di redditività", "reddito forfettario", "forfait"
        ],
        "metadati": {"categoria": "lavoro", "aliquota": "5-15%"}
    },
    {
        "id": "regime_impatriati",
        "documento": "Regime Impatriati (Rientro Cervelli): esenzione dal 50% al 90% del reddito da lavoro per lavoratori che trasferiscono la residenza in Italia. Riferimento: Art. 16, comma 1-bis, TUIR. Requisiti: non aver risieduto in Italia nei 3 anni precedenti.",
        "parole_chiave": [
            "impatriati", "rientro cervelli", "rientro in italia", "lavoratori estero",
            "trasferimento", "residenza", "estero", "lavoro estero",
            "esenzione fiscale", "50%", "70%", "90%", "tax break",
            "brain drain", "fuga cervelli", "rientro", "espatriati",
            "lavoratore qualificato", "alta specializzazione", "ricercatore",
            "università", "centri ricerca", "innovazione", "tecnologia"
        ],
        "metadati": {"categoria": "lavoro", "aliquota": "50-90%"}
    },
    {
        "id": "flat_tax_pensionati_esteri",
        "documento": "Flat Tax 7% per pensionati esteri: aliquota IRPEF del 7% per pensionati che trasferiscono la residenza in comuni sotto 20.000 abitanti del Mezzogiorno. Riferimento: Art. 24-bis, TUIR.",
        "parole_chiave": [
            "pensionati esteri", "flat tax 7%", "pensionati", "pensione estera",
            "mezzogiorno", "sud italia", "sicilia", "calabria", "sardegna",
            "basilicata", "campania", "puglia", "molise", "abruzzo",
            "20000 abitanti", "piccoli comuni", "borghi", "paesi",
            "7%", "sette", "aliquota ridotta", "pensione", "quiescenza",
            "trasferimento", "residenza", "estero", "pensionato straniero"
        ],
        "metadati": {"categoria": "lavoro", "aliquota": "7%"}
    },

    # ==========================================
    # CATEGORIA: AUTO E MOBILITÀ
    # ==========================================
    {
        "id": "bonus_auto_azienda",
        "documento": "Auto aziendale: deducibilità del 20% per autovetture concesse in uso promiscuo ai dipendenti. Riferimento: Art. 164, comma 1, lettera c), del TUIR. Per veicoli elettrici o ibridi plug-in la deducibilità sale al 30%.",
        "parole_chiave": [
            "auto", "automobile", "autovettura", "veicolo", "macchina", "vettura",
            "autovetture", "automezzi", "mezzo aziendale",
            "azienda", "aziendale", "impresa", "ditta", "società", "business",
            "uso promiscuo", "uso aziendale", "uso lavoro",
            "dipendente", "dipendenti", "lavoratore", "lavoratori", "collaboratore",
            "assegnazione", "concessione", "uso dipendente",
            "deducibile", "deduzione", "dedurre", "20%", "venti", "trenta", "30%",
            "costo acquisto", "spese esercizio", "spese auto",
            "elettrico", "elettrica", "ibrido", "ibrida", "plug-in", "plug in",
            "benzina", "diesel", "gasolio", "metano", "gpl",
            "carburante", "manutenzione", "assicurazione", "bollo",
            "rifornimento", "auto aziendale", "auto lavoro", "macchina lavoro",
            "veicolo aziendale", "flotta", "leasing auto", "noleggio auto"
        ],
        "metadati": {"categoria": "auto", "aliquota": "20-30%"}
    },
    {
        "id": "ecobonus_auto",
        "documento": "Ecobonus Auto: incentivo per acquisto veicoli a basse emissioni. Contributo statale per auto elettriche, ibride, metano e GPL. Riferimento: Decreto MISE annuale. Importi variabili da 2.000€ a 6.000€ in base alle emissioni CO2.",
        "parole_chiave": [
            "ecobonus auto", "bonus auto", "incentivo auto", "auto elettrica",
            "auto ibrida", "auto metano", "auto gpl", "veicolo elettrico",
            "emissioni", "co2", "basse emissioni", "zero emissioni",
            "tesla", "nissan leaf", "renault zoe", "fiat 500 elettrica",
            "ibrido plug-in", "full hybrid", "mild hybrid",
            "2000", "4000", "6000", "incentivo statale", "contributo acquisto",
            "auto nuova", "acquisto auto", "rottamazione", "permuta",
            "sostenibilità", "ambiente", "green", "mobilità sostenibile"
        ],
        "metadati": {"categoria": "auto", "massimale": 6000}
    },
    {
        "id": "bonus_colonnine_ricarica",
        "documento": "Bonus Colonnine Ricarica: detrazione del 50% per installazione infrastrutture di ricarica per veicoli elettrici. Riferimento: Art. 1, comma 1044, Legge 160/2019. Massimale: 8.000 euro per unità immobiliare.",
        "parole_chiave": [
            "colonnine ricarica", "ricarica elettrica", "wallbox", "presa elettrica auto",
            "infrastruttura ricarica", "installazione colonnina", "ricarica casa",
            "auto elettrica", "veicolo elettrico", "ev charging",
            "50%", "detrazione 50", "bonus colonnina", "bonus ricarica",
            "8000", "ottomila", "massimale", "garage", "box auto",
            "condominio", "parti comuni", "parcheggio", "installazione",
            "elettrico", "sostenibile", "green mobility"
        ],
        "metadati": {"categoria": "auto", "aliquota": "50%"}
    },

    # ==========================================
    # CATEGORIA: INVESTIMENTI E RISPARMIO
    # ==========================================
    {
        "id": "fondo_pensione",
        "documento": "Fondi Pensione Complementari: versamenti a fondi pensione sono deducibili dal reddito imponibile fino a 5.164,57 euro annui. Riferimento: Art. 10, comma 1, lettera e), del TUIR.",
        "parole_chiave": [
            "pensione", "fondo pensione", "fondi pensione", "previdenza", "previdenziale",
            "pensione complementare", "pensione integrativa", "seconda pensione",
            "versamenti", "versamento", "contributo", "contributi", "contributo previdenziale",
            "accantonamento", "accumulo", "piano pensionistico",
            "deducibile", "deduzione", "dedurre", "reddito imponibile", "imponibile",
            "abbattere imponibile", "ridurre imponibile",
            "fondo negoziale", "fondo aperto", "fondo chiuso", "previdenza integrativa",
            "investimento", "investire", "risparmio", "risparmiare", "accumulo capitale",
            "vantaggio fiscale", "risparmio fiscale", "aliquota", "irpef", "tasse",
            "detrazione", "beneficio fiscale",
            "5164", "5.164", "5164,57", "massimale", "limite",
            "esempio", "calcolo", "simulazione", "quanto risparmio",
            "piano accumulo", "pianificazione", "futuro", "pensionamento",
            "complementare", "integrativa", "secondo pilastro"
        ],
        "metadati": {"categoria": "investimenti", "massimale": 5164.57}
    },
    {
        "id": "patent_box",
        "documento": "Patent Box (Regime Brevetti): tassazione agevolata al 50% sui redditi derivanti da brevetti, marchi e software. Riferimento: Art. 9, Decreto 147/2015. Beneficio: esclusione dal 50% del reddito derivante da proprietà intellettuale.",
        "parole_chiave": [
            "patent box", "regime brevetti", "brevetti", "marchi", "software",
            "proprietà intellettuale", "ip", "innovazione", "ricerca",
            "sviluppo", "r&s", "tecnologia", "invenzione",
            "50%", "esclusione", "tassazione agevolata", "agevolazione",
            "royalties", "licenze", "licenza d'uso", "trasferimento tecnologia",
            "startup innovativa", "pmi innovative", "centri ricerca",
            "università", "spin-off", "brevetto europeo", "brevetto internazionale"
        ],
        "metadati": {"categoria": "investimenti", "aliquota": "50%"}
    },
    {
        "id": "ace_aiuto_crescita_economica",
        "documento": "ACE (Aiuto alla Crescita Economica): deduzione dal reddito IRES del rendimento nozionale del capitale proprio. Riferimento: Art. 1, commi 157-163, Legge 208/2010. Aliquota nozionale: 1,2%.",
        "parole_chiave": [
            "ace", "aiuto crescita economica", "capitale proprio", "patrimonio netto",
            "rendimento nozionale", "1,2%", "deduzione ires", "società",
            "spa", "srl", "società per azioni", "società responsabilità limitata",
            "capitalizzazione", "aumento capitale", "riserve", "utili non distribuiti",
            "ires", "tassazione società", "agevolazione imprese",
            "crescita", "sviluppo", "investimenti", "patrimonializzazione"
        ],
        "metadati": {"categoria": "investimenti", "aliquota": "1,2%"}
    },

    # ==========================================
    # CATEGORIA: IMPRESE E LAVORO AUTONOMO
    # ==========================================
    {
        "id": "credito_imposta_formazione_4",
        "documento": "Credito d'imposta formazione 4.0: credito del 50-70% per spese di formazione del personale su tecnologie digitali e Industria 4.0. Riferimento: Art. 1, commi 46-50, Legge 160/2019.",
        "parole_chiave": [
            "credito imposta", "formazione 4.0", "industria 4.0", "digitale",
            "formazione personale", "corsi formazione", "upskilling", "reskilling",
            "tecnologie digitali", "automazione", "robotica", "intelligenza artificiale",
            "big data", "cloud computing", "cybersecurity", "iot",
            "50%", "70%", "credito d'imposta", "agevolazione formazione",
            "dipendenti", "personale", "risorse umane", "hr",
            "competenze", "skill", "digital transformation", "innovazione"
        ],
        "metadati": {"categoria": "imprese", "aliquota": "50-70%"}
    },
    {
        "id": "credito_imposta_ricerca_sviluppo",
        "documento": "Credito d'imposta ricerca e sviluppo: credito del 20% per spese in ricerca di base, ricerca industriale e sviluppo sperimentale. Riferimento: Art. 3, Decreto 145/2013. Massimale: 5 milioni euro annui.",
        "parole_chiave": [
            "credito imposta", "ricerca sviluppo", "r&s", "rnd", "ricerca",
            "sviluppo", "innovazione", "brevetti", "prototipi", "sperimentazione",
            "20%", "credito d'imposta", "agevolazione ricerca", "incentivo",
            "università", "centri ricerca", "laboratori", "scienza",
            "tecnologia", "scientifica", "sperimentale", "industriale",
            "5 milioni", "massimale", "spese ricerca", "personale ricerca",
            "startup innovativa", "pmi innovative", "tecnologia avanzata"
        ],
        "metadati": {"categoria": "imprese", "aliquota": "20%"}
    },
    {
        "id": "bonus_assunzioni",
        "documento": "Bonus Assunzioni: sgravi contributivi per assunzione di giovani under 36, donne svantaggiate, disoccupati di lunga durata. Riferimento: varie leggi di bilancio annuali. Sgravio: fino al 100% dei contributi INPS.",
        "parole_chiave": [
            "bonus assunzioni", "sgravi contributivi", "assunzioni", "assumere",
            "giovani", "under 36", "donne", "disoccupati", "lunga durata",
            "contributi inps", "esenzione contributi", "sgravio", "incentivo assunzione",
            "100%", "contributi", "contratto lavoro", "assunzione",
            "datore lavoro", "azienda", "impresa", "occupazione",
            "lavoro", "impiego", "assunzione giovane", "prima assunzione",
            "incentivo", "agevolazione", "politiche attive", "centro impiego"
        ],
        "metadati": {"categoria": "imprese", "aliquota": "100%"}
    },
    {
        "id": "bonus_sud_credito_imposta",
        "documento": "Bonus Sud (Credito d'imposta Mezzogiorno): credito d'imposta per investimenti in beni strumentali nelle regioni del Mezzogiorno. Riferimento: Art. 1, commi 1-31, Legge 160/2019. Aliquote: 45-65% in base alla dimensione impresa e zona.",
        "parole_chiave": [
            "bonus sud", "mezzogiorno", "sud italia", "credito imposta mezzogiorno",
            "investimenti", "beni strumentali", "macchinari", "attrezzature",
            "45%", "65%", "credito d'imposta", "agevolazione sud",
            "sicilia", "calabria", "sardegna", "campania", "puglia",
            "basilicata", "molise", "abruzzo", "zone svantaggiate",
            "sviluppo territoriale", "coesione", "investimento produttivo",
            "impresa", "industria", "produzione", "capacità produttiva"
        ],
        "metadati": {"categoria": "imprese", "aliquota": "45-65%"}
    },
    {
        "id": "zes_zone_economiche_speciali",
        "documento": "ZES (Zone Economiche Speciali): crediti d'imposta e semplificazioni per imprese che investono in specifiche aree del Mezzogiorno. Riferimento: Art. 1, commi 158-164, Legge 208/2015.",
        "parole_chiave": [
            "zes", "zone economiche speciali", "mezzogiorno", "aree speciali",
            "credito imposta", "semplificazioni", "burocrazia", "investimenti",
            "sud italia", "sviluppo", "occupazione", "impresa",
            "agevolazioni", "incentivi", "zone franche", "porti",
            "logistica", "infrastrutture", "aree industriali", "parchi tecnologici"
        ],
        "metadati": {"categoria": "imprese", "tipo": "credito imposta"}
    },

    # ==========================================
    # CATEGORIA: CASA - MUTUO E LOCAZIONE
    # ==========================================
    {
        "id": "detrazioni_interessi_mutuo",
        "documento": "Detrazioni interessi mutuo prima casa: detrazione del 19% sugli interessi passivi del mutuo ipotecario per acquisto abitazione principale. Riferimento: Art. 15, comma 1, lettera b), TUIR. Massimale: 4.000 euro annui.",
        "parole_chiave": [
            "mutuo", "mutuo casa", "mutuo ipotecario", "interessi mutuo",
            "interessi passivi", "prima casa", "abitazione principale",
            "acquisto casa", "comprare casa", "mutuo acquisto",
            "19%", "detrazione 19", "detrazione interessi", "bonus mutuo",
            "4000", "quattromila", "massimale", "banca", "prestito",
            "ipoteca", "garanzia", "rata mutuo", "piano ammortamento",
            "surroga", "sostituzione mutuo", "mutuo verde", "mutuo giovane"
        ],
        "metadati": {"categoria": "casa", "aliquota": "19%"}
    },
    {
        "id": "detrazioni_canoni_locazione",
        "documento": "Detrazioni canoni di locazione: detrazione IRPEF per canoni di affitto di abitazione principale. Importi variabili in base al reddito (da 300€ a 2.000€ annui). Riferimento: Art. 16, TUIR.",
        "parole_chiave": [
            "locazione", "affitto", "canone", "canone affitto", "affittuario",
            "locatario", "inquilino", "appartamento in affitto", "casa in affitto",
            "detrazione affitto", "bonus affitto", "detrazione locazione",
            "300", "2000", "detrazione", "agevolazione", "reddito basso",
            "studenti fuori sede", "lavoratori trasferta", "giovani",
            "contratto affitto", "contratto locazione", "4+4", "3+2",
            "cedolare secca", "registrazione contratto"
        ],
        "metadati": {"categoria": "casa", "massimale": 2000}
    },
    {
        "id": "bonus_prima_casa_under36",
        "documento": "Bonus Prima Casa Under 36: esenzione da imposte di registro, ipotecaria e catastale per acquisto prima casa da parte di giovani under 36. Riferimento: Art. 1, comma 59, Legge 234/2021.",
        "parole_chiave": [
            "bonus prima casa", "under 36", "giovani", "prima casa",
            "esenzione imposte", "imposta registro", "imposta ipotecaria", "imposta catastale",
            "acquisto casa", "comprare casa", "giovani under 36",
            "agevolazioni giovani", "prima abitazione", "residenza",
            "36 anni", "giovani coppie", "famiglie giovani",
            "mutuo prima casa", "finanziamento giovani", "consap"
        ],
        "metadati": {"categoria": "casa", "tipo": "esenzione"}
    },

    # ==========================================
    # CATEGORIA: WELFARE E FRINGE BENEFITS
    # ==========================================
    {
        "id": "welfare_aziendale",
        "documento": "Welfare Aziendale: esenzione fiscale per prestazioni di welfare erogate ai dipendenti (buoni spesa, rimborsi scolastici, assistenza sanitaria). Riferimento: Art. 51, comma 3, TUIR. Limite esenzione: 3.000 euro annui (1.500€ con figli).",
        "parole_chiave": [
            "welfare aziendale", "fringe benefits", "benefit", "benefici",
            "buoni spesa", "buoni acquisto", "voucher", "ticket",
            "rimborsi scolastici", "assistenza sanitaria", "assicurazione sanitaria",
            "3000", "1500", "esenzione", "non tassato", "detassato",
            "dipendenti", "lavoratori", "azienda", "datore lavoro",
            "conciliazione vita-lavoro", "famiglia", "figli", "istruzione",
            "palestra", "viaggi", "tempo libero", "cultura"
        ],
        "metadati": {"categoria": "lavoro", "massimale": 3000}
    },
    {
        "id": "buoni_pasto_ticket",
        "documento": "Buoni Pasto e Ticket Restaurant: esenzione fiscale fino a 8 euro giornalieri per buoni pasto elettronici e 5,29€ per ticket cartacei. Riferimento: Art. 51, comma 2, lettera c), TUIR.",
        "parole_chiave": [
            "buoni pasto", "ticket restaurant", "ticket", "pasto", "mensa",
            "8 euro", "5,29", "esenzione", "non tassato", "detassato",
            "dipendenti", "lavoratori", "pranzo", "cibo", "alimentazione",
            "elettronici", "cartacei", "giornaliero", "feriale",
            "benefit", "fringe benefit", "welfare", "azienda"
        ],
        "metadati": {"categoria": "lavoro", "massimale": 8}
    },
    {
        "id": "smart_working_home_office",
        "documento": "Smart Working e Home Office: deducibilità spese per lavoro da casa (utenze, internet, attrezzatura). Riferimento: Art. 51, TUIR e accordi sindacali. Rimborso forfettario: 2,58€ giornalieri.",
        "parole_chiave": [
            "smart working", "lavoro agile", "home office", "lavoro da casa",
            "telelavoro", "remoto", "da remoto", "lavoro remoto",
            "utenze", "internet", "wifi", "attrezzatura", "computer",
            "2,58", "rimborso", "deducibile", "spese lavoro",
            "dipendenti", "azienda", "accordo smart working",
            "produttività", "flessibilità", "work life balance"
        ],
        "metadati": {"categoria": "lavoro", "massimale": 2.58}
    },
    {
        "id": "personale_domestico_badanti",
        "documento": "Detrazioni per personale domestico e badanti: detrazione IRPEF per contributi INPS versati per colf, badanti e domestici. Riferimento: Art. 10, comma 1, lettera f), TUIR. Massimale: 1.549,37 euro annui.",
        "parole_chiave": [
            "personale domestico", "badanti", "colf", "domestici", "collaboratore familiare",
            "contributi inps", "badante", "assistenza anziani", "assistenza disabili",
            "1549", "detrazione", "deduzione", "spese personale",
            "famiglia", "anziani", "disabili", "assistenza", "cura",
            "contratto domestico", "libretto famiglia", "prestazioni occasionali",
            "inps", "gestione separata", "contributi domestici"
        ],
        "metadati": {"categoria": "famiglia", "massimale": 1549.37}
    },

    # ==========================================
    # CATEGORIA: AUTO PERSONALE
    # ==========================================
    {
        "id": "bonus_bici_elettriche",
        "documento": "Bonus Mobilità Sostenibile: contributo per acquisto bici tradizionali ed elettriche, monopattini elettrici e servizi di sharing. Riferimento: Decreto Ministeriale annuale. Importi: fino a 500€ per bici elettriche.",
        "parole_chiave": [
            "bicicletta", "bici", "bici elettrica", "e-bike", "bici elettrica",
            "monopattino", "monopattino elettrico", "sharing", "bike sharing",
            "mobilità sostenibile", "green mobility", "trasporto sostenibile",
            "500", "contributo", "bonus bici", "bonus mobilità",
            "ambiente", "sostenibilità", "inquinamento", "zero emissioni",
            "spostamenti", "casa-lavoro", "pendolarismo", "ciclabile"
        ],
        "metadati": {"categoria": "auto", "massimale": 500}
    },

    # ==========================================
    # CATEGORIA: ALTRO
    # ==========================================
    {
        "id": "detrazioni_polizze_vita",
        "documento": "Detrazioni polizze vita e infortuni: detrazione del 19% per premi di assicurazioni sulla vita e contro gli infortuni. Riferimento: Art. 15, comma 1, lettera f), TUIR. Massimale: 1.936,24 euro annui.",
        "parole_chiave": [
            "polizza vita", "assicurazione vita", "vita", "infortuni", "assicurazione",
            "premi assicurativi", "polizza", "copertura", "protezione",
            "19%", "detrazione 19", "detrazione assicurazione", "bonus assicurazione",
            "1936", "massimale", "famiglia", "protezione familiare",
            "morte", "invalidità", "rendita", "capitale assicurato",
            "compagnia assicurativa", "premio annuo", "contratto assicurativo"
        ],
        "metadati": {"categoria": "investimenti", "aliquota": "19%"}
    },
]

# ==========================================
# 7. FUNZIONE RICERCA AVANZATA PER KEYWORD
# ==========================================

def cerca_normativa_pertinente(testo_ricerca: str, n_risultati: int = 3) -> List[str]:
    """
    Cerca nel database usando keyword matching avanzato con scoring.
    """
    testo_ricerca_lower = testo_ricerca.lower()
    parole_ricerca = set(testo_ricerca_lower.split())
    
    # Calcola punteggio per ogni bonus
    punteggi = []
    for bonus in BONUS_DATABASE:
        punteggio = 0
        
        # Controlla parole chiave (peso alto)
        for parola in bonus.get('parole_chiave', []):
            parola_lower = parola.lower()
            if parola_lower in testo_ricerca_lower:
                # Bonus extra se la parola è esatta
                if parola_lower in parole_ricerca:
                    punteggio += 3
                else:
                    punteggio += 2
            # Controlla anche sottostringhe
            elif len(parola_lower) > 4 and parola_lower[:4] in testo_ricerca_lower:
                punteggio += 1
        
        # Controlla nel documento (peso basso)
        if any(parola in testo_ricerca_lower for parola in testo_ricerca_lower.split()[:5]):
            punteggio += 1
        
        punteggi.append((bonus, punteggio))
    
    # Ordina per punteggio decrescente
    punteggi.sort(key=lambda x: x[1], reverse=True)
    
    # Ritorna i primi n risultati con punteggio > 0
    risultati = [bonus['documento'] for bonus, punteggio in punteggi[:n_risultati] if punteggio > 0]
    
    # Se nessun risultato, ritorna i primi bonus come fallback
    if not risultati:
        risultati = [bonus['documento'] for bonus in BONUS_DATABASE[:n_risultati]]
    
    return risultati

# ==========================================
# 8. SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
Sei FiscoHunter AI, esperto ottimizzatore fiscale italiano.
Il tuo obiettivo è massimizzare il risparmio fiscale rispettando la legge.

REGOLE:
1. Usa SOLO il contesto normativo fornito
2. Cita sempre la legge o circolare
3. Calcola il risparmio in Euro basandoti su importo e aliquota
4. Rispondi ESCLUSIVAMENTE in JSON con questa struttura:
{
    "obiettivo": "stringa",
    "vantaggio_economico": "stringa con calcolo euro",
    "riferimento_normativo": "stringa con citazione legge",
    "cavillo_strategia": "stringa",
    "rischi_controlli": "stringa",
    "azione_immediata": "stringa"
}
"""

# ==========================================
# 9. FUNZIONI MOTORE
# ==========================================

def genera_consiglio_fiscale(profilo: ProfiloUtente, spesa: str, importo: float, leggi_recuperate: List[str]) -> dict:
    contesto_leggi = "\n---\n".join(leggi_recuperate)
    user_prompt = f"""
PROFILO UTENTE:
- Regime fiscale: {profilo.regime_fiscale}
- Reddito complessivo: {profilo.reddito_complessivo}€
- Aliquota marginale: {profilo.aliquota_marginale * 100}%

SPESA DA ANALIZZARE:
- Descrizione: {spesa}
- Importo: {importo}€

CONTESTO NORMATIVO DISPONIBILE:
{contesto_leggi}

ISTRUZIONI:
Analizza la spesa e calcola il vantaggio economico esatto in euro.
"""
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        consiglio = json.loads(response.choices[0].message.content)
        return {
            "obiettivo": str(consiglio.get("obiettivo", "Obiettivo non specificato")),
            "vantaggio_economico": str(consiglio.get("vantaggio_economico", "Calcolo non disponibile")),
            "riferimento_normativo": str(consiglio.get("riferimento_normativo", "Riferimento non trovato")),
            "cavillo_strategia": str(consiglio.get("cavillo_strategia", "Nessuna strategia")),
            "rischi_controlli": str(consiglio.get("rischi_controlli", "Consultare commercialista")),
            "azione_immediata": str(consiglio.get("azione_immediata", "Nessuna azione urgente"))
        }
    except:
        raise HTTPException(status_code=500, detail="Errore nel parsing risposta AI")

def carica_cronologia(email_utente: str):
    try:
        if os.path.exists(CRONOLOGIA_FILE):
            with open(CRONOLOGIA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                return all_data.get(email_utente, [])
        return []
    except Exception as e:
        print(f"❌ Errore carica cronologia: {e}")
        return []

def salva_cronologia(email_utente: str, cronologia):
    try:
        if os.path.exists(CRONOLOGIA_FILE):
            with open(CRONOLOGIA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        else:
            all_data = {}
        all_data[email_utente] = cronologia
        with open(CRONOLOGIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Errore salva cronologia: {e}")

# ==========================================
# 10. ENDPOINT AUTH
# ==========================================

@app.post("/register")
async def register(user: UserRegister):
    users = load_users()
    if user.email in users:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    hashed_password = get_password_hash(user.password)
    users[user.email] = {
        "email": user.email,
        "password": hashed_password,
        "nome": user.nome,
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user.email, "nome": user.nome}
    }

@app.post("/login")
async def login(user: UserLogin):
    users = load_users()
    user_data = users.get(user.email)
    if not user_data or not verify_password(user.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Credenziali errate")
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"email": user_data["email"], "nome": user_data["nome"]}
    }

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["email"], "nome": current_user["nome"]}

# ==========================================
# 11. ENDPOINT PRINCIPALI
# ==========================================

@app.on_event("startup")
async def startup_event():
    print("🚀 FiscoHunter AI Backend pronto!")
    print(f"📚 {len(BONUS_DATABASE)} bonus fiscali caricati")

@app.get("/")
async def root():
    return {"message": "FiscoHunter AI Backend", "status": "active", "version": "2.1.0"}

@app.post("/analisi")
async def analizzare_spesa(request: RichiestaAnalisi, current_user: dict = Depends(get_current_user)):
    try:
        leggi_pertinenti = cerca_normativa_pertinente(request.spesa_descrizione)
        if not leggi_pertinenti:
            raise HTTPException(status_code=404, detail="Nessuna normativa trovata")
        
        consiglio = genera_consiglio_fiscale(
            profilo=request.profilo,
            spesa=request.spesa_descrizione,
            importo=request.importo_spesa,
            leggi_recuperate=leggi_pertinenti
        )
        return RispostaFiscale(**consiglio)
    except HTTPException:
        raise
    except Exception as e:
        print(f" Errore analisi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/salva-analisi")
async def salva_analisi(analisi: AnalisiCompleta, current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        nuova_analisi = {
            "id": len(cronologia) + 1,
            "data": datetime.now().isoformat(),
            "profilo": {
                "regime_fiscale": analisi.profilo.regime_fiscale,
                "reddito_complessivo": analisi.profilo.reddito_complessivo,
                "aliquota_marginale": analisi.profilo.aliquota_marginale
            },
            "spesa": {
                "descrizione": analisi.spesa_descrizione,
                "importo": analisi.importo_spesa
            },
            "consiglio": {
                "obiettivo": analisi.obiettivo,
                "vantaggio_economico": analisi.vantaggio_economico,
                "riferimento_normativo": analisi.riferimento_normativo,
                "cavillo_strategia": analisi.cavillo_strategia,
                "rischi_controlli": analisi.rischi_controlli,
                "azione_immediata": analisi.azione_immediata
            }
        }
        cronologia.append(nuova_analisi)
        salva_cronologia(current_user["email"], cronologia)
        return {"success": True, "id": nuova_analisi["id"]}
    except Exception as e:
        print(f"❌ Errore salva analisi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cronologia")
async def get_cronologia(current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        return {"success": True, "analisi": cronologia, "totale": len(cronologia)}
    except Exception as e:
        print(f"❌ Errore get cronologia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistiche")
async def get_statistiche(current_user: dict = Depends(get_current_user)):
    try:
        cronologia = carica_cronologia(current_user["email"])
        if not cronologia:
            return {
                "success": True,
                "totale_analisi": 0,
                "risparmio_totale": 0,
                "risparmio_mensile": {},
                "categorie": {},
                "media_risparmio": 0
            }
        
        risparmio_totale = 0
        risparmio_mensile = {}
        categorie = {}
        risparmi = []
        
        for analisi in cronologia:
            try:
                vantaggio = analisi['consiglio']['vantaggio_economico'] or ''
                match = re.search(r'[\d,]+\.?\d*', vantaggio)
                if match:
                    numero = match.group().replace(',', '.')
                    risparmio = float(numero)
                    risparmi.append(risparmio)
                    risparmio_totale += risparmio
                    
                    data = analisi.get('data', '')
                    if data:
                        mese = data[:7]
                        risparmio_mensile[mese] = risparmio_mensile.get(mese, 0) + risparmio
                    
                    descrizione = analisi['spesa']['descrizione'].lower()
                    if any(k in descrizione for k in ['farmacia', 'medico', 'salute']):
                        cat = 'Salute'
                    elif any(k in descrizione for k in ['casa', 'ristruttur']):
                        cat = 'Casa'
                    elif any(k in descrizione for k in ['auto', 'macchina', 'veicolo']):
                        cat = 'Auto'
                    elif any(k in descrizione for k in ['figli', 'nido', 'scuola']):
                        cat = 'Famiglia'
                    else:
                        cat = 'Altro'
                    categorie[cat] = categorie.get(cat, 0) + 1
            except:
                continue
        
        media_risparmio = sum(risparmi) / len(risparmi) if risparmi else 0
        return {
            "success": True,
            "totale_analisi": len(cronologia),
            "risparmio_totale": round(risparmio_totale, 2),
            "risparmio_mensile": dict(sorted(risparmio_mensile.items())),
            "categorie": categorie,
            "media_risparmio": round(media_risparmio, 2)
        }
    except Exception as e:
        print(f"❌ Errore statistiche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr-scontrino")
async def ocr_scontrino(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Nessuna immagine")
        
        base64_image = base64.b64encode(body).decode('utf-8')
        prompt = "Leggi questo scontrino italiano ed estrai SOLO: importo totale, breve descrizione, data. Rispondi in JSON con campi: importo (numero), descrizione (stringa), data (YYYY-MM-DD o null)."
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        try:
            risultato = json.loads(response.choices[0].message.content)
        except:
            json_match = re.search(r'\{.*?\}', response.choices[0].message.content, re.DOTALL)
            risultato = json.loads(json_match.group()) if json_match else {}
        
        return {
            "success": True,
            "importo": risultato.get("importo"),
            "descrizione": risultato.get("descrizione"),
            "data": risultato.get("data"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Errore OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simula-isee")
async def simula_isee(dati: DatiISEE, current_user: dict = Depends(get_current_user)):
    """Simula una stima dell'ISEE (formula semplificata)"""
    try:
        # Formula ISEE semplificata:
        # ISR = Reddito + 20% Patrimonio Mobiliare + Patrimonio Immobiliare
        # ISP = Patrimonio Immobiliare + Patrimonio Mobiliare
        # ISEE = (ISR + 20% ISP) / Scala Equivalente
        
        scala_equivalente = 1.0
        if dati.componenti_familiari > 1:
            scala_equivalente = 1.0 + (0.35 * (dati.componenti_familiari - 1))
        
        isr = dati.reddito_complessivo + (dati.patrimonio_mobiliare * 0.20) + dati.patrimonio_immobiliare
        isp = dati.patrimonio_immobiliare + dati.patrimonio_mobiliare
        
        isee_stimato = (isr + (isp * 0.20)) / scala_equivalente
        
        # Determina la fascia
        fascia = "ISEE superiore a 50.000€"
        if isee_stimato < 15000:
            fascia = "ISEE sotto 15.000€ (Massime agevolazioni)"
        elif isee_stimato < 30000:
            fascia = "ISEE tra 15.000€ e 30.000€ (Agevolazioni medie)"
        elif isee_stimato < 50000:
            fascia = "ISEE tra 30.000€ e 50.000€ (Agevolazioni ridotte)"
            
        return {
            "success": True,
            "isee_stimato": round(isee_stimato, 2),
            "fascia": fascia,
            "scala_equivalente": round(scala_equivalente, 2),
            "nota": "Questa è una stima semplificata. L'ISEE ufficiale si calcola tramite DSU all'INPS."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bonus_caricati": len(BONUS_DATABASE),
        "server": "uvicorn",
        "version": "2.1.0"
    }