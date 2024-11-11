from cas_parser import parse_to_ast

str = "3*x*x - 3*x - 9"
ast = parse_to_ast(str)
print(ast.simplify().pretty_str(100))