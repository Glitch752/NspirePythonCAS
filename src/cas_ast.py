import cas_settings
from cas_rational import Rational

def is_number(c):
  return "0" <= c <= "9"
def is_letter(c):
  return "a" <= c <= "z" or "A" <= c <= "Z"

# Micropython's float implementation unfortunately
# doesn't fall back to the __float__ magic method.
# This is a workaround for that.
def to_float(obj):
  try:
    return float(obj)
  except:
    return obj.__float__()

class SimplifyState:
  def __init__(self, node=None, sort_terms=False, expand_logarithms=False):
    self.parent = node
    self.sort_terms = sort_terms
    self.expand_logarithms = expand_logarithms
  def parent_is_term(self):
    return self.parent != None and self.parent.is_term()
  def after(self, node):
    return SimplifyState(node, self.sort_terms, self.expand_logarithms)
  def reduce(self, node):
    return node.reduce(self)
  def distribute(self, node):
    return node.distribute(self)

class ASTNode:
  precidence = 0
  def __init__(self):
    raise Exception("Implement me!")
  
  def __eq__(self, other):
    if type(self) != type(other):
      return False
    for attr in self.__dict__:
      if getattr(self, attr) != getattr(other, attr):
        return False
    return True
  def __ne__(self, other):
    return not self.__eq__(other)
  def __hash__(self):
    return hash(str(self))

  def pretty_str(self, precidence):
    raise Exception("Implement me!")
  def __str__(self):
    raise Exception("Implement me!")
  def __repr__(self):
    return self.__str__()
  
  def negate(self):
    return ASTProduct(ASTNumber(-1), self)

  # Don't override this; override reduce and expand instead
  def simplify(self, sort_terms=False, expand_logarithms=True):
    state = SimplifyState(sort_terms=sort_terms, expand_logarithms=expand_logarithms)
    return self.distribute(state).reduce(state)
  def reduce(self, state):
    return self
  def distribute(self, state):
    # TODO: Implement in subclasses
    return self
  
  def traverse(self, func):
    # Subclasses should call traverse on all children
    func(self)
  def get_variables(self):
    variables = set()
    self.traverse(lambda node: variables.add(node.name) if isinstance(node, ASTVariable) else None)
    return variables
  
  def substitute(self, var, value):
    return self
  def substitute_with_numbers(self, values):
    node = self
    for var, value in values.items():
      node = node.substitute(var, ASTNumber(value))
    return node

  def eval(self):
    raise Exception("Implement me!")
  
  def derivative(self, var):
    raise Exception("Implement me!")

  # Helper functions
  def is_constant(self):
    return False
  # TODO: There's definitely a more general way to implement this, but this works for now.
  def is_2pi_multiple(self, quarter_pi_offset):
    # Assumes the left of multiplication with pi is the number, which is currently always the case after simplification.
    if (self.is_exactly(0) and quarter_pi_offset == 0) or (isinstance(self, ASTPi) and quarter_pi_offset == 4):
      return True
    offset = Rational(quarter_pi_offset, 4) if cas_settings.USE_RATIONALS else quarter_pi_offset / 4
    # This is even more hacky than it was before with the assumption of only 2 factors long...
    # TODO: Fix this because it breaks under so many possible circumstances
    if isinstance(self, ASTProduct) and self.factors[0].is_number() and isinstance(self.factors[1], ASTPi):
      offset_coefficient = (self.factors[0].number - offset) / 2
      return offset_coefficient == int(offset_coefficient)
    return False
  def is_number(self):
    return isinstance(self, ASTNumber)
  def is_integer(self):
    return isinstance(self, ASTNumber) and int(self.number) == self.number
  def is_exactly(self, num):
    return isinstance(self, ASTNumber) and self.number == num

class ASTConstant(ASTNode):
  def __init__(self):
    if type(self) == ASTConstant:
      raise Exception("Cannot create an instance of ASTConstant. Use a subclass instead.")
    self.number = None
  
  def derivative(self, var):
    return ASTNumber(0)
  
  def eval(self):
    return to_float(self.number)

  def is_constant(self):
    return True

# TODO: Tests
class ASTPi(ASTConstant):
  def __init__(self):
    from math import pi
    self.number = pi
  def pretty_str(self, precidence):
    return "π"
  def __str__(self):
    return "π"

# TODO: Tests
class ASTEuler(ASTConstant):
  def __init__(self):
    from math import e
    self.number = e
  def pretty_str(self, precidence):
    return "e"
  def __str__(self):
    return "e"

