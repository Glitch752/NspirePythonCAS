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
  def __init__(self, node=None, sort_terms=False, expand_logarithms=False):
    self.parent = node
    self.sort_terms = sort_terms
    self.expand_logarithms = expand_logarithms
  def parent_is_expression(self):
    return self.parent != None and self.parent.is_expression()
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
    return ASTMultiply(ASTNumber(-1), self)

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
    if isinstance(self, ASTMultiply) and self.left.is_number() and isinstance(self.right, ASTPi):
      offset_coefficient = (self.left.number - offset) / 2
      return offset_coefficient == int(offset_coefficient)
    return False
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
  def distribute(self, state):
    # TODO
    return ASTAdd(self.left.distribute(state), self.right.distribute(state))
  
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
  
  def is_constant(self):
    return self.left.is_constant() and self.right.is_constant()

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
  def distribute(self, state):
    # TODO
    return ASTSubtract(self.left.distribute(state), self.right.distribute(state))
  
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
  
  def is_constant(self):
    return self.left.is_constant() and self.right.is_constant()

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

    left_string = left.pretty_str(ASTMultiply.precidence)
    # This is super hacky, but it works for now lol
    add_multiply = not left_string[-1] == ")" and (
        not left.is_number() and
        not left.is_term() and
        not (isinstance(left, ASTPi) or isinstance(left, ASTEuler))
      ) or (
        (isinstance(right, ASTMultiply) and right.left.is_number()) or \
        (isinstance(right, ASTDivide) and right.numerator.is_number())
      ) or "a" <= left_string[-1] <= "z"
    string = left_string + \
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
  def distribute(self, state):
    # TODO
    return ASTMultiply(self.left.distribute(state), self.right.distribute(state))
  
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
  
  def is_constant(self):
    return self.left.is_constant() and self.right.is_constant()

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
  def distribute(self, state):
    # TODO
    return ASTDivide(self.numerator.distribute(state), self.denominator.distribute(state))
  
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
  
  def is_constant(self):
    return self.numerator.is_constant() and self.denominator.is_constant()

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
      return ASTMultiply(
        ASTMultiply(
          self.exponent,
          ASTPower(self.base, ASTSubtract(self.exponent, ASTNumber(1))),
        ),
        self.base.derivative(var)
      ).simplify()
    
    # Constant to the power of a function
    # C^g(x) = C^g(x) * ln(C) * g'(x)
    if self.base.is_constant():
      return ASTMultiply(
        ASTPower(self.base, self.exponent),
        ASTMultiply(
          ASTLn(self.base),
          self.exponent.derivative(var)
        )
      ).simplify()
    
    # The general case:
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
      import cas_settings
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
        return ASTDivide(
          ASTLn(argument),
          ASTLn(base)
        ).reduce(state)
      
      # log_b(a^c) = c * log_b(a)
      if isinstance(argument, ASTPower):
        return ASTMultiply(
          argument.exponent,
          ASTLogarithm(base, argument.base)
        ).reduce(state)
      
      # log_b(a * c) = log_b(a) + log_b(c)
      if isinstance(argument, ASTMultiply):
        # TODO: We should do this in a better way; this is hopefully temporary...
        if argument.left.is_number() and isinstance(argument.left.number, Rational) and argument.left.number.denominator != 1:
          numerator = ASTMultiply(ASTNumber(argument.left.number.numerator), argument.right)
          denominator = ASTNumber(argument.left.number.denominator)
          return ASTSubtract(
            ASTLogarithm(base, numerator),
            ASTLogarithm(base, denominator)
          ).reduce(state)
        
        return ASTAdd(
          ASTLogarithm(base, argument.left),
          ASTLogarithm(base, argument.right)
        ).reduce(state)
      
      # log_b(a / c) = log_b(a) - log_b(c)
      if isinstance(argument, ASTDivide):
        return ASTSubtract(
          ASTLogarithm(base, argument.numerator),
          ASTLogarithm(base, argument.denominator)
        ).reduce(state)
    
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
      return ASTDivide(
        self.argument.derivative(var),
        ASTMultiply(
          self.argument,
          ASTLn(self.base)
        )
      ).simplify()
    
    # If the argument is a constant:
    # (log_[b(x)](C))' = (-ln(c) * b'(x)) / (b(x) * ln(b(x))^2)
    if self.argument.is_constant():
      return ASTDivide(
        ASTMultiply(
          ASTLn(self.argument),
          self.base.derivative(var)
        ).negate(),
        ASTMultiply(
          self.base,
          ASTPower(ASTLn(self.base), ASTNumber(2))
        )
      ).simplify()
    
    # The general case:
    # (log_[b(x)](f(x)))' = (ln(b(x)) * f'(x)/f(x) - ln(f(x)) * b'(x)/b(x)) / ln(b(x))^2
    return ASTDivide(
      ASTSubtract(
        ASTMultiply(
          ASTLn(self.base),
          ASTDivide(self.argument.derivative(var), self.argument)
        ),
        ASTMultiply(
          ASTLn(self.argument),
          ASTDivide(self.base.derivative(var), self.base)
        )
      ),
      ASTPower(ASTLn(self.base), ASTNumber(2))
    ).simplify()
  
  def is_constant(self):
    return self.base.is_constant() and self.argument.is_constant()

# Simple helper to avoid repetitive natural logarithm creation
def ASTLn(argument):
  return ASTLogarithm(ASTEuler(), argument)