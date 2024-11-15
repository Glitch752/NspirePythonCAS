from cas_parser import parse_to_ast
from cas_ast import ASTNumber

str = "log_(2*x+1)(8)"
ast = parse_to_ast(str)
print(ast.pretty_str(100))

print(ast.substitute("x", ASTNumber(2)).simplify().pretty_str(100))