builtin_variables = {
  "E": ASTEuler(),
  "pi": ASTPi(),
  "π": ASTPi()
}

class ASTNumber(ASTConstant):
  def __init__(self, number):
    if cas_settings.USE_RATIONALS and isinstance(number, int):
      self.number = Rational(number)
    else:
      self.number = number
  
  def pretty_str(self, precidence):
    if isinstance(self.number, Rational):
      return "(" + str(self.number) + ")"\
        if (precidence <= 3 and self.number.denominator != 1)\
        else str(self.number)
    return str(int(self.number)) if int(self.number) == self.number else str(self.number)
  def __str__(self):
    return str(self.number)
  
  def negate(self):
    return ASTNumber(self.number * -1)

class ASTVariable(ASTNode):
  def __init__(self, name):
    self.name = name
  
  def pretty_str(self, precidence):
    return self.name
  def __str__(self):
    return "(" + self.name + ")"
  
  def substitute(self, var, value):
    if self.name == var:
      return value
    return self
  def eval(self):
    raise Exception("Cannot evaluate variable")
  def derivative(self, var):
    if self.name == var:
      return ASTNumber(1)
    return ASTLebiniz(self.name, var, 1)

class ASTLebiniz(ASTNode):
  precidence = 6
  def __init__(self, main, relative_to, degree):
    self.main = main
    self.relative_to = relative_to
    self.degree = degree
  
  def pretty_str(self, precidence):
    string = "d"
    if self.degree != 1:
      string += "^" + str(self.degree) + " "
    string += self.main
    string += "/" if self.degree == 1 else " / "
    string += "d" + self.relative_to
    if self.degree != 1:
      string += "^" + str(self.degree)
    if precidence < ASTLebiniz.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    if self.degree != 1:
      return "(d^" + self.degree + " " + self.main + " / d" + self.relative_to + "^" + self.degree + ")"
    return "(d" + self.main + "/d" + self.relative_to + ")"
  
  def substitute(self, var, value):
    return self
  def eval(self):
    raise Exception("Cannot evaluate rate of change")
  def derivative(self, var):
    if self.main == var:
      return ASTLebiniz(self.main, self.relative_to, self.degree+1)
    return ASTProduct(
      ASTLebiniz(self.main, var, 1),
      self
    ).simplify()

# Invariant: no term in a sum is a sum
class ASTSum(ASTNode):
  precidence = 4
  # Can be constructed like ASTSum(term1, term2, ...) or ASTSum([term1, term2, ...])
  def __init__(self, *terms):
    if len(terms) == 1 and isinstance(terms[0], list):
      self.terms = terms[0]
    else:
      self.terms = list(terms)
    
    # Flatten sums; this enforces our no sum children invariant
    i = 0
    while i < len(self.terms):
      if isinstance(self.terms[i], ASTSum):
        self.terms = self.terms[:i] + self.terms[i].terms + self.terms[i+1:]
      else:
        i += 1
  
  @staticmethod
  def subtract(left, right):
    return ASTSum(left, right.negate())
  
  def pretty_str(self, precidence):
    string = ""
    for i, term in enumerate(self.terms):
      # This is a bit hacky, but it works for now
      term_str = term.pretty_str(ASTSum.precidence)
      if term_str[0] == "-":
        string = string[:-1]
      string += term_str
      if i < len(self.terms) - 1:
        string += "+"
    
    if precidence < ASTSum.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + "+".join(map(str, self.terms)) + ")"

  def reduce(self, original_state):
    state = original_state.after(self)
    
    # TODO: Combine with ExpressionReducer and refactor; this is a hack to get tests working for now
    new_terms = [term.reduce(state) for term in self.terms]
    
    # Merge constants
    constant = 0
    i = 0
    while i < len(new_terms):
      if new_terms[i].is_number():
        constant += new_terms[i].number
        new_terms.pop(i)
      else:
        i += 1
    if constant != 0:
      new_terms.append(ASTNumber(constant))
    
    from cas_simplify_expr import ExpressionReducer
    reduced = ExpressionReducer(new_terms, state).reduce().to_ast()
    
    if not isinstance(reduced, ASTSum):
      return reduced.reduce(state)
    if len(reduced.terms) == 0:
      return ASTNumber(0)
    if len(reduced.terms) == 1:
      return reduced.terms[0]
    
    return reduced
  def distribute(self, state):
    # TODO
    return ASTSum([term.distribute(state) for term in self.terms])
  
  def traverse(self, func):
    for term in self.terms:
      term.traverse(func)
    func(self)

  def substitute(self, var, value):
    return ASTSum([term.substitute(var, value) for term in self.terms])
  def eval(self):
    return sum(term.eval() for term in self.terms)
  def derivative(self, var):
    return ASTSum([term.derivative(var) for term in self.terms]).simplify()
  
  def is_constant(self):
    return all(term.is_constant() for term in self.terms)

