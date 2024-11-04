from cas_ast import *
from math import *

def gcd(data):  
  a = data[0]
  b = 0
  for i in range(1, len(data)):
    b = data[i]
    while a*b > 0:
      if a > b:
        a = a % b
      else:
        b  = b % a
    if a == 0:
      a = b
  return b if a == 0 else a

def to_multiplication_chain(parts):
  if len(parts) == 0:
    return ASTNumber(1)

  node = parts.pop()
  while len(parts) > 0:
    node = ASTMultiply(parts.pop(), node)
  
  return node

class ExpressionSimplifier:
  def __init__(self, topmost_node):
    self.common_terms = []
    self.node = topmost_node
    self.terms = []
    self.get_terms()
  
  def get_terms(self):
    node = self.node
    if not is_ast_expression(node):
      self.terms = [TermSimplifier(node)]
      return
    
    # (Subtracting, node)
    nodes = [(False, node)]
    add = []
    subtract = []
    while len(nodes) > 0:
      n = nodes.pop()
      adding = isinstance(n[1], ASTAdd)
      if is_ast_expression(n[1].left):
        nodes.append((n[0], n[1].left))
      else:
        (subtract if n[0] else add).append(TermSimplifier(n[1].left))
      if is_ast_expression(n[1].right):
        nodes.append((n[0] ^ (not adding), n[1].right))
      else:
        (add if (n[0] ^ adding) else subtract).append(TermSimplifier(n[1].right))
    
    self.terms = add
    for term in subtract:
      self.terms.append(term.negate())
  
  def simplify(self):
    # Remove 0 terms
    i = 0
    while i < len(self.terms):
      if self.terms[i].constant == 0:
        self.terms.pop(i)
        i -= 1
      i += 1
    
    if len(self.terms) > 1:
      for i in range(len(self.terms)):
        self.terms[i] = self.terms[i].simplify() # TODO: I don't think we technically need to simplify here
      
      # Factor out common terms
      com_num_factors = set(self.terms[0].numerator_terms)
      com_den_factors = set(self.terms[0].denominator_terms)
      for term in self.terms[1:]:
        com_num_factors.intersection_update(term.numerator_terms)
        com_den_factors.intersection_update(term.denominator_terms)
      if len(com_num_factors) > 0:
        self.common_terms.extend(com_num_factors)
        for term in self.terms:
          for factor in com_num_factors:
            term.numerator_terms.remove(factor)
      if len(com_den_factors) > 0:
        for factor in com_den_factors:
          self.common_terms.extend(ASTDivide(ASTNumber(1), factor))
        for term in self.terms:
          for factor in com_den_factors:
            term.denominator_terms.remove(factor)

      coefficients = []
      all_negative = True
      for term in self.terms:
        if term.constant % 1 != 0:
          coefficients = []
          break
        coefficients.append(fabs(term.constant))
        all_negative &= term.constant < 0 
      
      if len(coefficients) > 0:
        hcf = gcd(coefficients) * (-1 if all_negative else 1)
        
        if hcf != 1:
          self.common_terms.append(
            ASTNumber(hcf)
          )
          for term in self.terms:
            term.divide(hcf)
    
    # Merge numerical terms
    number = 0
    i = 0
    while i < len(self.terms):
      term = self.terms[i]
      if term.is_number():
        number += term.constant
        self.terms.pop(i)
        i -= 1
      i += 1
    
    if number != 0:
      self.terms.append(TermSimplifier(ASTNumber(number)))

    return self
  
  def to_ast(self):
    parts = list(self.terms) # clone

    if len(parts) == 0:
      return ASTNumber(0)

    terms = []
    if len(self.common_terms) > 0:
      terms = list(self.common_terms)
    
    if len(parts) > 0:
      node = parts.pop().to_ast()
      while len(parts) > 0:
        # TODO: subtract when negative
        node = ASTAdd(parts.pop().to_ast(), node)
      
      terms.append(node)
    
    if len(terms) == 0:
      return ASTNumber(0)
    
    return to_multiplication_chain(terms).simplify_in_expr()

class TermSimplifier:
  def __init__(self, node):
    if not is_ast_term(node):
      self.numerator_terms = [node]
      self.denominator_terms = []
      self.compute_constant()
      return
    
    # (In denominator, node)
    nodes = [(False, node)]
    numerator = []
    denominator = []
    while len(nodes) > 0:
      n = nodes.pop()
      if isinstance(n[1], ASTMultiply):
        if is_ast_term(n[1].left):
          nodes.append((n[0], n[1].left))
        else:
          (denominator if n[0] else numerator).append(n[1].left)
        if is_ast_term(n[1].right):
          nodes.append((n[0], n[1].right))
        else:
          (denominator if n[0] else numerator).append(n[1].right)
      else:
        if is_ast_term(n[1].numerator):
          nodes.append((n[0], n[1].numerator))
        else:
          (denominator if n[0] else numerator).append(n[1].numerator)
        if is_ast_term(n[1].denominator):
          nodes.append((not n[0], n[1].denominator))
        else:
          (numerator if n[0] else denominator).append(n[1].denominator)
    
    self.numerator_terms = numerator
    self.denominator_terms = denominator
    
    self.compute_constant()
  
  def negate(self):
    self.constant *= -1
    return self
  
  def divide(self, by):
    self.constant /= by
  
  def is_number(self):
    return len(self.numerator_terms) == 0 and len(self.denominator_terms) == 0
  
  def simplify_terms(self):
    for i in range(len(self.numerator_terms)):
      self.numerator_terms[i] = \
        self.numerator_terms[i].simplify()
    for i in range(len(self.denominator_terms)):
      self.denominator_terms[i] = \
        self.denominator_terms[i].simplify()
  
  def compute_constant(self):
    self.constant = 1
    self.simplify()
    
    i = 0
    while i < len(self.numerator_terms):
      term = self.numerator_terms[i]
      if isinstance(term, ASTNumber):
        self.constant *= term.number
        self.numerator_terms.pop(i)
        i -= 1
      i += 1
    
    i = 0
    while i < len(self.denominator_terms):
      term = self.denominator_terms[i]
      if isinstance(term, ASTNumber):
        self.constant /= term.number
        self.denominator_terms.pop(i)
        i -= 1
      i += 1
  
  def simplify(self):
    self.simplify_terms()

    # Cancel any shared terms in the numerator and denominator
    i = 0
    while i < len(self.numerator_terms):
      term = self.numerator_terms[i]
      if term in self.denominator_terms:
        self.numerator_terms.pop(i)
        self.denominator_terms.remove(term)
        i -= 1
      i += 1

    return self
  
  def to_ast(self):    
    numerator = list(self.numerator_terms)
    denominator = list(self.denominator_terms)
    if len(numerator) == 0 or self.constant == 0:
      return ASTNumber(self.constant)
    chain = to_multiplication_chain(numerator)
    numerator_ast = \
      ASTMultiply(ASTNumber(self.constant), chain) \
      if self.constant != 1 else chain
    if len(denominator) == 0:
      return numerator_ast
    return ASTDivide( # TODO: proper rationals?
      numerator_ast,
      to_multiplication_chain(denominator)
    )