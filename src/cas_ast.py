import cas_settings
from cas_rational import Rational
from math import sin, cos

def is_ast_constant(node):
  return isinstance(node, ASTNumber)
def is_ast_zero(node):
  return is_ast_constant(node)  and  node.number == 0
def is_ast_one(node):
  return is_ast_constant(node)  and  node.number == 1
def is_ast_negative_one(node):
  return is_ast_constant(node)  and  node.number == -1
def is_ast_term_left_constant(node):
  return \
    (isinstance(node, ASTMultiply) and is_ast_constant(node.left)) or \
    (isinstance(node, ASTDivide) and is_ast_constant(node.numerator))
def is_ast_expression(node):
  return isinstance(node, (ASTAdd, ASTSubtract))
def is_ast_term(node):
  return isinstance(node, (ASTMultiply, ASTDivide))

class SimplifyState:
  def __init__(self, node=None, sort_terms=False):
    self.parent = node
    self.sort_terms = sort_terms
  def parent_is_expression(self):
    return is_ast_expression(self.parent)
  def parent_is_term(self):
    return is_ast_term(self.parent)
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
  
  def substitute(self, var, value):
    return self
  def eval(self):
    raise Exception("Implement me!")
  
  def derivative(self, var):
    raise Exception("Implement me!")

class ASTNumber(ASTNode):
  def __init__(self, number):
    if cas_settings.USE_RATIONALS and isinstance(number, int):
      self.number = Rational(number)
    else:
      self.number = number
  
  def pretty_str(self, precidence):
    # if isinstance(self.number, Rational):
    #   return str(self.number)
    return str(int(self.number)) if int(self.number) == self.number else str(self.number)
  def __str__(self):
    return str(self.number)
  
  def negate(self):
    return ASTNumber(self.number * -1)
  def eval(self):
    if cas_settings.USE_RATIONALS:
      return float(self.number)
    return self.number
  def derivative(self, var):
    return ASTNumber(0)

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

class ASTFunctionCall(ASTNode):
  def __init__(self, name, argument):
    self.name = name
    self.argument = argument
  
  def pretty_str(self, precidence):
    return self.name + "(" + self.argument.pretty_str(100) + ")"
  def __str__(self):
    return self.name + "(" + str(self.argument) + ")"
  
  def reduce(self, state):
    return ASTFunctionCall(self.name, self.argument.reduce(state.after(self)))
  def expand(self, state):
    return ASTFunctionCall(self.name, self.argument.expand(state.after(self)))

  def substitute(self, var, value):
    return ASTFunctionCall(self.name, self.argument.substitute(var, value))
  def eval(self):
    if self.name == "sin":
      return sin(self.argument.eval())
    elif self.name == "cos":
      return cos(self.argument.eval())
    raise Exception("Unknown function: " + self.name)
  def derivative_f(self):
    if self.name == "sin":
      return ASTFunctionCall("cos", self.argument)
    elif self.name == "cos":
      return ASTMultiply(
        ASTNumber(-1),
        ASTFunctionCall("sin", self.argument)
      )
  def derivative(self, var):
    return ASTMultiply(
      self.derivative_f(),
      self.argument.derivative(var)
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
    if is_ast_zero(left):
      return right
    if is_ast_zero(right):
      return left
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number + right.number)
    simplified_self = ASTAdd(left, right)
    if original_state.parent_is_expression():
      return simplified_self
    
    from cas_simplify_expr import ExpressionReducer
    return ExpressionReducer(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTAdd(self.left.expand(state), self.right.expand(state))

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
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number - right.number)
    if is_ast_zero(left):
      return ASTMultiply(ASTNumber(-1), right)
    if is_ast_zero(right):
      return left
    if is_ast_constant(left) and left.number < 1:
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
    if is_ast_constant(right) and not is_ast_constant(left):
      (left, right) = (right, left)
    if is_ast_negative_one(left):
      return "-" + right.pretty_str(ASTMultiply.precidence)
    add_multiply = is_ast_constant(right) or is_ast_term_left_constant(right)
    string = left.pretty_str(ASTMultiply.precidence) + \
      ("*" if add_multiply else "") + \
      right.pretty_str(ASTMultiply.precidence)
    if precidence < ASTMultiply.precidence:
      string = "(" + string + ")"
    return string
  def __str__(self):
    return "(" + str(self.left) + "*" + str(self.right) + ")"
  
  def negate(self):
    if is_ast_constant(self.left):
      return ASTMultiply(self.left.negate(), self.right)
    return ASTMultiply(ASTNumber(-1), self)
  
  def reduce(self, original_state):
    state = original_state.after(self)

    left = self.left.reduce(state)
    right = self.right.reduce(state)
    if is_ast_zero(left) or is_ast_zero(right):
      return ASTNumber(0)
    if is_ast_one(right):
      return left
    if is_ast_one(left):
      return right
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number * right.number)
    simplified_self = ASTMultiply(left, right)

    if original_state.parent_is_term():
      return simplified_self
  
    from cas_simplify_expr import ExpressionTerm
    return ExpressionTerm(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTMultiply(self.left.expand(state), self.right.expand(state))
  
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
    if is_ast_constant(self.numerator):
      return ASTDivide(self.numerator.negate(), self.denominator)
    return ASTMultiply(ASTNumber(-1), self)
  
  def reduce(self, original_state):
    state = original_state.after(self)
    
    numerator = self.numerator.reduce(state)
    denominator = self.denominator.reduce(state)
    if is_ast_zero(numerator):
      return ASTNumber(0)
    if is_ast_one(denominator):
      return numerator
    if is_ast_constant(numerator) and is_ast_constant(denominator):
      return ASTNumber(numerator.number / denominator.number)
    simplified_self = ASTDivide(numerator, denominator)

    if original_state.parent_is_term():
      return simplified_self
  
    from cas_simplify_expr import ExpressionTerm
    return ExpressionTerm(simplified_self, original_state).reduce().to_ast().reduce(state)
  def expand(self, state):
    # TODO
    return ASTDivide(self.numerator.expand(state), self.denominator.expand(state))
  
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