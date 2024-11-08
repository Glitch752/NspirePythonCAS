from cas_parser import parse_to_ast
from cas_ast import *
from math import *

import cas_settings
cas_settings.USE_RATIONALS = False

# Some tests use test values, some use equality checking after loosely sorting the AST representation.
# There may be a more robust way to do this, but this is good enough for now.

test_values = [ ASTNumber(1), ASTNumber(0), ASTNumber(-1), ASTNumber(50), ASTNumber(36.2), ASTNumber(14.3), ASTNumber(8.9) ]
def test_expression_numeric(expr, expected, message, test_vars=["x"], no_zero_input=False):
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
      raise Exception("Test " + message + " failed")
    
    if fabs(expected_a - expected_b) > 0.0001:
      print("\nTest " + message + " failed!")
      print("Expected: " + str(expected_a))
      print("Got:      " + str(expected_b))
      print("")
      raise Exception("Test " + message + " failed")

  print("Test " + message + " passed!")

def test_eval_equality(expr, expected, message):
  a = parse_to_ast(expr).eval()
  b = parse_to_ast(expected).eval()
  if fabs(a - b) > 0.0001:
    print("Expected: " + str(b) + " (" + expected + ")")
    print("Got:      " + str(a) + " (" + expr + ")")
    print("")
    raise Exception("Test " + message + " failed")
  print("Test " + message + " passed!")

# This doesn't test for proper simplification; only
# equivalence after simplifying. It's good enough for now.
def test_simplify_numeric(full, simplified, message, test_vars=["x"], no_zero_input=False):
  test_expression_numeric(parse_to_ast(full).simplify(), parse_to_ast(simplified), message, test_vars, no_zero_input)

def test_derivative_numeric(expr, var, expected, message):
  test_expression_numeric(parse_to_ast(expr).derivative(var), parse_to_ast(expected), message, [var])

def test_pretty_str(expr, expected, message, simplify=False, sort=False):
  a = parse_to_ast(expr)
  if simplify or sort:
    a = a.simplify(sort)
  a = a.pretty_str(100)
  b = expected
  if a != b:
    print("Expected: " + b)
    print("Got:      " + a)
    print("\n")
    raise Exception("Test " + message + " failed")
  print("Test " + message + " passed!")

# TODO: Better test names...

test_eval_equality("1+1", "2", "Eval 1")
test_eval_equality("2*3", "6", "Eval 2")
# Our lack of decimal support is showing here...
# Soon. Maybe.
test_eval_equality("sin(0*10)", "0", "Eval 3")
test_eval_equality("cos(0)", "1", "Eval 4")

test_simplify_numeric("(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x", "3*x*(−3*x + 1))", "Simplify 1")
test_simplify_numeric("x*(x+1)", "x*(x+1)", "Simplify 2")
test_simplify_numeric("x*(x+1)+x*(x+1)", "2*x*(x+1)", "Simplify 3")
test_simplify_numeric("6*x*y + 2*x*x*y", "2*x*y*(3+x)", "Simplify 4", ("x", "y"))
test_simplify_numeric("sin(3/x)", "sin(3/x)", "Simplify 5", no_zero_input=True)
test_simplify_numeric("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5*x*x+x-1", "Simplify 6")

test_derivative_numeric("x*x", "x", "2*x", "Derivative 1")
test_derivative_numeric("x*x*x", "x", "3*x*x", "Derivative 2")
test_derivative_numeric("sin(2*x)+1", "x", "2*cos(2*x)", "Derivative 3")
test_derivative_numeric("cos(sin(x))", "x", "−1*sin(sin(x))*cos(x)", "Derivative 4")

test_pretty_str("x*x", "xx", "Pretty string 1")
test_pretty_str("15*(x+1)", "15(x+1)", "Pretty string 2")
test_pretty_str("(2*y)/(3*x*z)", "2y/(3xz)", "Pretty string 3")
test_pretty_str("3*sin(2*x)", "3sin(2x)", "Pretty string 4")
test_pretty_str("−1*x*x", "-xx", "Pretty string 5")

test_pretty_str("5*x*x + 10*x", "5(x+2)x", "Pretty string 6", simplify=True, sort=True)
test_pretty_str("3*x*y + 2*x*y", "5xy", "Pretty string 7", simplify=True, sort=True)
test_pretty_str("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5xx+x-1", "Pretty string 8", simplify=True, sort=True)

print("All tests passed!")
