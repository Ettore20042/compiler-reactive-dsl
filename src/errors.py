"""
Modulo: errors.py
Definisce le classi di eccezione customizzate per il compilatore roboLang,
includendo il supporto per il tracciamento di riga e colonna.
"""

class CompilerError(Exception):
    """Classe base per tutti gli errori del compilatore."""
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"[{self.line}:{self.column}] {self.message}"
        elif self.line is not None:
            return f"[Riga {self.line}] {self.message}"
        return f"{self.message}"


class SemanticError(CompilerError):
    """Errore legato allo scope o alle dichiarazioni (variabile mancante, funzione inesistente, ecc.)."""
    pass


class RoboTypeError(CompilerError):
    """Errore di tipo (incompatibilità tipi in assegnazioni, ritorni, operazioni, ecc.)."""
    pass
