# Relazione sull'Utilizzo dell'Intelligenza Artificiale (AI)

**Corso:** Elementi di Ingegneria dei Linguaggi di Programmazione  
**Professore:** G. Costagliola  
**Linguaggio Sviluppato:** roboLang  
**A.A.:** 2025/26  

---

## 1. Strumenti Utilizzati
Per la progettazione, lo sviluppo, la correzione e la documentazione del compilatore del linguaggio **roboLang**, è stato impiegato l'assistente basato su LLM **Antigravity** (Gemini 3.5 Flash / Gemini 1.5 Pro).

---

## 2. Tipologia di Utilizzo e Attività Svolte

L'assistente AI è stato integrato in varie fasi del ciclo di vita dello sviluppo del software:

### 2.1 Analisi delle Specifiche e Gap Analysis
*   L'AI ha letto e analizzato il file ministeriale contenente le modalità d'esame (`contenuto proposta`).
*   Ha effettuato un confronto automatico tra i requisiti d'esame e i file sorgenti presenti nel progetto, evidenziando le mancanze critiche (assenza di input utente, assenza di test suite, assenza di relazioni tecniche).

### 2.2 Sviluppo e Correzione del Codice (Bug Fixing)
*   **Risoluzione del Bug di Parsing:** Durante la revisione del parser Lark in [src/transformer.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/transformer.py), l'AI ha individuato che le espressioni con operatori multipli (es. `1 + 2 + 3`) venivano troncate a causa di una scorretta gestione del transformer (`BinOp(args[0], str(args[1]), args[2])`). L'AI ha proposto e implementato un algoritmo di folding sinistro-associativo (`_fold_binops`) che ha risolto definitivamente il problema.
*   **Risoluzione del Bug del Type Checker per Variabili Locali:** Nello sviluppo dei test complessi, l'AI ha individuato una mancanza nel modulo [src/typechecker.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/typechecker.py) in cui le variabili locali dichiarate dentro i task con `var` non venivano registrate nella tabella dei simboli del type checker, causando crash di tipo `KeyError` nelle istruzioni successive. L'AI ha corretto il metodo `visit_VarDecl` per registrare opportunamente la variabile nello scope locale corrente del type checker.
*   **Estensione delle Funzionalità (Built-in di Input):** L'AI ha suggerito di implementare le funzioni di lettura `read_int()` e `read_real()` come funzioni pre-registrate nello scope globale anziché stravolgere la sintassi della grammatica. Ha poi guidato la loro integrazione nei moduli [src/scope.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/scope.py), [src/typechecker.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/typechecker.py) e [src/codegen.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/codegen.py).

### 2.3 Generazione dei Casi di Test
*   L'AI ha generato il file [examples/test_menu.robo](file:///C:/Users/ettor/PycharmProjects/PythonProject1/examples/test_menu.robo) che implementa interamente i requisiti del punto 4 della proposta (un programma interattivo con menu, input di interi/double, operazioni aritmetiche gestite tramite funzioni, e ciclo di continuazione).
*   Ha generato una suite completa di test di unità in Python [tests/test_compiler.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/tests/test_compiler.py) per garantire la non-regressione delle modifiche apportate, incrementando il numero di test fino a 11 test case completi che coprono l'intero spettro delle funzionalità.

---

## 3. Valutazione dell'Efficacia dell'AI

### 3.1 Vantaggi Riscontrati
*   **Rapidità di Diagnosi:** L'AI ha individuato immediatamente la causa del troncamento delle espressioni matematiche lunghe (il bug nel transformer Lark), che ad un'analisi visiva superficiale sarebbe potuto sfuggire.
*   **Accuratezza del Codice C Generato:** La stesura manuale dei generatori di stringhe C in `src/codegen.py` può essere soggetta a errori di sintassi C (come dimenticare il punto e virgola `;` o il mapping dei tipi). L'AI ha generato modelli di codice C robusti che compilano con `gcc` senza alcun warning.
*   **Velocità nello Scrivere Test:** La generazione della suite `unittest` ha permesso di testare i corner case semantici in pochissimi secondi.

### 3.2 Svantaggi e Limitazioni Riscontrati
*   **Necessità di Supervisione Umana:** L'AI propone soluzioni standard (come l'uso di `float` per i numeri reali), ma è stato necessario l'intervento umano per ricalibrare la scelta su `double` (modificando il format `scanf` in `%lf`), come esplicitamente richiesto dalla traccia del docente.
*   **Comprensione del Flusso Asincrono:** Durante l'esecuzione di comandi asincroni (come la compilazione tramite terminale), è fondamentale che lo sviluppatore mantenga il controllo dello stato per evitare conflitti o letture di file parzialmente scritti.

---

## 4. Lezioni Apprese

*   **L'AI come Pair Programmer:** L'utilizzo dell'AI non deve essere inteso come un sostituto dello studio del funzionamento dei compilatori. Al contrario, collaborare con l'AI richiede una conoscenza approfondita di concetti come l'analisi semantica, la symbol table e la gestione degli scope, altrimenti non si sarebbe in grado di validare e integrare con successo le modifiche da essa proposte.
*   **Importanza dei Test:** L'introduzione di modifiche complesse (come il folding dell'AST) deve sempre essere accompagnata da test automatizzati per scongiurare regressioni silenziose.
