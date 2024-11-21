from cas_ast import *
from math import *
from cas_rational import gcd
import cas_settings

def to_multiplication_chain(parts):
  if len(parts) == 0:
    return ASTNumber(1)

  node = parts.pop()
  while len(parts) > 0:
    node = ASTMultiply(parts.pop(), node)
  
  return node

# A class that simplifies a nested expression and its terms
class ExpressionReducer:
  def __init__(self, terms, state):
    self.common_terms = []
    self.state = state
    self.terms = [ExpressionTerm(term, state) for term in terms]
  
  def reduce(self):
    # Remove 0 terms
    i = 0
    while i < len(self.terms):
      if self.terms[i].constant == 0:
        self.terms.pop(i)
        i -= 1
      i += 1
    
    if len(self.terms) > 1:
      # Combine like terms
      # This is really inefficient, but it works.
      # TODO: use a hash table or something
      i = 0
      while i < len(self.terms):
        term = self.terms[i]
        j = i + 1
        while j < len(self.terms):
          other = self.terms[j]
          if term.numerator_terms == other.numerator_terms and term.denominator_terms == other.denominator_terms:
            term.constant += other.constant
            self.terms.pop(j)
            j -= 1
          j += 1
        i += 1
      
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
          self.common_terms.append(ASTDivide(ASTNumber(1), factor))
        for term in self.terms:
          for factor in com_den_factors:
            term.denominator_terms.remove(factor)
      
      coefficients = []
      all_negative = True
      for term in self.terms:
        if term.constant % 1 != 0:
          coefficients = []
          break
        coefficients.append(abs(term.constant))
        all_negative &= term.constant < 0 
      
      if len(coefficients) > 0:
        hcf = gcd(coefficients) * (-1 if all_negative else 1)

        if hcf != 1:
          self.common_terms.append(
            ASTNumber(hcf)
          )
          for term in self.terms:
            term.divide(hcf)
    
    return self
  
  def to_ast(self):
    parts = list(self.terms) # clone
    
    if len(parts) == 0:
      return ASTNumber(0)
    
    if self.state.sort_terms:
      parts.sort(key=lambda x: x.__str__())
    
    terms = []
    if len(self.common_terms) > 0:
      terms = list(self.common_terms)
    
    if len(parts) > 0:
      terms.append(ASTSum([part.to_ast() for part in parts]))
    
    if len(terms) == 0:
      return ASTNumber(0)
    
    if self.state.sort_terms:
      terms.sort(key=lambda x: x.__str__())
    
    return to_multiplication_chain(terms)

class ExpressionTerm:
  def __init__(self, node, state):
    self.state = state.after(node)

    if not node.is_term():
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
        if n[1].left.is_term():
          nodes.append((n[0], n[1].left))
        else:
          (denominator if n[0] else numerator).append(n[1].left)
        if n[1].right.is_term():
          nodes.append((n[0], n[1].right))
        else:
          (denominator if n[0] else numerator).append(n[1].right)
      else:
        if n[1].numerator.is_term():
          nodes.append((n[0], n[1].numerator))
        else:
          (denominator if n[0] else numerator).append(n[1].numerator)
        if n[1].denominator.is_term():
          nodes.append((not n[0], n[1].denominator))
        else:
          (numerator if n[0] else denominator).append(n[1].denominator)
    
    self.numerator_terms = numerator
    self.denominator_terms = denominator
    
    self.compute_constant()
  
  def __str__(self):
    return "Term(" + str(self.numerator_terms) + ", " + str(self.denominator_terms) + ", " + str(self.constant) + ")"
  def __repr__(self):
    return self.__str__()
  
  def negate(self):
    self.constant *= -1
    return self
  
  def divide(self, by):
    self.constant /= by
  
  def is_number(self):
    return len(self.numerator_terms) == 0 and len(self.denominator_terms) == 0
  
  def reduce_terms(self):
    for i in range(len(self.numerator_terms)):
      self.numerator_terms[i] = \
        self.numerator_terms[i].reduce(self.state)
    for i in range(len(self.denominator_terms)):
      self.denominator_terms[i] = \
        self.denominator_terms[i].reduce(self.state)
  
  def compute_constant(self):
    self.constant = Rational(1) if cas_settings.USE_RATIONALS else 1
    self.reduce()
    
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
  
  def reduce(self):
    self.reduce_terms()

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
    if (len(numerator) == 0 and len(denominator) == 0) or self.constant == 0:
      return ASTNumber(self.constant)
    numerator_ast = None

    if len(numerator) > 0:
      if self.state.sort_terms:
        numerator.sort(key=lambda x: x.__str__())
      
      chain = to_multiplication_chain(numerator)
      numerator_ast = \
        ASTMultiply(ASTNumber(self.constant), chain) \
        if self.constant != 1 else chain
    else:
      numerator_ast = ASTNumber(self.constant)
    
    if len(denominator) == 0:
      return numerator_ast
    
    if self.state.sort_terms:
      denominator.sort(key=lambda x: x.__str__())
    
    return ASTDivide( # TODO: proper rationals?
      numerator_ast,
      to_multiplication_chain(denominator)
    )