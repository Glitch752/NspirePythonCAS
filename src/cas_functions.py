from cas_ast import *
from math import sin, cos, tan

class ASTFunctionCall(ASTNode):
  name = "generic_function"
  precidence = 100
  def __init__(self, argument):
    if type(self) == ASTFunctionCall:
      raise Exception("Cannot create an instance of ASTFunctionCall. Use a subclass or ASTFunctionCall.create() instead.")
    
    self.name = type(self).name
    self.argument = argument
  
  @staticmethod
  def create(name, argument):
    return function_names[name](argument)
  
  def pretty_str(self, precidence):
    return self.name + "(" + self.argument.pretty_str(100) + ")"
  def __str__(self):
    return self.name + "(" + str(self.argument) + ")"
  
  def reduce(self, state):
    return ASTFunctionCall.create(self.name, self.argument.reduce(state.after(self)))
  def expand(self, state):
    return ASTFunctionCall.create(self.name, self.argument.expand(state.after(self)))

  def traverse(self, func):
    self.argument.traverse(func)
    func(self)

  def substitute(self, var, value):
    return ASTFunctionCall.create(self.name, self.argument.substitute(var, value))
  def eval(self):
    raise Exception("Evaluation for function " + self.name + " is not implemented.")
  def derivative_f(self):
    raise Exception("Derivative for function " + self.name + " is not implemented.")
  def derivative(self, var):
    return ASTMultiply(
      self.derivative_f(),
      self.argument.derivative(var)
    ).simplify()


class FunctionSin(ASTFunctionCall):
  name = "sin"
  def eval(self):
    return sin(self.argument.eval())
  def derivative_f(self): # d/dx sin(x) = cos(x)
    return FunctionCos(self.argument)

class FunctionCos(ASTFunctionCall):
  name = "cos"
  def eval(self):
    return cos(self.argument.eval())
  def derivative_f(self): # d/dx cos(x) = -sin(x)
    return ASTMultiply(ASTNumber(-1), FunctionSin(self.argument))

class FunctionTan(ASTFunctionCall):
  name = "tan"
  def eval(self):
    return tan(self.argument.eval())
  def derivative_f(self): # d/dx tan(x) = sec(x)^2
    return ASTMultiply(FunctionSec(self.argument), FunctionSec(self.argument))

class FunctionCsc(ASTFunctionCall):
  name = "csc"
  def eval(self):
    return 1 / sin(self.argument.eval())
  def derivative_f(self): # d/dx csc(x) = -csc(x)*cot(x)
    return ASTMultiply(
      ASTNumber(-1),
      ASTMultiply(FunctionCsc(self.argument), FunctionCot(self.argument))
    )

class FunctionSec(ASTFunctionCall):
  name = "sec"
  def eval(self):
    return 1 / cos(self.argument.eval())
  def derivative_f(self): # d/dx sec(x) = sec(x)*tan(x)
    return ASTMultiply(FunctionSec(self.argument), FunctionTan(self.argument))

class FunctionCot(ASTFunctionCall):
  name = "cot"
  def eval(self):
    return 1 / tan(self.argument.eval())
  def derivative_f(self): # d/dx cot(x) = -csc(x)^2
    return ASTMultiply(
      ASTNumber(-1),
      ASTMultiply(FunctionCsc(self.argument), FunctionCsc(self.argument))
    )

function_names = {
  "sin": FunctionSin,
  "cos": FunctionCos,
  "tan": FunctionTan,
  "csc": FunctionCsc,
  "sec": FunctionSec,
  "cot": FunctionCot,

  # TODO: Inverse trigonometric functions
}