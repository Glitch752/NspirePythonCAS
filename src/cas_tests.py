from cas_parser import parse_to_ast
from cas_ast import *
from math import *

import cas_settings
cas_settings.USE_RATIONALS = True

QUIET = False
COLLAPSE_CATEGORIES = False
TIME_TESTS = True

# Some tests use test values, some use equality checking after loosely sorting the AST representation.
# There may be a more robust way to do this, but this is good enough for now.

total_tests = 0

tests_in_category = 0
current_category = ""

current_collapsed_category = None
collapsed_category_tests = 0

category_start_time = None

def test_category(name):
  global tests_in_category, current_category, category_start_time
  tests_in_category = 0
  current_category = name
  if not QUIET:
    print("\n" + name + ":")
  if TIME_TESTS:
    from time import time
    category_start_time = time()
def test_end_category():
  global tests_in_category, current_category, current_collapsed_category, category_start_time
  current_collapsed_category = None
  if QUIET:
    print("")
  print(
    " " + current_category + ": " + \
    str(tests_in_category) + "/" + str(tests_in_category) + " passed!",
    end=""
  )
  if TIME_TESTS:
    from time import time
    print(" Time: " + str(round(time() - category_start_time, 2)) + "s", end="")
  print("")

def test_pass(name):
  global total_tests, tests_in_category, current_collapsed_category, collapsed_category_tests
  total_tests += 1
  tests_in_category += 1
  if current_collapsed_category != None:
    collapsed_category_tests += 1
    return
  if QUIET:
    print(".", end="")
  else:
    print("  Test '" + name + "' passed!")

def test_collapsed_category(name):
  global current_collapsed_category, collapsed_category_tests
  if not COLLAPSE_CATEGORIES:
    return
  current_collapsed_category = name
  collapsed_category_tests = 0
def test_end_collapsed_category():
  global current_collapsed_category, collapsed_category_tests
  if not COLLAPSE_CATEGORIES:
    return
  print("  ... " + str(collapsed_category_tests) + " '" + current_collapsed_category + "' collapsed tests passed")
  current_collapsed_category = None

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

# We keep test values in a relatively small range to avoid massive numbers for certain tests.
# TODO: Overriding the test value list for particular test types?
test_values = [ ASTNumber(1), ASTNumber(0), ASTNumber(-1), ASTNumber(2.1), ASTNumber(4.2), ASTNumber(3.3), ASTNumber(-2.9), ASTNumber(1.7) ]
def test_expression_numeric(expr, expected, name, test_vars=["x"], filter_input=None):
  skipped = 0
  
  for value in test_values:
    expected_a = expr
    expected_b = expected
    
    i = 0
    stopped = False
    
    for var in test_vars:
      num = ASTAdd(value, ASTNumber(i))
      if filter_input != None and not filter_input(num.eval()):
        stopped = True
        break
      
      expected_a = expected_a.substitute(var, num)
      expected_b = expected_b.substitute(var, num)
      i += 1.3 # Random number
    
    if stopped:
      skipped += 1
      continue

    try:
      expected_a = expected_a.eval()
      expected_b = expected_b.eval()
    except Exception as e:
      print("\nError: " + str(e))
      print("Test '" + name + "' failed by erroring. This definitely shouldn't happen... did you forget to add a test variable?")
      print("")
      raise Exception("Test '" + name + "' failed")
    
    assert_equal(expected_a, expected_b, name)

  if skipped > len(test_values) / 2:
    print("Test '" + name + "' failed by skipping too many values. This is probably a problem with the test.")
    print("Skipped: " + str(skipped) + "/" + str(len(test_values)))
    print("")
    raise Exception("Test '" + name + "' failed")

  test_pass(name)

def test_result_str(expr, expected, name, simplify=False, sort=False):
  a = parse_to_ast(expr) if isinstance(expr, str) else expr
  if simplify or sort:
    a = a.simplify(sort)
  a = a.pretty_str(100)
  b = expected
  assert_equal(a, b, name)
  test_pass(name)



