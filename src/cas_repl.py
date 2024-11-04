from cas_parser import parse_to_ast

while True:
    str = input("Expression: ")
    ast = parse_to_ast(str)

    print("\nParsed:")
    ast.print(100)

    print("\n\nParsed simplified:")
    simplified_ast = ast.simplify()
    simplified_ast.print(100)

    print("\n\nDerivative for x:")
    simplified_ast.derivative("x").simplify().print(100)

    print("\n\n")