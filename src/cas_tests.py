from cas_parser import parse_to_ast
from cas_ast import *
from math import *

import cas_settings
cas_settings.USE_RATIONALS = False

QUIET = False

# Some tests use test values, some use equality checking after loosely sorting the AST representation.
# There may be a more robust way to do this, but this is good enough for now.

total_tests = 0

tests_in_category = 0
current_category = ""
def test_category(name):
  global tests_in_category, current_category
  tests_in_category = 0
  current_category = name
  if not QUIET:
    print("\n" + name + ":")
def test_end_category():
  global tests_in_category, current_category
  print(
    " " + current_category + ": " + \
    str(tests_in_category) + "/" + str(tests_in_category) + " passed!"
  )
def test_pass(name):
  global total_tests, tests_in_category
  total_tests += 1
  tests_in_category += 1
  if QUIET:
    print(".", end="")
  else:
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

def test_assert_equal(a, b, name):
  assert_equal(a, b, name)
  test_pass(name)

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
  a = parse_to_ast(expr) if isinstance(expr, str) else expr
  if simplify or sort:
    a = a.simplify(sort)
  a = a.pretty_str(100)
  b = expected
  assert_equal(a, b, name)
  test_pass(name)

# Functions used to separate test categories

def rational_tests():
  test_category("Rational tests")
  from cas_rational import Rational
  test_assert_equal(Rational(Rational(1, 2), Rational(1, 3)), Rational(3, 2), "Rational construction")
  test_assert_equal(Rational(1000, 4000).numerator + Rational(1000, 4000).denominator, 5, "Rational simplification")
  test_assert_equal(Rational(-5, -3).numerator, 5, "Rational negative simplification")
  test_assert_equal(-Rational(1, 2), Rational(-1, 2), "Rational negation")
  test_assert_equal(Rational(1, 2) + Rational(1, 4), Rational(3, 4), "Rational addition")
  test_assert_equal(5 + Rational(1, 2), Rational(11, 2), "Rational addition integer")
  test_assert_equal(Rational(15) - Rational(3, 2), Rational(27, 2), "Rational subtraction")
  test_assert_equal(2 - Rational(1, 2), Rational(3, 2), "Rational subtraction integer")
  test_assert_equal(Rational(3, 2) * Rational(2, 3), Rational(1), "Rational multiplication")
  test_assert_equal(2 * Rational(3, 2), Rational(3), "Rational multiplication integer")
  test_assert_equal(Rational(3, 2) / Rational(2, 3), Rational(9, 4), "Rational division")
  test_assert_equal(3 / Rational(2, 3), Rational(9, 2), "Rational division integer")
  test_assert_equal(Rational(5, 2) % Rational(1), Rational(1, 2), "Rational modulo")
  test_assert_equal(Rational(5, 2) % 1, Rational(1, 2), "Rational modulo integer")
  test_assert_equal(Rational(5, 7) < Rational(7, 9), True, "Rational less than")
  test_assert_equal(2 < Rational(5, 2), True, "Rational less than integer")
  test_assert_equal(Rational(5, 7) <= Rational(10, 14), True, "Rational less than or equal")
  test_assert_equal(Rational(5, 7) > Rational(3, 4), False, "Rational greater than")
  test_assert_equal(Rational(5, 7) >= Rational(10, 14), True, "Rational greater than or equal")
  test_assert_equal(Rational(5, 7) == Rational(10, 14), True, "Rational equality")
  test_assert_equal(Rational(8, 4) == 2, True, "Rational integer equality")
  test_assert_equal(str(Rational(5, 7)), "5/7", "Rational string")
  test_assert_equal(str(Rational(5)), "5", "Rational string integer")
  test_end_category()
rational_tests()

def eval_tests():
  test_category("Eval parsing tests")
  test_eval_equality("1+2*2", "5", "Simple integer expression")
  test_eval_equality("5 + 3*4/2 - 1 * (2 - 3)", "12", "Order of operations")
  test_eval_equality("sin(0*10) + cos(0)", "1", "Simple function calls")
  test_end_category()
eval_tests()

def simplify_equality_tests():
  test_category("Simplify numeric equality")
  test_simplify_numeric("(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x", "3*x*(−3*x + 1))", "Polynomial common factors")
  test_simplify_numeric("x*(x+1)", "x*(x+1)", "Retain common factors")
  test_simplify_numeric("x*(x+1)+x*(x+1)", "2*x*(x+1)", "Combine identical terms")
  test_simplify_numeric("6*x*y + 2*x*x*y", "2*x*y*(3+x)", "Common factors with multiple variables", ("x", "y"))
  test_simplify_numeric("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5*x*x+x-1", "Combine multiple like terms")
  test_end_category()
simplify_equality_tests()

def derivative_tests():
  test_category("Derivative tests")
  test_derivative_numeric("x*x", "x", "2*x", "Simple product rule")
  test_derivative_numeric("x*x*x", "x", "3*x*x", "Product displaying power rule")
  test_derivative_numeric("(5*x+3) / (2*x+1)", "x", "(−1)/((2*x+1)*(2*x+1))", "Quotient rule")
  test_derivative_numeric("sin(2*x)+1", "x", "2*cos(2*x)", "Chain rule and sin derivative")
  test_derivative_numeric("cos(sin(2*x))", "x", "−2*sin(sin(2*x))*cos(2*x)", "Nested chain rule and cos derivative")
  test_end_category()
derivative_tests()

def readable_string_tests():
  test_category("Readable result string tests")
  # Will be slightly simpler when we support parsing floats
  test_result_str(ASTNumber(1.2), "1.2", "Float representation")
  test_result_str(ASTNumber(-1.0), "-1", "Integer representation")
  test_result_str("x*x", "xx", "Multiplication compaction")
  test_result_str("(15)*(x+1)", "15(x+1)", "Parentheses for precedence")
  test_result_str("(2*y)/(3*x*z)", "2y/(3xz)", "Division precedence")
  test_result_str("(5)-(3+1)", "5-(3+1)", "Subtraction precedence")
  test_result_str("3*sin(2*x)", "3sin(2x)", "Function printing")
  test_result_str("sin(r)*3", "3sin(r)", "Multiplication constant in front convention")
  test_result_str("−1*x*x", "-xx", "Negative sign placement")
  test_result_str(ASTLebiniz("v", "t", 1), "dv/dt", "Leibniz notation")
  test_result_str(ASTLebiniz("v", "t", 2), "d^2 v / dt^2", "Leibniz notation squared")
  test_end_category()
readable_string_tests()

def exact_simplification_tests():
  test_category("Exact simplification tests")
  test_result_str("5*x*x + 10*x", "5(x+2)x", "Extract common factors", simplify=True, sort=True)
  test_result_str("3*x*y + 2*x*y", "5xy", "Combine like terns", simplify=True, sort=True)
  test_result_str("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5xx+x-1", "Simplify larger polynomial", simplify=True, sort=True)
  test_result_str("sin(6/(2*x))", "sin(3/x)", "Simplify function arguments", simplify=True, sort=True)
  test_end_category()
exact_simplification_tests()

print("\nAll " + str(total_tests) + " tests passed!")