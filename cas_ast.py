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

class ASTNode:
  precidence = 0
  def __init__(self):
    raise Exception("Implement me!")
  def __eq__(self, other):
    if type(self) != type(other):
      return False
    for attr in vars(self):
      if getattr(self, attr) != getattr(other, attr):
        return False
    return True
  def __ne__(self, other):
    return not self.__eq__(other)
  def __hash__(self):
    return hash(str(self))
  def __str__(self):
    raise Exception("Implement me!")

  def print(self, precidence):
    raise Exception("Implement me!")
  
  def simplify_in_expr(self):
    return self.simplify()
  def simplify_in_term(self):
    return self.simplify()
  
  def simplify(self):
    return self
  def substitute(self, var, value):
    return self
  def eval(self):
    raise Exception("Implement me!")
  
  def derivative(self, var):
    raise Exception("Implement me!")

class ASTNumber(ASTNode):
  def __init__(self, number):
    self.number = number
  def print(self, precidence):
    if self.number == int(self.number):
      print(str(int(self.number)), end="")
    else:
      print(str(self.number), end="")
  def __str__(self):
    return str(self.number)
  def eval(self):
    return self.number
  def derivative(self, var):
    return ASTNumber(0)

class ASTVariable(ASTNode):
  def __init__(self, name):
    self.name = name
  def print(self, precidence):
    print(self.name, end="")
  def __str__(self):
    return "(" + self.name + ")"
  def substitute(self, var, value):
    if self.name == var:
      return value
    return self
  def eval(self):
    raise Exception("Cannot evaluate variable")
  def derivative(self, var):
    # TODO: non-primary variables
    return ASTNumber(1)

class ASTFunctionCall(ASTNode):
  def __init__(self, name, argument):
    self.name = name
    self.argument = argument
  def print(self, precidence):
    print(self.name+"(", end="")
    self.argument.print(100)
    print(")", end="")
  def __str__(self):
    return self.name + "(" + str(self.argument) + ")"
  def simplify(self):
    return ASTFunctionCall(self.name, self.argument.simplify())
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
    )

class ASTAdd(ASTNode):
  precidence = 4
  def __init__(self, left, right):
    self.left = left
    self.right = right
  def print(self, precidence):
    if precidence < ASTAdd.precidence:
      print("(", end="")
    self.left.print(ASTAdd.precidence)
    print("+", end="")
    self.right.print(ASTAdd.precidence)
    if precidence < ASTAdd.precidence:
      print(")", end="")
  def __str__(self):
    return "(" + str(self.left) + "+" + str(self.right) + ")"
  def simplify_in_expr(self):
    left = self.left.simplify_in_expr()
    right = self.right.simplify_in_expr()
    if is_ast_zero(left):
      return right
    if is_ast_zero(right):
      return left
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number + right.number)
    return ASTAdd(left, right)
  def simplify(self):
    from cas_simplify_expr import ExpressionSimplifier
    return ExpressionSimplifier(
      self.simplify_in_expr()
    ).simplify().to_ast()
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
    )

class ASTSubtract(ASTNode):
  precidence = 4
  def __init__(self, left, right):
    self.left = left
    self.right = right
  def print(self, precidence):
    if precidence < ASTSubtract.precidence:
      print("(", end="")
    self.left.print(ASTSubtract.precidence)
    print("-", end="")
    self.right.print(ASTSubtract.precidence-1)
    if precidence < ASTSubtract.precidence:
      print(")", end="")
  def __str__(self):
    return "(" + str(self.left) + "-" + str(self.right) + ")"
  def simplify_in_expr(self):
    left = self.left.simplify_in_expr()
    right = self.right.simplify_in_expr()
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number - right.number)
    if is_ast_zero(left):
      return ASTMultiply(ASTNumber(-1), right)
    if is_ast_zero(right):
      return left
    return ASTSubtract(left, right)
  def simplify(self):
    from cas_simplify_expr import ExpressionSimplifier
    return ExpressionSimplifier(
      self.simplify_in_expr()
    ).simplify().to_ast()
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
    )

class ASTMultiply(ASTNode):
  precidence = 3
  def __init__(self, left, right):
    self.left = left
    self.right = right
  def print(self, precidence):
    left = self.left
    right = self.right
    if is_ast_constant(right) and not is_ast_constant(left):
      temp = left
      left = right
      right = temp
    if is_ast_negative_one(left):
      print("-", end="")
      right.print(ASTMultiply.precidence)
    else:
      if precidence < ASTMultiply.precidence:
        print("(", end="")
      left.print(ASTMultiply.precidence)
      if is_ast_constant(self.right) or is_ast_term_left_constant(self.right):
       print("*", end="")
      right.print(ASTMultiply.precidence)
      if precidence < ASTMultiply.precidence:
        print(")", end="")
  def __str__(self):
    return "(" + str(self.left) + "*" + str(self.right) + ")"
  def simplify_in_term(self):
    left = self.left.simplify_in_term()
    right = self.right.simplify_in_term()
    if is_ast_zero(left) or is_ast_zero(right):
      return ASTNumber(0)
    if is_ast_one(right):
      return left
    if is_ast_one(left):
      return right
    if is_ast_constant(left) and is_ast_constant(right):
      return ASTNumber(left.number * right.number)
    return ASTMultiply(left, right)
  def simplify(self):
    from cas_simplify_expr import TermSimplifier
    return TermSimplifier(
      self.simplify_in_term()
    ).simplify().to_ast()
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
    )

class ASTDivide(ASTNode):
  precidence = 3
  def __init__(self, numerator, denominator):
    self.numerator = numerator
    self.denominator = denominator
  def print(self, precidence):
    if precidence < ASTDivide.precidence:
      print("(", end="")
    self.numerator.print(ASTDivide.precidence)
    print("/", end="")
    self.denominator.print(ASTDivide.precidence)
    if precidence < ASTDivide.precidence:
      print(")", end="")
  def __str__(self):
    return "(" + str(self.numerator) + "/" + str(self.denominator) + ")"
  def simplify(self):
    from cas_simplify_expr import TermSimplifier
    return TermSimplifier(
      self.simplify_in_term()
    ).simplify().to_ast()
  def substitute(self, var, value):
    return ASTDivide(
      self.numerator.substitute(var, value),
      self.denominator.substitute(var, value)
    )
  def eval(self):
    return self.numerator.eval() / self.denominator.eval()
  def simplify_in_term(self):
    numerator = self.numerator.simplify_in_term()
    denominator = self.denominator.simplify_in_term()
    if is_ast_zero(numerator):
      return ASTNumber(0)
    if is_ast_one(denominator):
      return numerator
    if is_ast_constant(numerator) and is_ast_constant(denominator):
      return ASTNumber(numerator.number / denominator.number)
    return ASTDivide(numerator, denominator)
  
  def derivative(self, var):
    return ASTDivide(
      # ba' - ab'
      ASTSubtract(
        ASTMultiply(self.denominator, self.numerator.derivative(var)),
        ASTMultiply(self.numerator, self.denominator.derivative(var))
      ),
      # ... / b**2
      ASTMultiply(self.denominator, self.denominator)
    )

