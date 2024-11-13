import cas_settings
from cas_rational import Rational

# Micropython's float implementation unfortunately
# doesn't fall back to the __float__ magic method.
# This is a workaround for that.
def to_float(obj):
  try:
    return float(obj)
  except:
    return obj.__float__()

class SimplifyState:
  def __init__(self, node=None, sort_terms=False):
    self.parent = node
    self.sort_terms = sort_terms
  def parent_is_expression(self):
    return self.parent != None and self.parent.is_expression()
  def parent_is_term(self):
    return self.parent != None and self.parent.is_term()
  def after(self, node):
    return SimplifyState(node, self.sort_terms)
  def reduce(self, node):
    return node.reduce(self)
  def expand(self, node):
    return node.expand(self)

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
    return ASTMultiply(ASTNumber(-1), self)

  # Don't override this; override reduce and expand instead
  def simplify(self, sort_terms=False):
    return self.expand(SimplifyState()).reduce(SimplifyState(sort_terms=sort_terms))
  def reduce(self, state):
    return self
  def expand(self, state):
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
    return isinstance(self, ASTConstant)
  def is_number(self):
    return isinstance(self, ASTNumber)
  def is_integer(self):
    return isinstance(self, ASTNumber) and int(self.number) == self.number
  def is_exactly(self, num):
    return isinstance(self, ASTNumber) and self.number == num
  def is_expression(self):
    return isinstance(self, (ASTAdd, ASTSubtract))
  def is_term(self):
    return isinstance(self, (ASTMultiply, ASTDivide))

class ASTConstant(ASTNode):
  def __init__(self):
    if type(self) == ASTConstant:
      raise Exception("Cannot create an instance of ASTConstant. Use a subclass instead.")
    self.number = None
  
  def derivative(self, var):
    return ASTNumber(0)
  
  def eval(self):
    return to_float(self.number)

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
    return ASTMultiply(
      ASTLebiniz(self.main, var, 1),
      self
    ).simplify()