# --------------------
# Tests start here
# --------------------

def rational_tests():
  test_category("Rational tests")
  from cas_rational import Rational, gcd, fast_2_gcd
  
  test_assert_equal(Rational(Rational(1, 2), Rational(1, 3)), Rational(3, 2), "Rational construction")
  test_assert_equal(Rational(1000, 4000).numerator + Rational(1000, 4000).denominator, 5, "Rational simplification")
  test_assert_equal(Rational(-5, -3).numerator, 5, "Rational negative simplification")
  
  test_collapsed_category("Rational operations")
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
  test_assert_equal(Rational(5, 7) <= Rational(10, 14), True, "Rational less than or equal")
  test_assert_equal(Rational(5, 7) > Rational(3, 4), False, "Rational greater than")
  test_assert_equal(Rational(5, 7) >= Rational(10, 14), True, "Rational greater than or equal")
  test_assert_equal(Rational(5, 7) == Rational(10, 14), True, "Rational equality")
  test_assert_equal(Rational(8, 4) == 2, True, "Rational integer equality")
  test_assert_equal(str(Rational(5, 7)), "5/7", "Rational string")
  test_assert_equal(str(Rational(5)), "5", "Rational string integer")
  test_end_collapsed_category()

  test_assert_equal(gcd([5, 10, 15]), 5, "GCD multiple numbers")
  test_assert_equal(gcd([0, 3, 5]), 1, "GCD zero in list")
  test_assert_equal(gcd([Rational(3), Rational(6), Rational(9)]), 3, "GCD rationals")
  test_assert_equal(gcd([Rational(1), Rational(1), Rational(3)]), 1, "GCD rationals no common factor")
  test_assert_equal(fast_2_gcd(5, 10), 5, "Fast GCD")
  test_assert_equal(fast_2_gcd(0, 3), 3, "Fast GCD zero")
  test_assert_equal(fast_2_gcd(Rational(3), Rational(6)), 3, "Fast GCD rationals")

  # exact_rational_log tests
  from cas_rational import exact_rational_log, prime_factors
  
  test_collapsed_category("Prime factorization")
  test_assert_equal(prime_factors(1), {}, "Prime factorization of 1")
  test_assert_equal(prime_factors(2), {2: 1}, "Prime factorization of 2")
  test_assert_equal(prime_factors(3), {3: 1}, "Prime factorization of 3")
  test_assert_equal(prime_factors(6), {2: 1, 3: 1}, "Prime factorization of 6")
  test_assert_equal(prime_factors(60), {2: 2, 3: 1, 5: 1}, "Prime factorization of 60") # 2^2 * 3 * 5
  test_assert_equal(prime_factors(27), {3: 3}, "Prime factorization of 27")
  test_end_collapsed_category()

  test_collapsed_category("Exact rational logarithm simplification")
  test_assert_equal(exact_rational_log(Rational(1), Rational(1)), Rational(0), "log_1(1) = 0")
  test_assert_equal(exact_rational_log(Rational(5), Rational(1)), None, "log_1(5) = None")
  test_assert_equal(exact_rational_log(Rational(1), Rational(2, 19)), Rational(0), "log_2/19(1) = 0")
  test_assert_equal(exact_rational_log(Rational(2, 3), Rational(2, 3)), Rational(1), "log_2/3(2/3) = 1")
  test_assert_equal(exact_rational_log(Rational(3, 2), Rational(2, 3)), Rational(-1), "log_2/3(3/2) = -1")
  test_assert_equal(exact_rational_log(Rational(27), Rational(1, 3)), Rational(-3), "log_1/3(27) = -3")
  test_assert_equal(exact_rational_log(Rational(3), Rational(9)), Rational(1, 2), "log_9(3) = 1/2")
  test_assert_equal(exact_rational_log(Rational(0), Rational(1)), None, "log_1(0) = None")
  test_assert_equal(exact_rational_log(Rational(1), Rational(0)), None, "log_0(1) = None")
  test_assert_equal(exact_rational_log(Rational(-1), Rational(2)), None, "log_2(-1) = None")
  test_assert_equal(exact_rational_log(Rational(1, 4), Rational(2)), Rational(-2), "log_2(1/4) = -2")
  test_assert_equal(exact_rational_log(Rational(5), Rational(2)), None, "log_2(5) = None") # Irrational
  test_assert_equal(exact_rational_log(Rational(4), Rational(-2)), None, "log_-2(4) = None")
  test_assert_equal(exact_rational_log(Rational(100), Rational(10)), Rational(2), "log_10(100) = 2") # Large numbers, somewhat slow
  test_assert_equal(exact_rational_log(Rational(2, 5), Rational(4, 25)), Rational(1, 2), "log_4/25(2/5) = 1/2")
  test_end_collapsed_category()

  test_end_category()
