from cas_ast import *
from cas_functions import ASTFunctionCall
import cas_settings
from cas_rational import Rational

def is_letter(c):
  return "a" <= c <= "z" or "A" <= c <= "Z"
def is_number(c):
  return "0" <= c <= "9"

class TokenType:
  NUMBER = 0
  OPEN_PAREN = 1
  CLOSE_PAREN = 2
  IDENTIFIER = 3
  MULTIPLY = 4
  DIVIDE = 5
  ADD = 6
  SUBTRACT = 7
  EXPONENT = 8
  # Used in logarithms
  UNDERSCORE = 9

token_names = {}
token_chars = {}
longest_token_char = 0
def add_tok(type, name, chars=None):
  global longest_token_char
  token_names[type] = name
  if chars != None:
    if isinstance(chars, str):
      chars = [chars]
    
    for char in chars:
      token_chars[char] = type
      longest_token_char = max(longest_token_char, len(char))

add_tok(TokenType.NUMBER, "Number")
add_tok(TokenType.OPEN_PAREN, "OpenParen", "(")
add_tok(TokenType.CLOSE_PAREN, "CloseParen", ")")
add_tok(TokenType.IDENTIFIER, "Identifier")
add_tok(TokenType.MULTIPLY, "Multiply", "*")
add_tok(TokenType.DIVIDE, "Divide", "/")
add_tok(TokenType.ADD, "Add", "+")
add_tok(TokenType.SUBTRACT, "Subtract", "-")
add_tok(TokenType.EXPONENT, "Exponent", "^")
# ",," is an alternative to "_" because "_" is difficult
# to type in prompt inputs on NSpire calculators.
add_tok(TokenType.UNDERSCORE, "Underscore", ("_", ",,"))

class Token:
  def __init__(self, type, literal):
    self.type = type
    self.literal = literal
  def __str__(self):
    string = token_names[self.type] + "("
    
    if self.type == TokenType.NUMBER:
      string += str(self.literal)
    elif self.type == TokenType.IDENTIFIER:
      string += '"' + str(self.literal) + '"'
    
    string += ")"
    return string
  def __repr__(self):
    return str(self)

