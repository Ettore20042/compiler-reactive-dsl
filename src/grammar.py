"""
Modulo: grammar.py
Definisce la grammatica del linguaggio roboLang utilizzando la sintassi di Lark.
"""
grammar = """
start: (task_decl | stmt)*

task_decl: "task" CNAME "(" param_list? ")" ("->" TYPE)? "{" stmt* "}"
param_list: param ("," param)*
param: CNAME ":" TYPE

?stmt: var_decl
     | set_stmt
     | when_stmt
     | while_stmt
     | call_stmt
     | return_stmt
     | log_stmt

var_decl: "var" CNAME ":" TYPE "=" expr ";"
set_stmt: "set" CNAME "=" expr ";"
when_stmt: "when" "(" expr ")" "{" stmt* "}"
while_stmt: "while" "(" expr ")" "{" stmt* "}"
call_stmt: CNAME "(" expr_list? ")" ";"
return_stmt: "return" expr? ";"
log_stmt: "log" "(" expr ")" ";"

TYPE: "int" | "real" | "bool" | "string"

?expr: comp_expr
expr_list: expr ("," expr)*

?comp_expr: arith_expr (OP_REL arith_expr)*
?arith_expr: term (OP_ADD term)*
?term: factor (OP_MUL factor)*

?factor: NUMBER          -> number
       | call_expr
       | CNAME           -> var
       | ESCAPED_STRING  -> string
       | "true"          -> true_val
       | "false"         -> false_val
       | "(" expr ")"

call_expr: CNAME "(" expr_list? ")"

OP_ADD: "+" | "-"
OP_MUL: "*" | "/"
OP_REL: ">" | "<" | ">=" | "<=" | "==" | "!="

%import common.CNAME
%import common.SIGNED_NUMBER -> NUMBER
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""