# Invariant: no factor in a product is a product
class ASTProduct(ASTNode):
  precidence = 3
  def __init__(self, *factors):
    if len(factors) == 1 and isinstance(factors[0], list):
      self.factors = factors[0]
    else:
      self.factors = list(factors)
    
    # Flatten products; this enforces our no product children invariant
    i = 0
    while i < len(self.factors):
      if isinstance(self.factors[i], ASTProduct):
        self.factors = self.factors[:i] + self.factors[i].factors + self.factors[i+1:]
      else:
        i += 1
  
  @staticmethod
  def divide(numerator, denominator):
    return ASTProduct(numerator, ASTPower(denominator, ASTNumber(-1)))
  
  def pretty_str(self, precidence):
    string = ""
    number_factors = []
    numerator_factors = []
    denominator_factors = []
    for factor in self.factors:
      if factor.is_number():
        number_factors.append(factor)
      elif isinstance(factor, ASTPower) and factor.exponent.is_exactly(-1):
        denominator_factors.append(factor.base)
      else:
        numerator_factors.append(factor)
    
    # This _should_ be reduced most of the time,
    # but we still handle cases where there are multiple numberical constant factors
    for i, factor in enumerate(number_factors):
      if i == 0 and factor.is_exactly(-1):
        string += "-"
      else:
        string += factor.pretty_str(ASTProduct.precidence)
        if i < len(number_factors) - 1 or len(numerator_factors) > 0 and string[-1] != ")":
          string += "*"
    
    for i, factor in enumerate(numerator_factors):
      formatted_string = factor.pretty_str(ASTProduct.precidence)
      if len(string) > 1 and len(formatted_string) > 0 and string[-1] == "*"\
        and (not is_letter(formatted_string[0]) or is_number(string[-2])):
        string = string[:-1]
      string += formatted_string
      if i < len(numerator_factors) - 1\
        and string[-1] != ")":
        string += "*"
    if len(denominator_factors) > 0:
      string += "/"
      use_parentheses = len(denominator_factors) > 1 or isinstance(denominator_factors[0], ASTProduct)
      if use_parentheses:
        string += "("
      for i, factor in enumerate(denominator_factors):
        string += factor.pretty_str(ASTProduct.precidence)
        if i < len(denominator_factors) - 1:
          string += "*"
      if use_parentheses:
        string += ")"
    
    if precidence < ASTProduct.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + "*".join(map(str, self.factors)) + ")"
  
  def reduce(self, original_state):
    state = original_state.after(self)

    new_factors = [factor.reduce(state) for factor in self.factors]
    
    from cas_simplify_expr import ExpressionTerm
    reduced = ExpressionTerm(new_factors, state).reduce().to_ast()
    
    if not isinstance(reduced, ASTProduct):
      return reduced.reduce(state)
    if len(reduced.factors) == 0:
      return ASTNumber(1)
    if len(reduced.factors) == 1:
      return reduced.factors[0]
    
    return reduced
  
  def distribute(self, state):
    return ASTProduct([factor.distribute(state) for factor in self.factors])
  
  def traverse(self, func):
    for factor in self.factors:
      factor.traverse(func)
    func(self)
  
  def substitute(self, var, value):
    return ASTProduct([factor.substitute(var, value) for factor in self.factors])
  def eval(self):
    product = 1
    for factor in self.factors:
      product *= factor.eval()
    return product
  def derivative(self, var):
    # First, move the constant factors out of the derivative
    # Then, apply the product rule recursively
    constantTerms = []
    nonConstantFactors = []
    for factor in self.factors:
      if factor.is_constant():
        constantTerms.append(factor)
      else:
        nonConstantFactors.append(factor)
        
    # If there are no non-constant factors, derivative is zero
    if len(nonConstantFactors) == 0:
      return ASTNumber(0)

    # The generalized form of the product rule
    # is the sum of derivatives of each factor times the product of the others
    # e.g. (fgh)' = f'gh + fg'h + fgh'
    sumTerms = []
    for i, factor in enumerate(nonConstantFactors):
      otherFactors = nonConstantFactors[:i] + nonConstantFactors[i+1:]
      sumTerms.append(ASTProduct([factor.derivative(var)] + otherFactors))
    
    if len(constantTerms) > 0:
      return ASTProduct(constantTerms + [ASTSum(sumTerms)]).simplify()
    return ASTSum(sumTerms).simplify()
  
  def is_constant(self):
    return all(factor.is_constant() for factor in self.factors)

