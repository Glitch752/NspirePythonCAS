from cas_ast import *
from math import *
from cas_rational import gcd
import cas_settings

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
          if term.terms == other.terms:
            term.constant += other.constant
            self.terms.pop(j)
            j -= 1
          j += 1
        i += 1
      
      # Factor out common terms
      common_factors = set(self.terms[0].terms)
      for term in self.terms[1:]:
        common_factors.intersection_update(term.terms)
      if len(common_factors) > 0:
        self.common_terms.extend(common_factors)
        for term in self.terms:
          for factor in common_factors:
            term.terms.remove(factor)
      
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
    
    if len(terms) == 1:
      return terms[0]
    
    return ASTProduct(terms)

class ExpressionTerm:
  def __init__(self, terms, state):
    self.state = state

    if isinstance(terms, list):
      self.terms = terms
    else:
      self.terms = [terms]
    
    self.compute_constant()
  
  def __str__(self):
    return "Term(" + str(self.constant) + ", " + str(self.terms) + ")"
  def __repr__(self):
    return self.__str__()
  
  def negate(self):
    self.constant *= -1
    return self
  
  def divide(self, by):
    self.constant /= by
  
  def is_number(self):
    return len(self.terms) == 0
  
  def compute_constant(self):
    self.constant = Rational(1) if cas_settings.USE_RATIONALS else 1
    self.reduce()
    
    i = 0
    while i < len(self.terms):
      term = self.terms[i]
      if isinstance(term, ASTNumber):
        self.constant *= term.number
        self.terms.pop(i)
        i -= 1
      i += 1
  
  def reduce(self):
    for i in range(len(self.terms)):
      self.terms[i] = self.terms[i].reduce(self.state)

    return self
  
  def to_ast(self):
    if len(self.terms) == 0 or self.constant == 0:
      return ASTNumber(self.constant)
    
    if self.state.sort_terms:
      self.terms.sort(key=lambda x: x.__str__())
    
    return ASTProduct([ASTNumber(self.constant)] + self.terms)