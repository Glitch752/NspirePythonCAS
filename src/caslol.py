from cas_parser import parse_to_ast
from cas_ast import ASTNumber

str = "10*ln(sin(pi*k)+log_(k^2)(k/3))+55"
ast = parse_to_ast(str)

print(ast.pretty_str(100), end=" = ")
print(ast.simplify(expand_logarithms=False).pretty_str(100))

print("")
print(ast.derivative("k").pretty_str(100))
print(ast.simplify(expand_logarithms=False).derivative("k").pretty_str(100))