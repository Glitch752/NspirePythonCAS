from cas_parser import parse_to_ast

# str = "sin(3*x-2*cos(2/x))"
# str = input("Expression: ")
str = "x*x*x"
# str = "(−6*x)+(8*x)-(4*x+2*x*y)"
ast = parse_to_ast(str)

print("Parsed:")
print(ast.pretty_str(100))

print("\nParsed simplified:")
simplified_ast = ast.reduce()
print(simplified_ast.pretty_str(100))

print("\nDerivative for x:")
print(simplified_ast.derivative("x").reduce().pretty_str(100))