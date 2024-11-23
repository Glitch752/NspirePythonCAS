from math import fabs

# Returns a dictionary of prime factors and their exponents
def prime_factors(n):
  factors = {}
  i = 2
  while i * i <= abs(n):
    while n % i == 0:
      if i in factors:
        factors[i] += 1
      else:
        factors[i] = 1
      n //= i
    i += 1
  if n > 1:
      factors[n] = 1
  return factors

# Returns the exact logarithm of x to the base of base.
# If no rational result is possible, returns None.
# TODO: This is really slow and inefficient, so we should
# probably add a setting to disable it since it can take
# multiple seconds on calculators to calculate a single time.
# We should also probably cache results.
def exact_rational_log(x, base):
  # Easy cases
  if x <= 0 or base <= 0:
    return None # Undefined
  if x == 1:
    return Rational(0)
  if base == 1:
    return None # Undefined for base 1 unless x == 1
  if x == base:
    return Rational(1) # Trivial
  
  a, b = x.numerator, x.denominator
  c, d = base.numerator, base.denominator

  # We need to find integers p and q such that:
  # (exp_a - exp_b) * q = (exp_c - exp_d) * p

  # We can solve this using general principles for
  # solving Diophantine equations (I think lol)
  # https://en.wikipedia.org/wiki/Diophantine_equation

  factors_a = prime_factors(a)
  factors_b = prime_factors(b)
  factors_c = prime_factors(c)
  factors_d = prime_factors(d)

  p, q = None, None

  # Check consistency of all prime factors
  for prime in set(factors_a) | set(factors_b) | set(factors_c) | set(factors_d):
    exp_a = factors_a.get(prime, 0)
    exp_b = factors_b.get(prime, 0)
    exp_c = factors_c.get(prime, 0)
    exp_d = factors_d.get(prime, 0)

    num = exp_a - exp_b
    denom = exp_c - exp_d

    if denom == 0:
      if num != 0:
        return None # Inconsistent equation, no solution exists
      else:
        continue # This prime factor has no constraints

    # We need (num / denom) to be consistent across all prime factors
    candidate_p, candidate_q = num, denom

    if candidate_q < 0:
      candidate_p = -candidate_p
      candidate_q = -candidate_q

    # Reduce the fraction (p / q)
    g = fast_2_gcd(candidate_p, candidate_q)
    candidate_p //= g
    candidate_q //= g

    # Check for consistency with previous solutions
    if p == None and q == None:
      p, q = candidate_p, candidate_q
    elif p * candidate_q != candidate_p * q:
      return None # Inconsistent solutions

  if p != None and q != None:
    return Rational(p, q)
  return None


def gcd(data):
  a = data[0]
  b = 0
  for i in range(1, len(data)):
    b = data[i]
    while b != 0:
      a, b = b, a % b
    
    if a == 1:
      return 1
  return a

def fast_2_gcd(a, b):
  while b != 0:
    a, b = b, a % b
  return a

class Rational:
  def __init__(self, numerator, denominator=1):
    if isinstance(numerator, Rational):
      self.numerator = numerator.numerator
      self.denominator = numerator.denominator
      if isinstance(denominator, Rational):
        self.numerator *= denominator.denominator
        self.denominator *= denominator.numerator
      else:
        if int(denominator) != denominator:
          raise Exception("Rational numbers cannot be created from floats")
        self.denominator *= denominator
    else:
      if int(numerator) != numerator:
        raise Exception("Rational numbers cannot be created from floats")
      self.numerator = int(numerator)
      self.denominator = 1
      if isinstance(denominator, Rational):
        self.denominator = denominator.numerator
        self.numerator *= denominator.denominator
      else:
        if int(denominator) != denominator:
          raise Exception("Rational numbers cannot be created from floats")
        self.denominator = int(denominator)
    
    self.reduce()
  
  def reduce(self):
    if self.denominator < 0:
      self.numerator *= -1
      self.denominator *= -1
    g = fast_2_gcd(int(fabs(self.numerator)), int(fabs(self.denominator)))
    if g == 0:
      # Probably shouldn't happen, but just in case
      return
    self.numerator //= g
    self.denominator //= g
  
  def __add__(self, other):
    if isinstance(other, Rational):
      return Rational(self.numerator * other.denominator + other.numerator * self.denominator, self.denominator * other.denominator)
    return Rational(self.numerator + other * self.denominator, self.denominator)
  def __radd__(self, other):
    return self + other
  
  def __sub__(self, other):
    if isinstance(other, Rational):
      return Rational(self.numerator * other.denominator - other.numerator * self.denominator, self.denominator * other.denominator)
    return Rational(self.numerator - other * self.denominator, self.denominator)
  def __rsub__(self, other):
    return -self + other

  def __mul__(self, other):
    if isinstance(other, Rational):
      return Rational(self.numerator * other.numerator, self.denominator * other.denominator)
    return Rational(self.numerator * other, self.denominator)
  def __rmul__(self, other):
    return self * other
  
  def __truediv__(self, other):
    if isinstance(other, Rational):
      return Rational(self.numerator * other.denominator, self.denominator * other.numerator)
    return Rational(self.numerator, self.denominator * other)
  def __rtruediv__(self, other):
    return Rational(other) / self
  
  def __floordiv__(self, other):
    return (self / other).__int__()
  def __rfloordiv__(self, other):
    return Rational(other) // self

  def __mod__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    return self - other * (self // other)
  def __rmod__(self, other):
    return Rational(other) % self

  def __lt__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    return self.numerator * other.denominator < other.numerator * self.denominator
  
  def __le__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    return self.numerator * other.denominator <= other.numerator * self.denominator
  
  def __gt__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    return self.numerator * other.denominator > other.numerator * self.denominator
  
  def __ge__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    return self.numerator * other.denominator >= other.numerator * self.denominator
  
  def __eq__(self, other):
    if not isinstance(other, Rational):
      if other == None:
        return False
      other = Rational(other)
    return self.numerator == other.numerator and self.denominator == other.denominator
  
  def __str__(self):
    if self.denominator == 1:
      return str(int(self.numerator))
    return str(int(self.numerator)) + "/" + str(int(self.denominator))
  
  def __repr__(self):
    return str(self)
  
  def __neg__(self):
    return Rational(-self.numerator, self.denominator)
  
  def __abs__(self):
    return Rational(abs(self.numerator), abs(self.denominator))
  
  # Returns None if the result is not a rational number
  def __pow__(self, other):
    if not isinstance(other, Rational):
      other = Rational(other)
    if other.denominator == 1:
      power = other.numerator
      if power >= 0:
        return Rational(self.numerator ** power, self.denominator ** power)
      else: # Negative power
        return Rational(self.denominator ** abs(power), self.numerator ** abs(power))
    return None

  def __float__(self):
    return self.numerator / self.denominator
  
  def __int__(self):
    return int(self.numerator // self.denominator)