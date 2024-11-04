from cas_parser import parse_to_ast

# str = "sin(3*x-2*cos(2/x))"
# str = input("Expression: ")
str = "(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x"
# str = "(−6*x)+(8*x)-(4*x+2*x*y)"
ast = parse_to_ast(str)

print("Parsed:")
ast.print(100)

print("\n\nParsed simplified:")
simplified_ast = ast.simplify()
simplified_ast.print(100)

print("\n\nDerivative for x:")
simplified_ast.derivative("x").simplify().print(100)