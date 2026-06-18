# roboLang Compiler

Un compilatore in Python per **roboLang**, un linguaggio DSL orientato a sistemi reattivi, automazione e robotica.

Il compilatore effettua l'analisi sintattica, la validazione semantica (scope e tipi) e traduce il sorgente roboLang in codice sorgente C standard.

---

## 1. Funzionalità di roboLang

*   **Variabili Tipizzate:** Supporto per `int`, `real` (mappato a `double` in C), `bool` (`true`, `false`) e `string`.
*   **Assegnazioni:** Modifica dello stato tramite il costrutto `set`.
*   **Costrutti Reattivi:** Strutture decisionali guidate da eventi tramite `when`.
*   **Cicli:** Strutture iterative definite tramite `while`.
*   **Funzioni (Task):** Definizione di funzioni con parametri tipizzati e valore di ritorno tramite `task`.
*   **I/O Built-in:** Funzioni pre-registrate `read_int()` e `read_real()` per gestire l'input utente da console.
*   **Logging:** Output a console tramite `log()`.

---

## 2. Struttura del Progetto Organizzata

Il progetto è strutturato in modo modulare ed ordinato:

*   `main.py` - Punto di ingresso principale del compilatore.
*   `src/` - Pacchetto contenente il codice sorgente del compilatore:
    *   `src/grammar.py` - Definizione formale della grammatica Lark del linguaggio.
    *   `src/transformer.py` - Classe `ASTTransformer` per la conversione del Parse Tree in AST.
    *   `src/ast_nodes.py` - Classi che definiscono i nodi dell'Abstract Syntax Tree.
    *   `src/semantic.py` - Orchestratore dell'analisi semantica.
    *   `src/scope.py` - Gestore di scope, dichiarazioni e funzioni.
    *   `src/typechecker.py` - Controllore di tipi, compatibilità e cast impliciti.
    *   `src/codegen.py` - Generatore di codice sorgente C.
*   `examples/` - Esempi di codice scritti in roboLang:
    *   `examples/example.robo` - Programma dimostrativo delle funzionalità base.
    *   `examples/test_menu.robo` - Calcolatrice con menu aritmetico interattivo.
*   `tests/` - Suite di test del compilatore:
    *   `tests/test_compiler.py` - Suite completa di test unitari automatizzati.
*   `specifiche_e_documentazione.md` - Documentazione tecnica dettagliata delle specifiche.
*   `relazione_ai.md` - Relazione obbligatoria d'esame sull'uso dell'Intelligenza Artificiale.

---

## 3. Requisiti e Installazione

Il compilatore richiede **Python 3.x** e la libreria parser **Lark**.

Installa le dipendenze con:
```bash
pip install -r requirements.txt
```

---

## 4. Istruzioni per l'Esecuzione

### Compilazione di un sorgente roboLang
Puoi compilare un file sorgente `.robo` specificandolo come argomento:
```bash
python main.py examples/test_menu.robo
```
Il compilatore analizzerà il file e salverà il codice generato in un file con lo stesso nome ma estensione `.c` (es. `examples/test_menu.c`).

### Compilazione ed esecuzione del codice C generato
Per compilare il codice C generato in un eseguibile (richiede `gcc`):
```bash
gcc examples/test_menu.c -o test_menu.exe
.\test_menu.exe
```

---

## 5. Suite di Test Automatizzati

Puoi eseguire l'intera suite di 11 test unitari automatizzati per verificare la correttezza del compilatore:
```bash
python -m unittest tests/test_compiler.py
```
