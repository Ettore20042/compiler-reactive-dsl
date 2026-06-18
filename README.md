# DSL Compiler Project

Un piccolo compilatore in Python per un linguaggio DSL orientato a sistemi reattivi, automazione e robotica.

## Cosa fa

- legge un file sorgente del DSL
- esegue il parsing con **Lark**
- costruisce un **AST**
- fa **analisi semantica** con controllo di scope e tipi
- genera codice target in **C**

## Funzionalità supportate

- variabili tipizzate: `int`, `real`, `bool`, `string`
- assegnazioni con `set`
- condizioni reattive con `when`
- cicli con `while`
- funzioni con `task`
- chiamate di funzione
- `return`
- `log` per stampe di debug

## Struttura del progetto

- `main.py` - punto di ingresso del compilatore
- `grammar.py` - grammatica del linguaggio in Lark
- `transformer.py` - conversione del parse tree in AST
- `ast_nodes.py` - definizione dei nodi dell'AST
- `semantic.py` - orchestrazione dell'analisi semantica
- `scope.py` - controllo di scope e dichiarazioni
- `typechecker.py` - controllo dei tipi
- `codegen.py` - generazione del codice C
- `example.txt` - esempio di programma nel DSL
- `test_menu.txt` - programma DSL per il test del menu aritmetico (richiesto dai requisiti)
- `test_compiler.py` - suite di test automatizzati per il compilatore
- `specifiche_e_documentazione.md` - documentazione tecnica e specifiche formali del linguaggio
- `relazione_ai.md` - relazione sull'utilizzo dell'intelligenza artificiale per l'esame

## Requisiti

- Python 3.x
- libreria `lark`

Installa le dipendenze con:

```bash
pip install -r requirements.txt
```

## Come eseguire

Puoi compilare il file di esempio con:

```bash
python main.py
```

Oppure specificare un file diverso:

```bash
python main.py example.txt
```

## Output

Il compilatore stampa:
- il sorgente DSL letto
- l'esito dell'analisi semantica
- il codice C generato

Inoltre salva il codice C in un file `.c` con lo stesso nome del sorgente, quando possibile.

## Esempio

```text
var speed: int = 0;
var max_speed: int = 100;
var running: bool = true;

task calculateSpeed(base: int, bonus: int) -> int {
    return base + bonus;
}

when (speed < max_speed) {
    set speed = calculateSpeed(speed, 10);
}

while (running == true) {
    set running = false;
}
```