rational_tests()

def is_constant_tests():
  def test_is_constant(expr, expected, name):
    a = parse_to_ast(expr).is_constant()
    assert_equal(a, expected, name)
    test_pass(name)
    
  test_category("Is constant tests")
  test_is_constant("5", True, "Constant number")
  test_is_constant("x", False, "Variable")
  test_is_constant("x+5", False, "Addition")
  test_is_constant("5*sin(3+4*(1/2))", True, "Function call")
  test_is_constant("5*sin(3+4*(1/2)*x)", False, "Deeply nested variable")
  test_is_constant("3*log_(2*x)(5*3+2^3)", False, "Logarithm base variable")
  test_is_constant("3*ln(5*3+2^x)", False, "Logarithm argument and power variable")
  test_end_category()
is_constant_tests()

def eval_tests():
  def test_eval_equality(expr, expected, name):
    a = parse_to_ast(expr).eval()
    b = parse_to_ast(expected).eval()
    assert_equal(a, b, name)
    test_pass(name)
  
  test_category("Eval parsing tests")
  # LOL we don't support decimals yet so here's our workaround
  test_eval_equality("pi", "3141592653589793/1000000000000000", "Pi")
  test_eval_equality("E", "2718281828459045/1000000000000000", "Euler's number")

  test_eval_equality("1+2*2", "5", "Simple integer expression")
  test_eval_equality("5 + 3*4/2 - 1 * (2 - 3)", "12", "Order of operations")
  test_eval_equality("sin(0*10) + cos(0)", "1", "Simple function calls")
  test_eval_equality("sqrt(4)", "2", "Square root")
  test_eval_equality("cbrt(8)", "2", "Cube root")
  test_eval_equality("sqrt(1/sqrt(16))", "1/2", "Square root rational")
  test_eval_equality("10^2", "100", "Exponentiation")
  test_eval_equality("5^2^3", "390625", "Exponentiation associativity")
  test_eval_equality("(2/3)^3", "8/27", "Exponentiation rational")
  test_eval_equality("2^(−3)", "1/8", "Negative exponent")
  test_eval_equality("log(100)+ln(E*E)", "4", "Logarithms")
  # This is kind of a weird way to test this, but it works for now
  test_eval_equality("sin(pi/2) + cos(pi/2) - tan(pi/4) - csc(pi/2) + sec(pi) - cot(pi/4)", "−3", "Trigonometric functions")
  test_end_category()
eval_tests()

def simplify_equality_tests():
  # This doesn't test for proper simplification; only equivalence after simplifying.
  def test_simplify_numeric(full, simplified, message, test_vars=["x"], filter_input=None):
    test_expression_numeric(parse_to_ast(full).simplify(), parse_to_ast(simplified), message, test_vars, filter_input)
  
  test_category("Simplify numeric equality")
  test_simplify_numeric("(3*x)+(2*x)-(1*x+1*x)-(3*3*x)*x", "3*x*(−3*x + 1)", "Polynomial common factors")
  test_simplify_numeric("x*(x+1)", "x*(x+1)", "Retain common factors")
  test_simplify_numeric("x*(x+1)+x*(x+1)", "2*x*(x+1)", "Combine identical terms")
  test_simplify_numeric("6*x*y + 2*x*x*y", "2*x*y*(3+x)", "Common factors with multiple variables", ("x", "y"))
  test_simplify_numeric("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5*x*x+x-1", "Combine multiple like terms")
  test_end_category()
