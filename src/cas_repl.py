from cas_parser import parse_to_ast

str = input("Expression: ")
ast = parse_to_ast(str)

while True:
  print("\nCurrent expression: ", end="")
  print(ast.pretty_str(100))
  
  print("1. Derivative")
  print("2. Evaluate")
  print("3. Simplify")
  print("4. New expression")
  print("5. Exit")

  option = input("Option: ")

  print("\n")
  simplified_ast = ast.simplify()
  if option == "1":
    var = input("Variable of differentiation: ")
    derivative = simplified_ast.derivative(var)

    print("\n*** Derivative: ", end="")
    print(derivative.pretty_str(100))
  elif option == "2":
    variables = simplified_ast.get_variables()
    values = {}
    for var in variables:
      values[var] = float(input(f"Value of {var}: "))
    new_ast = simplified_ast.substitute_with_numbers(values)

    print("\n*** Approximate result: ", end="")
    print(new_ast.eval())
    print("\n*** Exact result: ", end="")
    print(new_ast.simplify().pretty_str(100))
  elif option == "3":
    print("\n*** Simplified: ", end="")
    print(simplified_ast.pretty_str(100))
  elif option == "4":
    str = input("Expression: ")
    ast = parse_to_ast(str)
    simplified_ast = ast.simplify()
  elif option == "5":
    break