class Tokens:
  def __init__(self, str):
    self.str = str
    self.idx = 0
    self.list = []
  
  def test_token_chars(self):
    to_test = min(len(self.str) - self.idx, longest_token_char)
    for i in range(to_test, 0, -1):
      chars = self.str[self.idx : self.idx + i]
      if chars in token_chars:
        self.list.append(Token(token_chars[chars], chars))
        self.idx += i
        return True
    return False
  
  def test_identifier(self):
    ident = ""
    while self.idx < len(self.str) and \
        is_letter(self.str[self.idx]):
      ident += self.str[self.idx]
      self.idx += 1
    if len(ident) > 0:
      self.list.append(Token(TokenType.IDENTIFIER, ident))
      return True
    return False
  
  def test_number(self):
    # TODO: More number formats including decimals
    # TODO: Somehow decide between subtract and negative number so we don't need to use −
    # TODO: Proper rational number support
    num = ""
    negative_symbols = ["−"]
    if self.str[self.idx] in negative_symbols:
      num = "-"
      self.idx += 1
    while self.idx < len(self.str) and is_number(self.str[self.idx]):
      num += self.str[self.idx]
      self.idx += 1
    if len(num) > 0:
      number = int(num)
      if cas_settings.USE_RATIONALS:
        number = Rational(number)
      self.list.append(Token(TokenType.NUMBER, number))
      return True
    
    return False
  
  def parse(self):
    self.list = []
    while self.idx < len(self.str):
      char = self.str[self.idx]
      
      if self.test_identifier():
        continue
      if self.test_token_chars():
        continue
      if self.test_number():
        continue
      
      if char == " ":
        self.idx += 1
        continue
      
      # This is an unknown character
      raise Exception("Unknown character: " + char)
  
  def p_error(self, err):
    # TODO: store token positions, better errors
    print(err)
    raise Exception(err)
  
  def p_peek(self):
    if self.idx >= len(self.list):
      self.p_error("Unexpected end")
    return self.list[self.idx]
  
  def p_peek_next(self):
    if self.idx+1 >= len(self.list):
      self.p_error("Unexpected end")
    return self.list[self.idx+1]
  
  def p_take_if(self, type):
    if self.idx == len(self.list):
      return None
    tok = self.p_peek()
    if tok.type == type:
      self.idx += 1
      return tok
    return None
  
  def p_take_expect(self, type):
    tok = self.p_peek()
    if tok.type == type:
      self.idx += 1
      return tok
    self.p_error("Expected " + token_names[type] + ", found " + token_names[tok.type])
    
  def p_take(self):
    tok = self.p_peek()
    self.idx += 1
    return tok

  def to_ast(self):
    self.idx = 0
    expression = self.p_expr()
    if self.idx < len(self.list):
      self.p_error("Unexpected tokens at end of input: " + str(self.list[self.idx:]))
    return expression
  
  # Recursive descent parser grammar:
  # Expression -> Term ((+ | -) Term)*
  # Term -> Power ((* | /) Power)*
  # Power -> Factor (^ Factor)*
  # Factor -> Number | (Expression) | FunctionCall | Identifier
  # FunctionCall -> Identifier (Expression)
  
  def p_expr(self):
    node = self.p_term()
    while self.idx < len(self.list) and self.p_peek().type in [TokenType.ADD, TokenType.SUBTRACT]:
      op = self.p_take()
      right = self.p_term()
      if op.type == TokenType.ADD:
        node = ASTAdd(node, right)
      else:
        node = ASTSubtract(node, right)
    return node

  def p_term(self):
    node = self.p_power()
    while self.idx < len(self.list) and self.p_peek().type in [TokenType.MULTIPLY, TokenType.DIVIDE]:
      op = self.p_take()
      right = self.p_power()
      if op.type == TokenType.MULTIPLY:
        node = ASTMultiply(node, right)
      else:
        node = ASTDivide(node, right)
    return node

  # Right-associative
  def p_power(self):
    node = self.p_factor()
    if self.idx < len(self.list) and self.p_peek().type == TokenType.EXPONENT:
      self.p_take()
      # Recursive for right associativity
      right = self.p_power()
      node = ASTPower(node, right)
    return node

  def p_factor(self):
    tok = self.p_peek()
    if tok.type == TokenType.NUMBER:
      return ASTNumber(self.p_take().literal)
    elif tok.type == TokenType.OPEN_PAREN:
      self.p_take()
      node = self.p_expr()
      self.p_take_expect(TokenType.CLOSE_PAREN)
      return node
    elif tok.type == TokenType.IDENTIFIER:
      return self.p_ident_or_func()

    self.p_error("Unexpected token: " + token_names[tok.type])
  
  def p_ident_or_func(self):
    ident = self.p_take()
    
    if ident.literal == "log" and self.p_take_if(TokenType.UNDERSCORE):
      # This is a logarithm
      # If the next token is a number, we have a log with a specified base
      # If not, expect parentheses and an argument
      base = None
      if self.p_peek().type == TokenType.NUMBER:
        base = ASTNumber(self.p_take().literal)
      else:
        self.p_take_expect(TokenType.OPEN_PAREN)
        base = self.p_expr()
        self.p_take_expect(TokenType.CLOSE_PAREN)
      
      self.p_take_expect(TokenType.OPEN_PAREN)
      argument = self.p_expr()
      self.p_take_expect(TokenType.CLOSE_PAREN)
      return ASTLogarithm(base, argument)

    if self.p_take_if(TokenType.OPEN_PAREN):
      argument = self.p_expr()
      self.p_take_expect(TokenType.CLOSE_PAREN)
      return ASTFunctionCall.create(ident.literal, argument)
    
    if ident.literal in builtin_variables:
      return builtin_variables[ident.literal]
    
    return ASTVariable(ident.literal)
  
  def print(self):
    print("Tokens: ")
    for token in self.list:
      token.print()

def parse_to_ast(str):
  tokens = Tokens(str)
  tokens.parse()
  return tokens.to_ast()