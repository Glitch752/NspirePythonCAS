from cas_parser import parse_to_ast

while True:
  str = input("Expression: ")
  ast = parse_to_ast(str)
  
  print("\nParsed:")
  print(ast.pretty_str(100))
  
  print("\nParsed simplified:")
  simplified_ast = ast.reduce()
  print(simplified_ast.pretty_str(100))
  
  print("\nDerivative for x:")
  derivative = simplified_ast.derivative("x")
  # derivative = derivative.simplify()
  print(derivative.pretty_str(100))
  
  print("\n")