class ASTPower(ASTNode):
  precidence = 2
  def __init__(self, base, exponent):
    self.base = base
    self.exponent = exponent
  
  def pretty_str(self, precidence):
    string = self.base.pretty_str(ASTPower.precidence) + "^" + self.exponent.pretty_str(ASTPower.precidence)
    if precidence < ASTPower.precidence:
      string = "(" + string + ")"
    return string

  def __str__(self):
    return "(" + str(self.base) + "^" + str(self.exponent) + ")"
  
  def reduce(self, original_state):
    state = original_state.after(self)
    
    base = self.base.reduce(state)
    exponent = self.exponent.reduce(state)
    # This results in the ambiguous 0^0 case being 0.
    # Maybe this should be a setting or warning?
    if base.is_exactly(0):
      return ASTNumber(0)
    
    if exponent.is_exactly(0):
      return ASTNumber(1)
    if exponent.is_exactly(1):
      return base
    
    if base.is_exactly(1):
      return ASTNumber(1)
    
    if base.is_number() and exponent.is_number():
      result = base.number ** exponent.number
      # When rational numbers are enabled and the result is not a rational number
      if result == None:
        return self
      return ASTNumber(result)
    
    simplified_self = ASTPower(base, exponent)
    return simplified_self

  def distribute(self, state):
    # TODO
    return ASTPower(self.base.distribute(state), self.exponent.distribute(state))
  
  def traverse(self, func):
    self.base.traverse(func)
    self.exponent.traverse(func)
    func(self)
  
  def substitute(self, var, value):
    return ASTPower(
      self.base.substitute(var, value),
      self.exponent.substitute(var, value)
    )

  def eval(self):
    if self.base.is_exactly(0) and self.exponent.is_exactly(0):
      # This is an ambiguous case; 0^0 is undefined. We should probably make this a setting and warning.
      return 0
    # This _can_ return complex numbers, but it's fine in evaluation for now.
    return self.base.eval() ** self.exponent.eval()
  
  def derivative(self, var):
    # There are a few simpler cases that we can take shortcuts
    # in to avoid unnecessary calculations. These aren't technically
    # necessary, but they speed up processing.

    # Function to the power of a constant
    # f(x)^C = C * f(x)^(C-1) * f'(x)
    if self.exponent.is_constant():
      return ASTProduct(
        self.exponent,
        ASTPower(self.base, ASTSum.subtract(self.exponent, ASTNumber(1))),
        self.base.derivative(var)
      ).simplify()
    
    # Constant to the power of a function
    # C^g(x) = C^g(x) * ln(C) * g'(x)
    if self.base.is_constant():
      return ASTProduct(
        ASTPower(self.base, self.exponent),
        ASTLn(self.base),
        self.exponent.derivative(var)
      ).simplify()
    
    # The general case:
    # (f(x)^g(x))' = f(x)^g(x) * (f'(x)/f(x) * g(x) + g'(x) * ln(f(x)))
    return ASTProduct(
      self,
      ASTSum(
        ASTProduct(
          ASTProduct.divide(self.base.derivative(var), self.base),
          self.exponent
        ),
        ASTProduct(
          self.exponent.derivative(var),
          ASTLn(self.base)
        )
      )
    ).simplify()
  
  def is_constant(self):
    return self.base.is_constant() and self.exponent.is_constant()

