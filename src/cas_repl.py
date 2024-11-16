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

  if option == "1":
    var = input("Variable of differentiation: ")
    
    simplified_ast = ast.simplify(expand_logarithms=False)
    derivative = simplified_ast.derivative(var)

    print("\n*** Derivative: ", end="")
    print(derivative.pretty_str(100))
  elif option == "2":
    simplified_ast = ast.simplify(expand_logarithms=False)
    
    variables = simplified_ast.get_variables()
    values = {}
    for var in variables:
      values[var] = int(input("Value of " + var + ": "))
    new_ast = simplified_ast.substitute_with_numbers(values)

    print("\n*** Exact result: ", end="")
    exact = new_ast.simplify()
    print(exact.pretty_str(100))
    if not exact.is_integer():
      print("*** Approximate result: ", end="")
      print(new_ast.eval())
  elif option == "3":
    # TODO: Expand_logarithms should be only used on explicit user request
    simplified_ast = ast.simplify(expand_logarithms=True) # TODO: Allow the user to configure this
    print("\n*** Simplified: ", end="")
    print(simplified_ast.pretty_str(100))
  elif option == "4":
    str = input("Expression: ")
    ast = parse_to_ast(str)
  elif option == "5":
    break