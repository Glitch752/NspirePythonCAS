from cas_parser import parse_to_ast
from cas_ast import *
from math import *

import cas_settings
cas_settings.USE_RATIONALS = False

# Some tests use test values, some use equality checking after loosely sorting the AST representation.
# There may be a more robust way to do this, but this is good enough for now.

total_tests = 0
def test_pass(name):
  global total_tests
  total_tests += 1
  print("  Test '" + name + "' passed!")

def assert_equal(a, b, name):
  if isinstance(a, float) and isinstance(b, float):
    equal = fabs(a - b) < 0.0001
  else:
    equal = a == b
  
  if not equal:
    print(name)
    print("Expected: " + str(b))
    print("Got:      " + str(a))
    print("")
    raise Exception("Test '" + name + "' failed: " + str(a) + " != " + str(b))

test_values = [ ASTNumber(1), ASTNumber(0), ASTNumber(-1), ASTNumber(50), ASTNumber(36.2), ASTNumber(14.3), ASTNumber(8.9) ]
def test_expression_numeric(expr, expected, name, test_vars=["x"], no_zero_input=False):
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
      print("Test '" + name + "' failed by erroring. This definitely shouldn't happen... did you forget to add a test variable?")
      print("")
      raise Exception("Test '" + name + "' failed")
    
    assert_equal(expected_a, expected_b, name)

  test_pass(name)

def test_eval_equality(expr, expected, name):
  a = parse_to_ast(expr).eval()
  b = parse_to_ast(expected).eval()
  assert_equal(a, b, name)
  test_pass(name)

# This doesn't test for proper simplification; only
# equivalence after simplifying. It's good enough for now.
def test_simplify_numeric(full, simplified, message, test_vars=["x"], no_zero_input=False):
  test_expression_numeric(parse_to_ast(full).simplify(), parse_to_ast(simplified), message, test_vars, no_zero_input)

def test_derivative_numeric(expr, var, expected, message):
  test_expression_numeric(parse_to_ast(expr).derivative(var), parse_to_ast(expected), message, [var])

def test_result_str(expr, expected, name, simplify=False, sort=False):
  a = parse_to_ast(expr)
  if simplify or sort:
    a = a.simplify(sort)
  a = a.pretty_str(100)
  b = expected
  assert_equal(a, b, name)
  test_pass(name)

# Functions used to separate test categories

def eval_tests():
  print("\nSimple eval equality")
  test_eval_equality("1+2*2", "5", "Simple integer expression")
  # Our lack of decimal support is showing here...
  test_eval_equality("sin(0*10) + cos(0)", "1", "Simple function calls")
eval_tests()

def simplify_equality_tests():
  print("\nSimplify equality")
  test_simplify_numeric("(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x", "3*x*(−3*x + 1))", "Polynomial common factors")
  test_simplify_numeric("x*(x+1)", "x*(x+1)", "Retain common factors")
  test_simplify_numeric("x*(x+1)+x*(x+1)", "2*x*(x+1)", "Combine identical terms")
  test_simplify_numeric("6*x*y + 2*x*x*y", "2*x*y*(3+x)", "Common factors with multiple variables", ("x", "y"))
  test_simplify_numeric("sin(6/(2*x))", "sin(3/x)", "Simplification in functions", no_zero_input=True)
  test_simplify_numeric("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5*x*x+x-1", "Combine multiple like terms")
simplify_equality_tests()

def derivative_tests():
  print("\nDerivative tests")
  test_derivative_numeric("x*x", "x", "2*x", "Simple product rule")
  test_derivative_numeric("x*x*x", "x", "3*x*x", "Product displaying power rule")
  test_derivative_numeric("(5*x+3) / (2*x+1)", "x", "(−1)/((2*x+1)*(2*x+1))", "Quotient rule")
  test_derivative_numeric("sin(2*x)+1", "x", "2*cos(2*x)", "Chain rule and sin derivative")
  test_derivative_numeric("cos(sin(2*x))", "x", "−2*sin(sin(2*x))*cos(2*x)", "Nested chain rule and cos derivative")
derivative_tests()

def readable_string_tests():
  print("\nReadable result string tests")
  test_result_str("x*x", "xx", "Multiplication compaction")
  test_result_str("(15)*(x+1)", "15(x+1)", "Parentheses for precedence")
  test_result_str("(2*y)/(3*x*z)", "2y/(3xz)", "Division and precedence")
  test_result_str("3*sin(2*x)", "3sin(2x)", "Function printing")
  test_result_str("−1*x*x", "-xx", "Negative sign placement")
readable_string_tests()

def exact_simplification_tests():
  print("\nExact simplification tests")
  test_result_str("5*x*x + 10*x", "5(x+2)x", "Extract common factors", simplify=True, sort=True)
  test_result_str("3*x*y + 2*x*y", "5xy", "Combine like terns", simplify=True, sort=True)
  test_result_str("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5xx+x-1", "Simplify larger polynomial", simplify=True, sort=True)
exact_simplification_tests()

print("\nAll " + str(total_tests) + " tests passed!")