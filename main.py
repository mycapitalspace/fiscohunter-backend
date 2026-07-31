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
    version="2.0.0"
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

# ==========================================
# 6. DATABASE BONUS CON PAROLE CHIAVE COMPLETE
# ==========================================

BONUS_DATABASE = [
    {
        "id": "ecobonus_65",
        "documento": "Ecobonus 65% per climatizzatori e pompe di calore. Detrazione del 65% delle spese sostenute per l'installazione di climatizzatori con pompa di calore ad alta efficienza energetica. Riferimento: Art. 1, commi 345-347, Legge 296/2006 (Finanziaria 2007). Requisiti: documentazione tecnica del produttore, bonifico parlante per riqualificazione energetica. Massimale: 100.000 euro. Recupero: 10 quote annuali.",
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
        "id": "bonus_ristrutturazioni_50",
        "documento": "Bonus Ristrutturazioni 50% per interventi di manutenzione straordinaria, restauro, risanamento conservativo e ristrutturazione edilizia. Detrazione IRPEF del 50%. Riferimento: Art. 16-bis del TUIR. Requisiti: titolo abilitativo (CILA, SCIA), bonifico parlante, fatture dettagliate. Massimale: 96.000 euro. Recupero: 10 quote annuali.",
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
        "documento": "Bonus Mobili ed Elettrodomestici 50% per l'acquisto di mobili nuovi e grandi elettrodomestici in classe energetica A o superiore. Detrazione IRPEF del 50%. Riferimento: Art. 16-bis, comma 3, del TUIR. Requisiti: aver iniziato una ristrutturazione, bonifico parlante o carta di credito. Massimale: 5.000 euro. Recupero: 10 quote annuali.",
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
        "id": "detrazioni_sanitarie_19",
        "documento": "Detrazioni spese sanitarie 19% per spese mediche, chirurgiche, specialistiche, diagnostiche e di laboratorio. Detrazione IRPEF del 19% sulla parte che eccede la franchigia di 129,11 euro. Riferimento: Art. 15, comma 1, lettera c), del TUIR. Requisiti: scontrini parlanti con codice fiscale. Sono detraibili anche psicologi, osteopati, logopedisti.",
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
        "id": "bonus_nido_3000",
        "documento": "Bonus Nido: rimborso fino a 3.000 euro annui per rette di asili nido pubblici e privati o per servizi di baby-sitting. Riferimento: Art. 1, comma 355, Legge 232/2016. Requisiti: domanda all'INPS entro il 31 dicembre, ISEE non superiore a 40.000 euro. Importo: fino a 3.000 euro per ISEE fino a 25.000 euro.",
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
        "id": "fondo_pensione",
        "documento": "Fondi Pensione Complementari: versamenti a fondi pensione sono deducibili dal reddito imponibile fino a 5.164,57 euro annui. Riferimento: Art. 10, comma 1, lettera e), del TUIR. Vantaggio: riducendo il reddito imponibile, si abbassa l'aliquota IRPEF. Esempio: reddito 60.000€ (aliquota 35%), versi 5.000€, paghi tasse su 55.000€, risparmi 1.750€.",
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
        "id": "bonus_auto_azienda",
        "documento": "Auto aziendale: deducibilità del 20% per autovetture concesse in uso promiscuo ai dipendenti. Riferimento: Art. 164, comma 1, lettera c), del TUIR. La deduzione è limitata al 20% del costo di acquisto e delle spese di esercizio. Per veicoli elettrici o ibridi plug-in la deducibilità sale al 30%.",
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
        "metadati": {"categoria": "auto", "aliquota": "20%"}
    },
    {
        "id": "istruzione_19",
        "documento": "Detrazioni spese istruzione 19% per spese di frequenza di scuole dell'infanzia, primarie, secondarie e universitarie. Riferimento: Art. 15, comma 1, lettera g), del TUIR. Massimale: 786 euro per alunno/studente. Sono detraibili anche le spese per corsi di laurea, master e dottorati.",
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
    return {"message": "FiscoHunter AI Backend", "status": "active", "version": "2.0-light"}

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
        print(f"❌ Errore analisi: {e}")
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

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bonus_caricati": len(BONUS_DATABASE),
        "server": "uvicorn",
        "version": "2.0-light"
    }