simplify_equality_tests()

def derivative_tests():
  # This doesn't test for proper simplification; only equivalence after simplifying.
  def test_derivative_numeric(expr, var, expected, message, filter_input=None):
    test_expression_numeric(parse_to_ast(expr).derivative(var), parse_to_ast(expected), message, [var], filter_input)

  test_category("Derivative tests")
  test_derivative_numeric("x*x", "x", "2*x", "Simple product rule")
  test_derivative_numeric("x*x*x", "x", "3*x*x", "Product displaying power rule")
  test_derivative_numeric("(5*x+3) / (2*x+1)", "x", "(−1)/((2*x+1)*(2*x+1))", "Quotient rule")
  test_derivative_numeric("sin(2*x)+1", "x", "2*cos(2*x)", "Chain rule and sin derivative")
  test_derivative_numeric("cos(sin(2*x))", "x", "−2*sin(sin(2*x))*cos(2*x)", "Nested chain rule and cos derivative")
  test_derivative_numeric(
    "cot(sec(x))", "x",
    "−1*tan(x)*sec(x)*csc(sec(x))*csc(sec(x))",
    "Cot and sec derivatives with / chain rule"
  )
  test_derivative_numeric(
    "csc(2*x + 1)*tan(3*x + 1)", "x",
    "csc(2*x + 1)*(3*sec(3*x + 1)*sec(3*x + 1) - 2*tan(3*x + 1)*cot(2*x + 1))",
    "Csc and tan derivatives / product, chain rule"
  )
  
  test_derivative_numeric("x^2", "x", "2*x", "Power rule")
  test_derivative_numeric("x^3", "x", "3*x^2", "Power rule")
  test_derivative_numeric("5*x^3 - 3*x^2 + 2*x - 4", "x", "15*x^2 - 6*x + 2", "Simple polynomial")
  test_derivative_numeric("(2*x+3) ^ (3*x+1)", "x", "(2*x+3)^(3*x)*(6*x+(6*x+9)*ln(2*x+3)+2)", "Logarithmic differentiation", filter_input=lambda x: x < 5 and x > 0)
  test_derivative_numeric("4^((1/2)*x)", "x", "2^x * ln(2)", "Exponential differentiation")
  test_derivative_numeric("((1/3)*x + 1)^(x^2/2)", "x", "((x/3)+1)^(x^2/2) * (x^2/(2*x+6) + x*ln(x/3+1))", "Full exponential differentiation")
  test_derivative_numeric("ln(5*x^2)", "x", "2/x", "Natural logarithm", filter_input=lambda x: x != 0)
  test_derivative_numeric("log_(x)(2*x)", "x", "(ln(x) - ln(2*x))/(x*ln(x)^2)", "Logarithm non-constant base and exponent", filter_input=lambda x: x > 1)
  test_derivative_numeric("log_(5+x)(x^3)", "x", "(3*ln(5+x)/x - ln(x^3)/(5+x)) / ln(5+x)^2", "Non-constant logarithm base", filter_input=lambda x: x > 1)
  
  test_end_category()
derivative_tests()