class ASTLogarithm(ASTNode):
  precidence = 0
  def __init__(self, base, argument):
    self.base = base
    self.argument = argument
  
  def pretty_str(self, precidence):
    if isinstance(self.base, ASTEuler):
      string = "ln"
    elif self.base.is_exactly(10):
      string = "log"
    else:
      string = "log_"
      if self.base.is_number():
        string += self.base.pretty_str(ASTLogarithm.precidence)
      else:
        # Maybe this should be a setting to adjust what parentheses are used?
        # I don't think it's a huge deal.
        string += "[" + self.base.pretty_str(100) + "]"
    
    string += "(" + self.argument.pretty_str(100) + ")"
    if precidence < ASTLogarithm.precidence:
      string = "(" + string + ")"
    return string
  
  def __str__(self):
    return "log_[ " + str(self.base) + " ](" + str(self.argument) + ")"
  
  def reduce(self, original_state):
    state = original_state.after(self)
    
    base = self.base.reduce(state)
    argument = self.argument.reduce(state)
    
    if base.is_exactly(1):
      # This is a special case because log_1(x) is undefined.
      # Returning 0 isn't correct, but it's better than nothing.
      # Maybe this should be a warning until we properly represent function domains?
      return ASTNumber(0)
    if argument.is_exactly(1):
      return ASTNumber(0)
    
    if base.is_number() and argument.is_number():
      import math

      if cas_settings.USE_RATIONALS:
        from cas_rational import exact_rational_log
        result = exact_rational_log(argument.number, base.number)
        # When rational numbers are enabled and the result is not a rational number
        if result == None:
          return ASTLogarithm(base, argument)
        return ASTNumber(result)
      
      return ASTNumber(math.log(argument.number, base.number))
    
    # log_b(b) = 1 if b != 1
    if base == argument and not base.is_exactly(1):
      # Handles ln(e) = 1
      return ASTNumber(1)
    
    if state.expand_logarithms:
      # log_b(a) = ln(a) / ln(b)
      if not base.is_constant():
        return ASTProduct.divide(
          ASTLn(argument),
          ASTLn(base)
        ).reduce(state)
      
      # log_b(rational a/c) = log_b(a) - log_b(c)
      if cas_settings.USE_RATIONALS and isinstance(argument, ASTNumber) and argument.number.denominator != 1:
        return ASTSum.subtract(
          ASTLogarithm(base, ASTNumber(argument.number.numerator)),
          ASTLogarithm(base, ASTNumber(argument.number.denominator))
        )
      
      # log_b(a^c) = c * log_b(a)
      if isinstance(argument, ASTPower):
        return ASTProduct(
          argument.exponent,
          ASTLogarithm(base, argument.base)
        ).reduce(state)
      
      # log_b(a * c + ...) = log_b(a) + log_b(c) + ...
      if isinstance(argument, ASTProduct):
        return ASTSum([ASTLogarithm(base, factor) for factor in argument.factors]).reduce(state)
    
    return ASTLogarithm(base, argument)

  def distribute(self, original_state):
    # TODO
    return ASTLogarithm(self.base.distribute(original_state), self.argument.distribute(original_state))
  
  def traverse(self, func):
    self.base.traverse(func)
    self.argument.traverse(func)
    func(self)
  
  def substitute(self, var, value):
    return ASTLogarithm(
      self.base.substitute(var, value),
      self.argument.substitute(var, value)
    )

  def eval(self):
    from math import log
    return log(self.argument.eval(), self.base.eval())
  
  def derivative(self, var):
    # There are a few simpler cases that we can take shortcuts
    # in to avoid unnecessary calculations. These aren't technically
    # necessary, but they speed up processing.

    # If the base is a constant:
    # (log_b(f(x)))' = f'(x) / (f(x) * ln(b))
    if self.base.is_constant():
      return ASTProduct.divide(
        self.argument.derivative(var),
        ASTProduct(
          self.argument,
          ASTLn(self.base)
        )
      ).simplify()
    
    # If the argument is a constant:
    # (log_[b(x)](C))' = (-ln(c) * b'(x)) / (b(x) * ln(b(x))^2)
    if self.argument.is_constant():
      return ASTProduct.divide(
        ASTProduct(
          ASTLn(self.argument),
          self.base.derivative(var)
        ).negate(),
        ASTProduct(
          self.base,
          ASTPower(ASTLn(self.base), ASTNumber(2))
        )
      ).simplify()
    
    # The general case:
    # (log_[b(x)](f(x)))' = (ln(b(x)) * f'(x)/f(x) - ln(f(x)) * b'(x)/b(x)) / ln(b(x))^2
    return ASTProduct.divide(
      ASTSum.subtract(
        ASTProduct(
          ASTLn(self.base),
          ASTProduct.divide(self.argument.derivative(var), self.argument)
        ),
        ASTProduct(
          ASTLn(self.argument),
          ASTProduct.divide(self.base.derivative(var), self.base)
        )
      ),
      ASTPower(ASTLn(self.base), ASTNumber(2))
    ).simplify()
  
  def is_constant(self):
    return self.base.is_constant() and self.argument.is_constant()

# Simple helper to avoid repetitive natural logarithm creation
def ASTLn(argument):
  return ASTLogarithm(ASTEuler(), argument)