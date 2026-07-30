# popola_database.py
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Configura OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("ERRORE: OPENAI_API_KEY non trovata nel file .env")

# Inizializza ChromaDB
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=api_key,
    model_name="text-embedding-3-small"
)

chroma_client = chromadb.Client()
fisco_collection = chroma_client.get_or_create_collection(
    name="normativa_fiscale_italiana",
    embedding_function=openai_ef
)

# ==========================================
# DATABASE COMPLETO DEI BONUS FISCALI ITALIANI
# ==========================================

BONUS_DATABASE = [
    # ==========================================
    # CASA E PATRIMONIO IMMOBILIARE
    # ==========================================
    {
        "id": "ecobonus_65_climatizzatori",
        "categoria": "casa",
        "documento": "Ecobonus 65% per climatizzatori inverter e pompe di calore. Detrazione del 65% delle spese sostenute per l'installazione di climatizzatori con pompa di calore ad alta efficienza energetica. Riferimento normativo: Art. 1, commi 345-347, Legge 296/2006 (Finanziaria 2007) e successive modifiche. Circolare Agenzia delle Entrate n. 13/E del 2023. Requisiti: documentazione tecnica del produttore che attesti il rispetto dei requisiti minimi di efficienza energetica, bonifico parlante specifico per riqualificazione energetica, asseverazione di un tecnico abilitato se si opta per la cessione del credito o sconto in fattura. Massimale di spesa: 100.000 euro per unità immobiliare. Recupero: 10 quote annuali di pari importo nella dichiarazione dei redditi. Cavillo: se l'intervento è trainato da una ristrutturazione edilizia, si può accedere al Bonus Casa 50% con massimale più alto di 96.000 euro.",
        "metadati": {"aliquota": "65%", "tipo": "ecobonus", "massimale": 100000, "anni_recupero": 10}
    },
    {
        "id": "bonus_ristrutturazioni_50",
        "categoria": "casa",
        "documento": "Bonus Ristrutturazioni 50% per interventi di manutenzione straordinaria, restauro, risanamento conservativo e ristrutturazione edilizia. Detrazione IRPEF del 50% delle spese sostenute. Riferimento normativo: Art. 16-bis del TUIR (Testo Unico delle Imposte sui Redditi, DPR 917/1986). Requisiti: titolo abilitativo (CILA, SCIA o permesso di costruire), bonifico parlante con causale specifica, fatture dettagliate. Massimale: 96.000 euro per unità immobiliare. Recupero: 10 quote annuali di pari importo. Cavillo strategico: anche la manutenzione ordinaria (tinteggiatura, sostituzione infissi senza modifica dimensioni) è detraibile al 50% se l'immobile è in condominio e l'intervento riguarda parti comuni. Per le parti private serve manutenzione straordinaria.",
        "metadati": {"aliquota": "50%", "tipo": "ristrutturazione", "massimale": 96000, "anni_recupero": 10}
    },
    {
        "id": "bonus_mobili_50",
        "categoria": "casa",
        "documento": "Bonus Mobili ed Elettrodomestici 50% per l'acquisto di mobili nuovi e grandi elettrodomestici in classe energetica A o superiore (F per i forni). Detrazione IRPEF del 50%. Riferimento normativo: Art. 16-bis, comma 3, del TUIR. Requisiti: aver iniziato un intervento di ristrutturazione edilizia prima dell'acquisto dei mobili, bonifico parlante o pagamento con carta di credito/debito (non contanti), fatture e ricevute fiscali. Massimale: 5.000 euro per l'anno 2024 (10.000 euro per gli anni 2022-2023). Recupero: 10 quote annuali. Cavillo: l'acquisto di mobili usati non è ammesso, solo mobili nuovi. Gli elettrodomestici devono essere di classe A o superiore (tranne i forni che possono essere classe F).",
        "metadati": {"aliquota": "50%", "tipo": "mobili", "massimale": 5000, "anni_recupero": 10}
    },
    {
        "id": "bonus_barriere_architettoniche_75",
        "categoria": "casa",
        "documento": "Bonus Barriere Architettoniche 75% per l'eliminazione delle barriere architettoniche in condomini e abitazioni private. Detrazione del 75% delle spese. Riferimento normativo: Art. 119, comma 2, del Decreto Rilancio (DL 34/2020) convertito in Legge 77/2020. Requisiti: interventi su ascensori, montascale, piattaforme elevatrici, rampe, servizi igienici accessibili. La spesa deve essere documentata con fatture e bonifici parlanti. Massimale: 50.000 euro per unità immobiliare in condominio, 30.000 euro per villette. Recupero: 5 quote annuali (novità rispetto ai 10 anni degli altri bonus). Cavillo: non è necessario alcun titolo abilitativo per questi interventi, basta una dichiarazione sostitutiva dell'atto di notorietà.",
        "metadati": {"aliquota": "75%", "tipo": "barriere_architettoniche", "massimale": 50000, "anni_recupero": 5}
    },
    {
        "id": "bonus_verde_36",
        "categoria": "casa",
        "documento": "Bonus Verde 36% per la sistemazione a verde di aree scoperte private di edifici esistenti (giardini, terrazzi, balconi, recinzioni, impianti di irrigazione). Detrazione IRPEF del 36%. Riferimento normativo: Art. 1, commi 10-14, Legge 232/2016 (Legge di Bilancio 2017). Requisiti: fatture dettagliate, pagamenti tracciabili (bonifico o carta). Massimale: 5.000 euro per unità immobiliare. Recupero: 10 quote annuali. Cavillo: rientrano anche le spese per la potatura di alberi ad alto fusto e la manutenzione di giardini esistenti, non solo la creazione ex-novo.",
        "metadati": {"aliquota": "36%", "tipo": "verde", "massimale": 5000, "anni_recupero": 10}
    },
    {
        "id": "sismabonus_85",
        "categoria": "casa",
        "documento": "Sismabonus 85% per interventi di riduzione del rischio sismico su edifici in zona sismica 1, 2 o 3. Detrazione fino all'85% se l'intervento migliora di due classi il rischio sismico dell'edificio. Riferimento normativo: Art. 16-ter del TUIR, introdotto dal DL 50/2017. Requisiti: attestazione SISMIC dell'ingegnere strutturista prima e dopo l'intervento, bonifico parlante, fatture. Massimale: 96.000 euro per unità immobiliare. Recupero: 5 quote annuali. Cavillo: se l'intervento è effettuato su parti comuni condominiali, la detrazione spetta a ogni condomino in proporzione alla sua millesimale.",
        "metadati": {"aliquota": "85%", "tipo": "sismabonus", "massimale": 96000, "anni_recupero": 5}
    },
    {
        "id": "bonus_facciate_90",
        "categoria": "casa",
        "documento": "Bonus Facciate 90% per il restauro, la pulitura e la tinteggiatura della facciata esterna degli edifici. Detrazione del 90% delle spese. Riferimento normativo: Art. 1, commi 219-223, Legge 160/2019 (Legge di Bilancio 2020). Requisiti: l'edificio deve essere ubicato in zona A o B (centro storico o edificato), fatture e bonifici parlanti. Massimale: non previsto (detrazione su tutta la spesa). Recupero: 10 quote annuali. Cavillo: la detrazione spetta anche per la pulitura e tinteggiatura, non solo per il restauro strutturale della facciata.",
        "metadati": {"aliquota": "90%", "tipo": "facciate", "massimale": None, "anni_recupero": 10}
    },
    
    # ==========================================
    # SALUTE E BENESSERE
    # ==========================================
    {
        "id": "detrazioni_sanitarie_19",
        "categoria": "salute",
        "documento": "Detrazioni spese sanitarie 19% per spese mediche, chirurgiche, specialistiche, diagnostiche e di laboratorio. Detrazione IRPEF del 19% sulla parte che eccede la franchigia di 129,11 euro. Riferimento normativo: Art. 15, comma 1, lettera c), del TUIR. Requisiti: scontrini parlanti con codice fiscale del contribuente, fatture per prestazioni specialistiche. La franchigia di 129,11 euro è annuale e si applica al totale delle spese sanitarie. Cavillo strategico: sono detraibili anche le spese per psicologi e psicoterapeuti (se iscritti all'Albo), osteopati, chiropratici, logopedisti. Anche le spese veterinarie per animali guida dei non vedenti sono detraibili. Le protesi dentarie e gli apparecchi acustici rientrano tra le spese sanitarie.",
        "metadati": {"aliquota": "19%", "tipo": "sanitarie", "franchigia": 129.11, "massimale": None}
    },
    {
        "id": "bonus_psicologo_1500",
        "categoria": "salute",
        "documento": "Bonus Psicologo: contributo fino a 1.500 euro per sedute di supporto psicologico. Non è una detrazione ma un contributo a fondo perduto erogato dall'INPS. Riferimento normativo: Art. 2, comma 6, del DL 146/2021 convertito in Legge 205/2021. Requisiti: ISEE non superiore a 50.000 euro, prenotazione tramite portale INPS, scelta dello psicologo dall'elenco degli aderenti all'iniziativa. L'importo varia in base all'ISEE: fino a 1.500 euro per ISEE fino a 15.000 euro, 1.250 euro per ISEE 15.000-30.000, 1.000 euro per ISEE 30.000-50.000. Cavillo: il bonus è cumulabile con la detrazione IRPEF del 19% sulla parte di spesa non coperta dal contributo.",
        "metadati": {"aliquota": "contributo", "tipo": "psicologo", "massimale": 1500, "isee_max": 50000}
    },
    {
        "id": "detrazioni_disabili_19",
        "categoria": "salute",
        "documento": "Detrazioni per disabili 19% per spese mediche, di assistenza specifica e di aiuto personale. Detrazione IRPEF del 19% senza applicazione della franchigia di 129,11 euro. Riferimento normativo: Art. 15, comma 1, lettera c-bis), del TUIR. Requisiti: certificazione di disabilità (Legge 104/1992), fatture e scontrini parlanti. Rientrano: spese per addetti all'assistenza personale, mezzi ausiliari (carrozzine, deambulatori), sussidi tecnici e informatici. Cavillo: se il disabile è fiscalmente a carico, le spese possono essere detratte dal familiare che lo ha a carico, anche se pagate dal disabile stesso.",
        "metadati": {"aliquota": "19%", "tipo": "disabili", "franchigia": 0, "massimale": None}
    },
    
    # ==========================================
    # FAMIGLIA E FIGLI
    # ==========================================
    {
        "id": "assegno_unico_figli",
        "categoria": "famiglia",
        "documento": "Assegno Unico Universale per i figli a carico: prestazione mensile erogata dall'INPS per ogni figlio fino a 21 anni (o senza limite di età se disabile). L'importo varia in base all'ISEE familiare. Riferimento normativo: DL 230/2021 convertito in Legge 15/2022. Requisiti: domanda all'INPS, ISEE valido. Importo base: 175 euro mensili per figlio (2024), con maggiorazioni per figli disabili, famiglie numerose (3+ figli), madri under 21. L'assegno è erogato direttamente dall'INPS, non passa per la dichiarazione dei redditi. Cavillo: l'assegno spetta anche per i figli maggiorenni fino a 21 anni se studenti, disoccupati o con reddito inferiore a 8.000 euro annui.",
        "metadati": {"tipo": "assegno_unico", "importo_base_mensile": 175, "eta_max": 21}
    },
    {
        "id": "bonus_nido_3000",
        "categoria": "famiglia",
        "documento": "Bonus Nido: rimborso fino a 3.000 euro annui per rette di asili nido pubblici e privati o per servizi di baby-sitting. Riferimento normativo: Art. 1, comma 355, Legge 232/2016. Requisiti: domanda all'INPS entro il 31 dicembre dell'anno di riferimento, ISEE non superiore a 40.000 euro. Importo: fino a 3.000 euro per ISEE fino a 25.000 euro, fino a 2.500 euro per ISEE 25.000-35.000, fino a 1.500 euro per ISEE 35.000-40.000. Cavillo: il bonus spetta anche per le rette dei centri estivi e dei servizi integrativi per l'infanzia.",
        "metadati": {"tipo": "bonus_nido", "massimale": 3000, "isee_max": 40000}
    },
    {
        "id": "detrazioni_istruzione_19",
        "categoria": "famiglia",
        "documento": "Detrazioni spese istruzione 19% per spese scolastiche e universitarie. Detrazione IRPEF del 19% su: rette di scuole paritarie (massimale 800 euro annui), spese universitarie (iscrizione, tasse, contributi), master e corsi di specializzazione. Riferimento normativo: Art. 15, comma 1, lettera i-ter) e i-quater), del TUIR. Requisiti: attestazioni di pagamento delle istituzioni scolastiche/universitarie. Cavillo: sono detraibili anche le spese per corsi di laurea all'estero se l'università è riconosciuta in Italia. Le spese per libri di testo sono detraibili solo se obbligatorie e certificate dalla scuola.",
        "metadati": {"aliquota": "19%", "tipo": "istruzione", "massimale_scuola": 800, "massimale_universita": None}
    },
    {
        "id": "detrazioni_sport_minori_19",
        "categoria": "famiglia",
        "documento": "Detrazioni attività sportive per minori 19% per quote associative e abbonamenti a società sportive per ragazzi tra 5 e 18 anni. Detrazione IRPEF del 19% su un massimo di 1.500 euro annui per figlio. Riferimento normativo: Art. 15, comma 1, lettera i-quinquies), del TUIR. Requisiti: attestazione della società sportiva con dati del ragazzo, pagamento tracciabile. Massimale: 1.500 euro per figlio, quindi detrazione massima di 285 euro annui (19% di 1.500). Cavillo: rientrano anche le spese per lezioni private di sport (es. tennis, nuoto) se erogate da società sportive dilettantistiche.",
        "metadati": {"aliquota": "19%", "tipo": "sport_minori", "massimale": 1500, "eta_min": 5, "eta_max": 18}
    },
    
    # ==========================================
    # LAVORO E BUSINESS
    # ==========================================
    {
        "id": "bonus_lavoro_dipendente",
        "categoria": "lavoro",
        "documento": "Bonus Lavoro Dipendente (ex Renzi): detrazione IRPEF per redditi da lavoro dipendente fino a 15.000 euro. Importo: 1.200 euro annui per redditi fino a 8.000 euro, 720 euro per redditi 8.000-15.000 euro. Riferimento normativo: Art. 13, comma 1-bis), del TUIR. Requisiti: reddito da lavoro dipendente, dichiarazione dei redditi. Il bonus è erogato direttamente in busta paga dal datore di lavoro. Cavillo: se il reddito supera i 15.000 euro ma è inferiore a 28.000 euro, spetta una detrazione decrescente calcolata con formula specifica.",
        "metadati": {"tipo": "bonus_lavoro", "importo_max": 1200, "reddito_max": 15000}
    },
    {
        "id": "regime_forfettario_5_15",
        "categoria": "business",
        "documento": "Regime Forfettario: tassazione agevolata per partite IVA con ricavi/compensi fino a 85.000 euro annui. Imposta sostitutiva del 5% per i primi 5 anni (start-up) e 15% dal sesto anno. Riferimento normativo: Art. 1, commi 54-89, Legge 190/2014 (Legge di Stabilità 2015). Requisiti: ricavi/compensi non superiori a 85.000 euro, spese per lavoro dipendente non superiori a 20.000 euro lordi annui. Vantaggi: no IVA, no IRAP, no ritenuta d'acconto, contributi INPS ridotti del 35%. Cavillo strategico: il coefficiente di redditività varia per codice ATECO (es. 78% per professioni, 40% per commercio). Si pagano le tasse solo sul 40-78% dei ricavi, non sul totale.",
        "metadati": {"aliquota_start": "5%", "aliquota_ordinaria": "15%", "massimale_ricavi": 85000}
    },
    {
        "id": "credito_imposta_rs",
        "categoria": "business",
        "documento": "Credito d'imposta Ricerca e Sviluppo (R&S): credito d'imposta del 20% sulle spese per ricerca di base, ricerca industriale e sviluppo sperimentale. Riferimento normativo: Art. 3, DL 145/2013 (Decreto Destina Italia) convertito in Legge 9/2014, modificato dalla Legge di Bilancio 2024. Requisiti: progetti di innovazione tecnologica, documentazione tecnica, certificazione del credito da parte di un revisore. Massimale: 5 milioni di euro annui per beneficiario. Cavillo: rientrano anche le spese per personale altamente qualificato (laureati, dottorandi) dedicato ai progetti di R&S, non solo le spese per attrezzature.",
        "metadati": {"aliquota": "20%", "tipo": "credito_imposta", "massimale": 5000000}
    },
    {
        "id": "credito_imposta_industria_40",
        "categoria": "business",
        "documento": "Credito d'imposta Industria 4.0 (Transizione 4.0): credito d'imposta per investimenti in beni materiali e immateriali strumentali nuovi, interconnessi al sistema aziendale. Aliquota: 20% per investimenti fino a 2,5 milioni di euro, 10% per la parte eccedente fino a 10 milioni. Riferimento normativo: Art. 1, commi 184-200, Legge 160/2019 (Legge di Bilancio 2020), modificato dalla Legge di Bilancio 2024. Requisiti: beni nuovi (non usati), interconnessione al sistema aziendale (IoT), documentazione tecnica. Cavillo: i beni immateriali (software gestionali, sistemi ERP, cybersecurity) rientrano nel credito con aliquota del 20% fino a 1 milione di euro.",
        "metadati": {"aliquota": "20%", "tipo": "credito_imposta", "massimale": 10000000}
    },
    {
        "id": "welfare_aziendale",
        "categoria": "business",
        "documento": "Welfare Aziendale: prestazioni di welfare erogate dal datore di lavoro ai dipendenti sono esenti da tasse e contributi fino a 3.000 euro annui (1.500 euro se senza figli). Riferimento normativo: Art. 51, comma 3, del TUIR. Requisiti: piano di welfare aziendale, documenti di spesa. Rientrano: buoni spesa, rimborsi per istruzione dei figli, servizi di baby-sitting, assistenza agli anziani, auto aziendale per uso personale. Cavillo strategico: invece di dare un aumento di stipendio di 1.000 euro (tassato al 35-43%), erogare welfare aziendale dello stesso importo è netto per il dipendente e deducibile per l'azienda.",
        "metadati": {"tipo": "welfare", "massimale_con_figli": 3000, "massimale_senza_figli": 1500}
    },
    
    # ==========================================
    # AUTO E TRASPORTI
    # ==========================================
    {
        "id": "detrazione_auto_promiscuo",
        "categoria": "auto",
        "documento": "Deducibilità auto in uso promiscuo: per i professionisti e lavoratori autonomi, le spese per auto assegnate in uso promiscuo (personale e professionale) sono deducibili al 50% del costo. Riferimento normativo: Art. 16, comma 1, lettera d), del TUIR. Requisiti: contratto di assegnazione auto, registro dei chilometri (consigliato). Rientrano: acquisto auto, leasing, noleggio, carburante, manutenzione, assicurazione, bollo. Cavillo: se l'auto è usata esclusivamente per l'attività professionale (agenti di commercio, rappresentanti), la deducibilità sale all'80% o al 100% a seconda dei casi. Per i dipendenti con auto aziendale, il fringe benefit è tassato solo sul 25% del valore (30% per auto ibride, 15% per elettriche).",
        "metadati": {"aliquota_deducibilita": "50%", "tipo": "auto_promiscuo"}
    },
    {
        "id": "bonus_colonnine_ricarica",
        "categoria": "auto",
        "documento": "Bonus Colonnine di Ricarica: credito d'imposta del 50% per l'installazione di infrastrutture di ricarica per veicoli elettrici. Riferimento normativo: Art. 1, comma 1044, Legge 178/2020 (Legge di Bilancio 2021). Requisiti: installazione di colonnine private o condominiali, fatture e pagamenti tracciabili. Massimale: 8.000 euro per unità immobiliare. Recupero: credito d'imposta in 3 quote annuali. Cavillo: il bonus spetta anche per l'installazione di colonnine in box privati e posti auto condominiali, non solo in garage.",
        "metadati": {"aliquota": "50%", "tipo": "colonnine", "massimale": 8000, "anni_recupero": 3}
    },
    
    # ==========================================
    # INVESTIMENTI E RISPARMIO
    # ==========================================
    {
        "id": "fondo_pensione_deducibile",
        "categoria": "investimenti",
        "documento": "Fondi Pensione Complementari: versamenti a fondi pensione complementari sono deducibili dal reddito imponibile fino a 5.164,57 euro annui. Riferimento normativo: Art. 10, comma 1, lettera e), del TUIR. Requisiti: adesione a fondo pensione aperto o negoziale, versamenti documentati. Vantaggio: riducendo il reddito imponibile, si abbassa l'aliquota IRPEF marginale. Esempio: se hai un reddito di 60.000 euro (aliquota 35%) e versi 5.000 euro al fondo pensione, paghi le tasse su 55.000 euro, risparmiando 1.750 euro di IRPEF. Cavillo strategico: i versamenti sono deducibili anche se effettuati dal coniuge o dai figli a carico, purché il fondo sia intestato al contribuente.",
        "metadati": {"tipo": "deduzione", "massimale": 5164.57, "aliquota_risparmio": "variabile"}
    },
    {
        "id": "piano_individuali_risparmio_pir",
        "categoria": "investimenti",
        "documento": "Piani Individuali di Risparmio (PIR): investimenti in PIR sono esenti da imposta sulle successioni e da imposta di bollo. Riferimento normativo: Art. 1, commi 617-628, Legge 232/2016 (Legge di Stabilità 2017). Requisiti: investimento minimo 5 anni, portafoglio diversificato con almeno il 70% in strumenti finanziari di imprese italiane o UE. Vantaggi: no imposta di bollo (0,2% annui), no tasse sulle plusvalenze, no imposta di successione. Cavillo: se il PIR è mantenuto per almeno 5 anni, le plusvalenze sono completamente esenti da tassazione.",
        "metadati": {"tipo": "esenzione", "durata_minima": 5, "aliquota_bollo": "0%"}
    },
    
    # ==========================================
    # ENERGIA E SOSTENIBILITÀ
    # ==========================================
    {
        "id": "bonus_solare_termico_65",
        "categoria": "energia",
        "documento": "Ecobonus 65% per pannelli solari termici per produzione di acqua calda sanitaria. Detrazione del 65% delle spese. Riferimento normativo: Art. 1, commi 345-347, Legge 296/2006. Requisiti: pannelli certificati, installazione da parte di tecnico abilitato, bonifico parlante. Massimale: 100.000 euro. Recupero: 10 quote annuali. Cavillo: se i pannelli solari sono installati insieme a una caldaia a condensazione, entrambi gli interventi rientrano nell'Ecobonus 65% con massimali separati.",
        "metadati": {"aliquota": "65%", "tipo": "solare_termico", "massimale": 100000, "anni_recupero": 10}
    },
    {
        "id": "bonus_cappotto_termico_65",
        "categoria": "energia",
        "documento": "Ecobonus 65% per cappotto termico (coibentazione involucro opaco) con miglioramento di almeno 2 classi energetiche. Detrazione del 65%. Riferimento normativo: Art. 1, commi 345-347, Legge 296/2006. Requisiti: attestato di prestazione energetica (APE) prima e dopo l'intervento, documentazione tecnica, bonifico parlante. Massimale: 100.000 euro. Recupero: 10 quote annuali. Cavillo: se il cappotto termico è trainato da una ristrutturazione edilizia, si può accedere al Sismabonus 85% se si migliora anche la classe sismica.",
        "metadati": {"aliquota": "65%", "tipo": "cappotto_termico", "massimale": 100000, "anni_recupero": 10}
    },
    {
        "id": "bonus_caldaia_condensazione_65",
        "categoria": "energia",
        "documento": "Ecobonus 65% per sostituzione di caldaia con caldaia a condensazione di classe A con sistemi di termoregolazione evoluti. Detrazione del 65%. Riferimento normativo: Art. 1, commi 345-347, Legge 296/2006. Requisiti: caldaia in classe A, sistemi di termoregolazione evoluti (classe V, VI o VIII secondo regolamento UE 811/2013), bonifico parlante. Massimale: 100.000 euro. Recupero: 10 quote annuali. Cavillo: se la caldaia è in classe A+ o superiore, la detrazione sale al 65% anche senza termoregolazione evoluta.",
        "metadati": {"aliquota": "65%", "tipo": "caldaia_condensazione", "massimale": 100000, "anni_recupero": 10}
    },
    
    # ==========================================
    # DONAZIONI E FILANTROPIA
    # ==========================================
    {
        "id": "detrazioni_donazioni_30",
        "categoria": "filantropia",
        "documento": "Detrazioni donazioni a ONLUS, associazioni di volontariato, fondazioni: detrazione IRPEF del 30% delle donazioni fino a 30.000 euro annui. Riferimento normativo: Art. 14, DL 35/2005 convertito in Legge 80/2005. Requisiti: donazioni tracciabili (bonifico, carta), attestazione dell'ente beneficiario. Massimale: 30.000 euro annui. Recupero: in dichiarazione dei redditi. Cavillo: le donazioni a favore di partiti politici sono deducibili (non detraibili) fino a 30.000 euro annui, con vantaggio maggiore per i contribuenti con aliquota marginale alta.",
        "metadati": {"aliquota": "30%", "tipo": "donazioni", "massimale": 30000}
    },
    
    # ==========================================
    # ASSICURAZIONI E PREVIDENZA
    # ==========================================
    {
        "id": "detrazioni_assicurazioni_19",
        "categoria": "previdenza",
        "documento": "Detrazioni polizze assicurative 19% per polizze sulla vita e contro gli infortuni. Detrazione IRPEF del 19% sui premi versati. Riferimento normativo: Art. 15, comma 1, lettera f), del TUIR. Requisiti: polizze vita o infortuni, attestazione della compagnia assicurativa. Massimale: 1.291,14 euro annui per polizze vita, 1.549,37 euro per polizze infortuni. Recupero: in dichiarazione dei redditi. Cavillo: le polizze sulla vita con clausola di rivalutazione del capitale sono detraibili solo se la durata è almeno di 5 anni.",
        "metadati": {"aliquota": "19%", "tipo": "assicurazioni", "massimale_vita": 1291.14, "massimale_infortuni": 1549.37}
    },
    
    # ==========================================
    # MUTUI E CASA PRIMA ABITAZIONE
    # ==========================================
    {
        "id": "detrazioni_interessi_mutuo_19",
        "categoria": "casa",
        "documento": "Detrazioni interessi passivi mutuo prima casa 19% per interessi passivi su mutui ipotecari per acquisto, costruzione o ristrutturazione dell'abitazione principale. Detrazione IRPEF del 19%. Riferimento normativo: Art. 15, comma 1, lettera b), del TUIR. Requisiti: mutuo ipotecario, acquisto entro 12 mesi dalla fine dei lavori (per costruzione/ristrutturazione), abitazione principale. Massimale: 4.000 euro annui di interessi (quindi detrazione massima di 760 euro annui). Recupero: in dichiarazione dei redditi. Cavillo: la detrazione spetta anche per i mutui contratti all'estero se l'immobile è in Italia e il mutuo è garantito da ipoteca.",
        "metadati": {"aliquota": "19%", "tipo": "interessi_mutuo", "massimale": 4000}
    },
    
    # ==========================================
    # CANONI DI LOCAZIONE
    # ==========================================
    {
        "id": "deduzione_canoni_locazione",
        "categoria": "casa",
        "documento": "Deduzione canoni di locazione per studenti fuori sede: deduzione dal reddito del 19% dei canoni di locazione pagati da studenti universitari fuori sede. Riferimento normativo: Art. 15, comma 1, lettera i-sexies), del TUIR. Requisiti: studente universitario iscritto a corso di laurea in comune diverso da quello di residenza, contratto di locazione registrato. Massimale: 2.633 euro annui di canone (quindi deduzione massima di 500 euro annui). Recupero: in dichiarazione dei redditi. Cavillo: la deduzione spetta anche per le residenze universitarie pubbliche e private, non solo per appartamenti in locazione.",
        "metadati": {"aliquota": "19%", "tipo": "canoni_locazione_studenti", "massimale": 2633}
    },
    
    # ==========================================
    # LAVORATORI IMPATRIATI
    # ==========================================
    {
        "id": "regime_lavoratori_impatriati",
        "categoria": "lavoro",
        "documento": "Regime lavoratori impatriati: esenzione dal 50% del reddito da lavoro per lavoratori che trasferiscono la residenza fiscale in Italia. Riferimento normativo: Art. 16, DL 34/2019 (Decreto Crescita) convertito in Legge 58/2019, modificato dalla Legge di Bilancio 2024. Requisiti: non essere stato residente in Italia nei 3 anni precedenti, trasferire la residenza in Italia, svolgere attività di lavoro dipendente o autonomo. Durata: 5 anni (prorogabili a 10 se si hanno figli o si acquista un immobile). Cavillo: la normativa è stata ridimensionata dalla Legge di Bilancio 2024: ora l'esenzione è del 50% (non più 70% o 90%) e il massimale di reddito esente è 600.000 euro annui.",
        "metadati": {"aliquota_esenzione": "50%", "tipo": "impatriati", "durata": 5, "massimale": 600000}
    }
]