def readable_string_tests():
  test_category("Readable result string tests")
  # Will be slightly simpler when we support parsing floats
  test_result_str(ASTNumber(1.2), "1.2", "Float representation")
  test_result_str(ASTNumber(-1.0), "-1", "Integer representation")
  
  # We print Euler's number as "e" and pi as "π".
  test_result_str("E+E", "e+e", "Euler's number")
  test_result_str("pi*2*pi", "2ππ", "Pi")
  
  test_result_str("x*x", "x*x", "Multiplication compaction")
  test_result_str("(15)*(x+1)", "15(x+1)", "Parentheses for precedence")
  test_result_str("(2^3)*x", "2^3*x", "Multiplication operator insertion")
  test_result_str("(2*y)/(3*x*z)", "2y/(3x*z)", "Division precedence")
  test_result_str("(5)-(3+1)", "5-(3+1)", "Subtraction precedence")
  test_result_str("3*sin(2*x)", "3sin(2x)", "Function printing")
  test_result_str("sin(r)*3", "3sin(r)", "Multiplication constant in front convention")
  test_result_str("−1*x*x", "-x*x", "Negative sign placement")
  test_result_str(ASTLebiniz("v", "t", 1), "dv/dt", "Leibniz notation")
  test_result_str(ASTLebiniz("v", "t", 2), "d^2 v / dt^2", "Leibniz notation squared")
  test_result_str(
    ASTAdd(ASTNumber(Rational(5, 3)), ASTVariable("x")),
    "5/3+x", "Rational printing precedence no parens"
  )
  test_result_str(
    ASTMultiply(ASTNumber(Rational(5, 3)), ASTVariable("x")),
    "(5/3)x", "Rational printing precedence parens"
  )
  test_result_str("ln(5)", "ln(5)", "Natural logarithm notation")
  test_result_str("log(5)", "log(5)", "Default base-10 logarithm notation")
  test_result_str("log,,5(3)", "log_5(3)", "Alternative logarithm input notation")
  test_result_str("log_(5)(5)", "log_5(5)", "Logarithm notation")
  test_result_str("log_10(5)", "log(5)", "Logarithm base conversion")
  test_result_str("10*log_(x+1)(5+x)", "10log_[x+1](5+x)", "Logarithm notation")
  
  test_end_category()
readable_string_tests()

