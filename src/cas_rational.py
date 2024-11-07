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

class Rational:
    def __init__(self, numerator, denominator=1):
        if isinstance(numerator, Rational):
            self.numerator = numerator.numerator
            self.denominator = numerator.denominator
            if isinstance(denominator, Rational):
                self.numerator *= denominator.denominator
                self.denominator *= denominator.numerator
            else:
                self.denominator *= denominator
        else:
            self.numerator = int(numerator)
            self.denominator = 1
            if isinstance(denominator, Rational):
                self.denominator = denominator.numerator
                self.numerator *= denominator.denominator
            else:
                self.denominator = int(denominator)
        
        self.reduce()
    
    def reduce(self):
        if self.denominator < 0:
            self.numerator *= -1
            self.denominator *= -1
        g = gcd([self.numerator, self.denominator])
        self.numerator //= g
        self.denominator //= g
    
    def __add__(self, other):
        if isinstance(other, Rational):
            return Rational(self.numerator * other.denominator + other.numerator * self.denominator, self.denominator * other.denominator)
        return Rational(self.numerator + other * self.denominator, self.denominator)
    
    def __sub__(self, other):
        if isinstance(other, Rational):
            return Rational(self.numerator * other.denominator - other.numerator * self.denominator, self.denominator * other.denominator)
        return Rational(self.numerator - other * self.denominator, self.denominator)

    def __mul__(self, other):
        if isinstance(other, Rational):
            return Rational(self.numerator * other.numerator, self.denominator * other.denominator)
        return Rational(self.numerator * other, self.denominator)
    
    def __truediv__(self, other):
        if isinstance(other, Rational):
            return Rational(self.numerator * other.denominator, self.denominator * other.numerator)
        return Rational(self.numerator, self.denominator * other)
    
    def __floordiv__(self, other):
        if isinstance(other, Rational):
            return self / other
        return Rational(self.numerator // other, self.denominator)

    def __mod__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)
        return self - other * (self // other)

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
            return str(self.numerator)
        return str(self.numerator) + "/" + str(self.denominator)
    
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