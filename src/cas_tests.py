from cas_parser import parse_to_ast
from cas_ast import *
from math import *

# TODO: Proper equality checking
# Since we use set which is unordered, we can't
# directly compare values. This means we need to
# test values instead of comparing them robustly.

test_values = [
  ASTNumber(1),
  ASTNumber(0),
  ASTNumber(-1),
  ASTNumber(50),
  ASTNumber(36.2),
  ASTNumber(14.3),
  ASTNumber(8.9),
  # There's probably a better way to do this lol
]

def expect(expr, expected, message, test_vars=["x"], no_zero_input=False):
  for value in test_values:
    expected_a = expr
    expected_b = expected
    i = 0
    for var in test_vars:
      if no_zero_input and i == 0:
        i += 0.1
      
      num = ASTAdd(value, ASTNumber(i))

      expected_a = expected_a.substitute(var, num)
      expected_b = expected_b.substitute(var, num)
      i += 3.3 # Random number

    try:
      expected_a = expected_a.eval()
      expected_b = expected_b.eval()
    except Exception as e:
      print("\nError: " + str(e))
      print("Test " + message + " failed by erroring. This definitely shouldn't happen... did you forget to add a test variable?")
      print("Expected: " + str(expected))
      print("Got:      " + str(expr))
      print("")
      return
    
    if fabs(expected_a - expected_b) > 0.0001:
      print("\nTest " + message + " failed!")
      print("Expected: " + str(expected_a))
      print("Got:      " + str(expected_b))
      print("")
      return

  print("Test " + message + " passed!")

def test_eval(expr, expected, message):
  a = parse_to_ast(expr).eval()
  b = parse_to_ast(expected).eval()
  if fabs(a - b) > 0.0001:
    print("Expected: " + str(b) + " (" + expected + ")")
    print("Got:      " + str(a) + " (" + expr + ")")
    print("\n")
    raise Exception("Test " + message + " failed")
  print("Test " + message + " passed!")

# Due to the aforementioned issue with equality checking,
# this doesn't _really_ test for simplification; only
# equivalence after simplifying. It's good enough for now.
def test_simplify(full, simplified, message, test_vars=["x"], no_zero_input=False):
  expect(parse_to_ast(full).simplify(), parse_to_ast(simplified), message, test_vars, no_zero_input)

def test_derivative(expr, var, expected, message):
  expect(parse_to_ast(expr).derivative(var), parse_to_ast(expected), message, [var])

def test_pretty_str(expr, expected, message):
  a = parse_to_ast(expr).pretty_str(100)
  b = expected
  if a != b:
    print("Expected: " + b)
    print("Got:      " + a)
    print("\n")
    raise Exception("Test " + message + " failed")
  print("Test " + message + " passed!")


test_eval("1+1", "2", "Eval 1")
test_eval("2*3", "6", "Eval 2")
# Our lack of decimal support is showing here...
# Soon. Maybe.
test_eval("sin(0*10)", "0", "Eval 3")
test_eval("cos(0)", "1", "Eval 4")

test_simplify("(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x", "3*x*(−3*x + 1))", "Simplify 1")
test_simplify("x*(x+1)", "x*(x+1)", "Simplify 2")
test_simplify("x*(x+1)+x*(x+1)", "2*x*(x+1)", "Simplify 3")
test_simplify("6*x*y + 2*x*x*y", "2*x*y*(3+x)", "Simplify 4", ("x", "y"))
test_simplify("sin(3/x)", "sin(3/x)", "Simplify 5", no_zero_input=True)

test_derivative("x*x", "x", "2*x", "Derivative 1")
test_derivative("x*x*x", "x", "3*x*x", "Derivative 2")
test_derivative("sin(2*x)+1", "x", "2*cos(2*x)", "Derivative 3")
test_derivative("cos(sin(x))", "x", "−1*sin(sin(x))*cos(x)", "Derivative 4")

test_pretty_str("x*x", "xx", "Pretty string 1")
test_pretty_str("15*(x+1)", "15(x+1)", "Pretty string 2")
test_pretty_str("(2*y)/(3*x*z)", "2y/(3xz)", "Pretty string 3")
test_pretty_str("3*sin(2*x)", "3sin(2x)", "Pretty string 4")
test_pretty_str("−1*x*x", "-xx", "Pretty string 5")

print("All tests passed!")