# ==========================================
# FUNZIONE DI POPOLAMENTO
# ==========================================

def popola_database_completo():
    """Popola il database con tutti i bonus fiscali"""
    print("📚 Inizio popolamento database con bonus fiscali completi...")
    
    # Controlla se il database è già popolato
    if fisco_collection.count() > 0:
        print(f"⚠️  Il database contiene già {fisco_collection.count()} documenti.")
        risposta = input("Vuoi sovrascrivere? (s/n): ")
        if risposta.lower() != 's':
            print(" Operazione annullata.")
            return
    
    # Prepara i dati per ChromaDB
    documenti = [bonus["documento"] for bonus in BONUS_DATABASE]
    metadati = [bonus["metadati"] for bonus in BONUS_DATABASE]
    ids = [bonus["id"] for bonus in BONUS_DATABASE]
    
    # Inserisci nel database
    fisco_collection.add(
        documents=documenti,
        metadatas=metadati,
        ids=ids
    )
    
    print(f"✅ Database popolato con successo!")
    print(f"📊 Totale bonus inseriti: {len(BONUS_DATABASE)}")
    print(f"📂 Categorie coperte: casa, salute, famiglia, lavoro, business, auto, investimenti, energia, filantropia, previdenza")

if __name__ == "__main__":
    popola_database_completo()