class ASTAdd(ASTNode):
  precidence = 4
  def __init__(self, left, right):
    self.left = left
    self.right = right
  
  def pretty_str(self, precidence):
    string = self.left.pretty_str(ASTAdd.precidence) + "+" + self.right.pretty_str(ASTAdd.precidence)
    if precidence < ASTAdd.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + str(self.left) + "+" + str(self.right) + ")"

  def reduce(self, original_state):
    state = original_state.after(self)

    left = self.left.reduce(state)
    right = self.right.reduce(state)
    if left.is_exactly(0):
      return right
    if right.is_exactly(0):
      return left
    if left.is_number() and right.is_number():
      return ASTNumber(left.number + right.number)
    simplified_self = ASTAdd(left, right)
    if original_state.parent_is_expression():
      return simplified_self
    
    from cas_simplify_expr import ExpressionReducer
    return ExpressionReducer(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTAdd(self.left.expand(state), self.right.expand(state))
  
  def traverse(self, func):
    self.left.traverse(func)
    self.right.traverse(func)
    func(self)

  def substitute(self, var, value):
    return ASTAdd(
      self.left.substitute(var, value),
      self.right.substitute(var, value)
    )
  def eval(self):
    return self.left.eval() + self.right.eval()
  def derivative(self, var):
    return ASTAdd(
     self.left.derivative(var),
     self.right.derivative(var)
    ).simplify()

class ASTSubtract(ASTNode):
  precidence = 4
  def __init__(self, left, right):
    self.left = left
    self.right = right
  
  def pretty_str(self, precidence):
    string = self.left.pretty_str(ASTSubtract.precidence) + "-" + self.right.pretty_str(ASTSubtract.precidence-1)
    if precidence < ASTSubtract.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + str(self.left) + "-" + str(self.right) + ")"
  
  def negate(self):
    return ASTSubtract(self.right, self.left)
  
  def reduce(self, original_state):
    state = original_state.after(self)

    left = self.left.reduce(state)
    right = self.right.reduce(state)
    if left.is_number() and right.is_number():
      return ASTNumber(left.number - right.number)
    if left.is_exactly(0):
      return ASTMultiply(ASTNumber(-1), right)
    if right.is_exactly(0):
      return left
    if left.is_number() and left.number < 1:
      return ASTSubtract(
        right.negate(),
        left.negate()
      )
    simplified_self = ASTSubtract(left, right)
  
    if original_state.parent_is_expression():
      return simplified_self
    
    from cas_simplify_expr import ExpressionReducer
    return ExpressionReducer(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTSubtract(self.left.expand(state), self.right.expand(state))
  
  def traverse(self, func):
    self.left.traverse(func)
    self.right.traverse(func)
    func(self)

  def substitute(self, var, value):
    return ASTSubtract(
      self.left.substitute(var, value),
      self.right.substitute(var, value)
    )
  def eval(self):
    return self.left.eval() - self.right.eval()
  def derivative(self, var):
    return ASTSubtract(
     self.left.derivative(var),
     self.right.derivative(var)
    ).simplify()

class ASTMultiply(ASTNode):
  precidence = 3
  def __init__(self, left, right):
    self.left = left
    self.right = right
  
  def pretty_str(self, precidence):
    left = self.left
    right = self.right
    if right.is_number() and not left.is_number():
      (left, right) = (right, left)
    if left.is_exactly(-1):
      return "-" + right.pretty_str(ASTMultiply.precidence)

    add_multiply = right.is_number() or (
        (isinstance(right, ASTMultiply) and right.left.is_number()) or \
        (isinstance(right, ASTDivide) and right.numerator.is_number())
      )
    string = left.pretty_str(ASTMultiply.precidence) + \
      ("*" if add_multiply else "") + \
      right.pretty_str(ASTMultiply.precidence)
    if precidence < ASTMultiply.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + str(self.left) + "*" + str(self.right) + ")"
  
  def negate(self):
    if self.left.is_number():
      return ASTMultiply(self.left.negate(), self.right)
    return ASTMultiply(ASTNumber(-1), self)
  
  def reduce(self, original_state):
    state = original_state.after(self)

    left = self.left.reduce(state)
    right = self.right.reduce(state)
    if left.is_exactly(0) or right.is_exactly(0):
      return ASTNumber(0)
    if right.is_exactly(1):
      return left
    if left.is_exactly(1):
      return right
    if left.is_number() and right.is_number():
      return ASTNumber(left.number * right.number)
    simplified_self = ASTMultiply(left, right)

    if original_state.parent_is_term():
      return simplified_self
  
    from cas_simplify_expr import ExpressionTerm
    return ExpressionTerm(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTMultiply(self.left.expand(state), self.right.expand(state))
  
  def traverse(self, func):
    self.left.traverse(func)
    self.right.traverse(func)
    func(self)
  
  def substitute(self, var, value):
    return ASTMultiply(
      self.left.substitute(var, value),
      self.right.substitute(var, value)
    )
  def eval(self):
    return self.left.eval() * self.right.eval()
  def derivative(self, var):
    return ASTAdd(
      ASTMultiply(self.left, self.right.derivative(var)),
      ASTMultiply(self.right, self.left.derivative(var))
    ).simplify()

class ASTDivide(ASTNode):
  precidence = 3
  def __init__(self, numerator, denominator):
    self.numerator = numerator
    self.denominator = denominator
  
  def pretty_str(self, precidence):
    string = self.numerator.pretty_str(ASTDivide.precidence) + "/" + self.denominator.pretty_str(ASTDivide.precidence - 1)
    if precidence < ASTDivide.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + str(self.numerator) + "/" + str(self.denominator) + ")"
  
  def negate(self):
    if self.numerator.is_number():
      return ASTDivide(self.numerator.negate(), self.denominator)
    return ASTMultiply(ASTNumber(-1), self)
  
  def reduce(self, original_state):
    state = original_state.after(self)
    
    numerator = self.numerator.reduce(state)
    denominator = self.denominator.reduce(state)
    if numerator.is_exactly(0):
      return ASTNumber(0)
    if denominator.is_exactly(1):
      return numerator
    if numerator.is_number() and denominator.is_number():
      return ASTNumber(numerator.number / denominator.number)
    simplified_self = ASTDivide(numerator, denominator)

    if original_state.parent_is_term():
      return simplified_self
  
    from cas_simplify_expr import ExpressionTerm
    return ExpressionTerm(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTDivide(self.numerator.expand(state), self.denominator.expand(state))
  
  def traverse(self, func):
    self.numerator.traverse(func)
    self.denominator.traverse(func)
    func(self)
  
  def substitute(self, var, value):
    return ASTDivide(
      self.numerator.substitute(var, value),
      self.denominator.substitute(var, value)
    )
  def eval(self):
    return self.numerator.eval() / self.denominator.eval()
  
  def derivative(self, var):
    return ASTDivide(
      # ba' - ab'
      ASTSubtract(
        ASTMultiply(self.denominator, self.numerator.derivative(var)),
        ASTMultiply(self.numerator, self.denominator.derivative(var))
      ),
      # ... / b**2
      ASTMultiply(self.denominator, self.denominator)
    ).simplify()

# TODO: Extensive tests
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

  def expand(self, state):
    # TODO
    return ASTPower(self.base.expand(state), self.exponent.expand(state))
  
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
    return self.base.eval() ** self.exponent.eval()
  
  def derivative(self, var):
    # (f(x)^g(x))' = f(x)^g(x) * (f'(x)/f(x) * g(x) + g'(x) * ln(f(x)))
    return ASTMultiply(
      self,
      ASTAdd(
        ASTMultiply(
          ASTDivide(self.base.derivative(var), self.base),
          self.exponent
        ),
        ASTMultiply(
          self.exponent.derivative(var),
          ASTLogarithm(ASTEuler(), self.base)
        )
      )
    ).simplify()

# TODO: Extensive tests
class ASTLogarithm(ASTNode):
  precidence = 100
  def __init__(self, base, argument):
    self.base = base
    self.argument = argument
  
  def pretty_str(self, precidence):
    if self.base == ASTEuler():
      string = "ln"
    else:
      string = "log_" + self.base.pretty_str(ASTLogarithm.precidence)
    string += "(" + self.argument.pretty_str(ASTLogarithm.precidence) + ")"
    if precidence < ASTLogarithm.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "log" + str(self.base) + "(" + str(self.argument) + ")"
  
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
      import cas_settings
      import math

      if cas_settings.USE_RATIONALS:
        from cas_rational import exact_rational_log
        result = exact_rational_log(argument.number, base.number)
        # When rational numbers are enabled and the result is not a rational number
        if result == None:
          return self
        return ASTNumber(result)
      
      return ASTNumber(math.log(argument.number, base.number))
    
    simplified_self = ASTLogarithm(base, argument)
    return simplified_self

  def expand(self, state):
    # TODO
    return ASTLogarithm(self.base.expand(state), self.argument.expand(state))
  
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
    return math.log(self.argument.eval(), self.base.eval())
  
  def derivative(self, var):
    # (log_b(f(x)))' = f'(x) / (f(x) * ln(b))
    return ASTDivide(
      self.argument.derivative(var),
      ASTMultiply(
        self.argument,
        ASTLogarithm(ASTEuler(), self.base)
      )
    ).simplify()