def exact_simplification_tests():
  test_category("Exact simplification tests")
  test_result_str("5*x*x + 10*x", "5(x+2)x", "Extract common factors", simplify=True, sort=True)
  test_result_str("3*x*y + 2*x*y", "5x*y", "Combine like terns", simplify=True, sort=True)
  test_result_str("3 - 4 + x*x - 2*x + 4*x*x + 3*x", "5x*x+x-1", "Simplify larger polynomial", simplify=True, sort=True)
  test_result_str("sin(6/(2*x))", "sin(3/x)", "Simplify function arguments", simplify=True, sort=True)
  test_result_str("3*x*x - 3*x - 9", "3(x*x-3-x)", "GCD doesn't break on edge cases", simplify=True)
  
  test_result_str("log_(2/3)(3/2)", "-1", "Logarithm notation and simplification", simplify=True)
  test_result_str("log_(2*x+3)(2*x+3)", "1", "Logarithm simplification", simplify=True)
  test_result_str("log_(x/4)(5)", "ln(5)/(ln(x)-ln(4))", "Logarithm base conversion", simplify=True)
  test_result_str("log(100)", "2", "Logarithm default base 10", simplify=True)
  test_result_str("ln(E*E)", "2", "Natural logarithm", simplify=True)
  test_result_str("log_(pi)(pi)", "1", "Logarithm irrational base", simplify=True)
  test_result_str("log_(2*x)(x)", "ln(x)/(ln(2)+ln(x))", "Logarithm simplification", simplify=True)
  
  # This is a probably-unnecessary number of tests for trig simplification.
  # Maybe we should add a "collapsed test group" feature to make them not take up so much space.
  # We don't test undefined values because we don't have a way to represent them yet.
  test_result_str("sin(0)", "0", "Trig simplification: sin(0)=0", simplify=True)
  
  test_collapsed_category("Trig simplification: sin, cos, tan, csc, sec, cot")
  
  test_result_str("sin(pi/2)", "1", "Trig simplification: sin(pi/2)=1", simplify=True)
  test_result_str("sin(pi)", "0", "Trig simplification: sin(pi)=0", simplify=True)
  test_result_str("sin(3*pi/2)", "-1", "Trig simplification: sin(3*pi/2)=-1", simplify=True)
  test_result_str("sin(55*pi/2)", "-1", "Trig simplification: sin(55*pi/2)=-1", simplify=True)
  test_result_str("sin(2/3*pi)", "sin((2/3)π)", "Trig simplification: sin(2/3*pi)=sin(2/3*pi)", simplify=True)
  test_result_str("sin(3*pi)", "0", "Trig simplification: sin(3*pi)=0", simplify=True)
  
  test_result_str("cos(0)", "1", "Trig simplification: cos(0)=1", simplify=True)
  test_result_str("cos(pi/2)", "0", "Trig simplification: cos(pi/2)=0", simplify=True)
  test_result_str("cos(pi)", "-1", "Trig simplification: cos(pi)=-1", simplify=True)
  test_result_str("cos(3*pi/2)", "0", "Trig simplification: cos(3*pi/2)=0", simplify=True)
  test_result_str("cos(55*pi/2)", "0", "Trig simplification: cos(55*pi/2)=0", simplify=True)
  test_result_str("cos(2/3*pi)", "cos((2/3)π)", "Trig simplification: cos(2/3*pi)=cos(2/3*pi)", simplify=True)
  test_result_str("cos(3*pi)", "-1", "Trig simplification: cos(3*pi)=-1", simplify=True)
  
  test_result_str("tan(0)", "0", "Trig simplification: tan(0)=0", simplify=True)
  test_result_str("tan(pi/4)", "1", "Trig simplification: tan(pi/4)=1", simplify=True)
  test_result_str("tan(pi)", "0", "Trig simplification: tan(pi)=0", simplify=True)
  test_result_str("tan(3*pi/4)", "-1", "Trig simplification: tan(3*pi/4)=-1", simplify=True)
  test_result_str("tan(55*pi/2)", "0", "Trig simplification: tan(55*pi/2)=0", simplify=True)
  test_result_str("tan(2/3*pi)", "tan((2/3)π)", "Trig simplification: tan(2/3*pi)=tan(2/3*pi)", simplify=True)
  test_result_str("tan(3*pi)", "0", "Trig simplification: tan(3*pi)=0", simplify=True)
  
  test_result_str("csc(pi/2)", "1", "Trig simplification: csc(pi/2)=1", simplify=True)
  test_result_str("csc(3*pi/2)", "-1", "Trig simplification: csc(3*pi/2)=-1", simplify=True)
  test_result_str("csc(55*pi/2)", "-1", "Trig simplification: csc(55*pi/2)=-1", simplify=True)
  test_result_str("csc(2/3*pi)", "csc((2/3)π)", "Trig simplification: csc(2/3*pi)=csc(2/3*pi)", simplify=True)
  
  test_result_str("sec(0)", "1", "Trig simplification: sec(0)=1", simplify=True)
  test_result_str("sec(pi)", "-1", "Trig simplification: sec(pi)=-1", simplify=True)
  test_result_str("sec(2/3*pi)", "sec((2/3)π)", "Trig simplification: sec(2/3*pi)=sec(2/3*pi)", simplify=True)
  test_result_str("sec(3*pi)", "-1", "Trig simplification: sec(3*pi)=-1", simplify=True)
  
  test_result_str("cot(pi/2)", "0", "Trig simplification: cot(pi/2)=0", simplify=True)
  test_result_str("cot(pi/4)", "1", "Trig simplification: cot(pi/4)=1", simplify=True)
  test_result_str("cot(3*pi/4)", "-1", "Trig simplification: cot(3*pi/4)=-1", simplify=True)
  
  test_end_collapsed_category()
  
  test_end_category()
exact_simplification_tests()

print("\nAll " + str(total_tests) + " tests passed!")