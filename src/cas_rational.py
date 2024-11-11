from math import fabs

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
            return Rational(self.numerator ** other.numerator, self.denominator ** other.numerator)
        # TODO: We can simplify _some_ cases where the denominator isn't 1.
        # For example, (4/1)^(1/2) should be (2/1) but we don't handle that.
        return None

    def __float__(self):
        return self.numerator / self.denominator
    
    def __int__(self):
        return int(self.numerator // self.denominator)