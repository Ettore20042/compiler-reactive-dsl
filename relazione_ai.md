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

### 2.2 Sviluppo, Correzione del Codice (Bug Fixing) e Nuove Funzionalità
*   **Risoluzione del Bug di Parsing:** Durante la revisione del parser Lark in [src/transformer.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/transformer.py), l'AI ha individuato che le espressioni con operatori multipli (es. `1 + 2 + 3`) venivano troncate a causa di una scorretta gestione del transformer (`BinOp(args[0], str(args[1]), args[2])`). L'AI ha proposto e implementato un algoritmo di folding sinistro-associativo (`_fold_binops`) che ha risolto definitivamente il problema.
*   **Risoluzione del Bug del Type Checker per Variabili Locali:** Nello sviluppo dei test complessi, l'AI ha individuato una mancanza nel modulo [src/typechecker.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/typechecker.py) in cui le variabili locali dichiarate dentro i task con `var` non venivano registrate nella tabella dei simboli del type checker, causando crash di tipo `KeyError` nelle istruzioni successive. L'AI ha corretto il metodo `visit_VarDecl` per registrare opportunamente la variabile nello scope locale corrente del type checker.
*   **Estensione delle Funzionalità (Built-in di Input):** L'AI ha suggerito di implementare le funzioni di lettura `read_int()` e `read_real()` come funzioni pre-registrate nello scope globale anziché stravolgere la sintassi della grammatica. Ha poi guidato la loro integrazione nei moduli [src/scope.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/scope.py), [src/typechecker.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/typechecker.py) e [src/codegen.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/codegen.py).
*   **Correzione di 5 Bug Critici Successivi:**
    - **Variabili non dichiarate in sotto-espressioni**: Risolto in [src/scope.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/scope.py) aggiungendo un metodo ricorsivo `_check_expr` per scovare variabili non dichiarate annidate in espressioni complesse, evitando KeyError imprevisti nel TypeChecker.
    - **Type Soundness Aritmetica**: Modificato `expr_type_BinOp` in [src/typechecker.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/typechecker.py) per sollevare un errore semantico chiaro in caso di operazioni illegittime come `"abc" + 5`.
    - **Shadowing dei Parametri**: Sistemato lo [ScopeAnalyzer](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/scope.py#L80-L95) affinché controlli i parametri duplicati dei task usando un set locale, rendendo lecito lo shadowing di variabili globali senza generare falsi errori di "parametro duplicato".
    - **Forward Declarations in C**: Aggiornato [src/codegen.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/codegen.py) per inserire i prototipi di tutti i task in cima al file C generato, risolvendo il problema delle chiamate a funzioni definite successivamente (che causavano errori di "implicit declaration" in `gcc`).
    - **Notazione Esponenziale**: Sistemata la funzione `number()` in [src/transformer.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/transformer.py) per riconoscere esponenziali come `5e3` come tipo `real` (cercando la presenza di `'e'` o `'E'`).
*   **Integrazione Supporto per i Commenti**: L'AI ha supportato la modifica della grammatica formale in [src/grammar.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/src/grammar.py#L71-L75) introducendo le direttive `%import common.SH_COMMENT` e `%ignore SH_COMMENT` per consentire l'utilizzo di commenti a riga singola con `#` nel codice sorgente roboLang.

### 2.3 Generazione dei Casi di Test ed Esempi Algoritmici
*   L'AI ha generato il file [examples/test_menu.robo](file:///C:/Users/ettor/PycharmProjects/PythonProject1/examples/test_menu.robo) che implementa interamente i requisiti del punto 4 della proposta (un programma interattivo con menu, input di interi/double, operazioni aritmetiche gestite tramite funzioni, e ciclo di continuazione).
*   Ha generato ed esteso la suite completa di test di unità in Python [tests/test_compiler.py](file:///C:/Users/ettor/PycharmProjects/PythonProject1/tests/test_compiler.py) per garantire la non-regressione, portando i casi di test totali a **17** (aggiungendo test per i 5 bug fix e per la validazione dei commenti).
*   Ha creato tre programmi di esempio aggiuntivi per dimostrare le capacità del DSL: [examples/multiples.robo](file:///C:/Users/ettor/PycharmProjects/PythonProject1/examples/multiples.robo), [examples/fibonacci.robo](file:///C:/Users/ettor/PycharmProjects/PythonProject1/examples/fibonacci.robo) (generazione iterativa di successioni), e [examples/factorial.robo](file:///C:/Users/ettor/PycharmProjects/PythonProject1/examples/factorial.robo) (task ricorsivi).

---

## 3. Valutazione dell'Efficacia dell'AI

### 3.1 Vantaggi Riscontrati
*   **Rapidità di Diagnosi**: L'AI ha individuato immediatamente la causa del troncamento delle espressioni matematiche lunghe (il bug nel transformer Lark), che ad un'analisi visiva superficiale sarebbe potuto sfuggire.
*   **Accuratezza del Codice C Generato**: La stesura manuale dei generatori di stringhe C in `src/codegen.py` può essere soggetta a errori di sintassi C. L'AI ha generato modelli di codice C robusti che compilano con `gcc` senza alcun warning.
*   **Sicurezza da Regressioni**: La stesura assistita dei 17 test unitari ha garantito che l'introduzione di nuove funzionalità (come i commenti `#`) non rompesse gli stadi preesistenti di analisi semantica o parsing.

### 3.2 Svantaggi e Limitazioni Riscontrati
*   **Necessità di Supervisione Umana**: L'AI propone soluzioni standard (come l'uso di `float` per i numeri reali), ma è stato necessario l'intervento umano per ricalibrare la scelta su `double` (modificando il format `scanf` in `%lf`), come esplicitamente richiesto dalla traccia del docente.
*   **Controllo delle Esecuzioni**: L'esecuzione di comandi terminali (come l'uso di `gcc` o `python main.py`) richiede costante validazione umana per assicurarsi che i percorsi dei file e i parametri di compilazione siano configurati correttamente.

---

## 4. Lezioni Apprese

*   **L'AI come Pair Programmer**: L'utilizzo dell'AI non deve essere inteso come un sostituto dello studio del funzionamento dei compilatori. Al contrario, collaborare con l'AI richiede una conoscenza approfondita di concetti come l'analisi semantica, la symbol table e la gestione degli scope, altrimenti non si sarebbe in grado di validare e integrare con successo le modifiche da essa proposte.
*   **Importanza dei Test**: L'introduzione di modifiche complesse (come il folding dell'AST) deve sempre essere accompagnata da test automatizzati per scongiurare regressioni silenziose.
