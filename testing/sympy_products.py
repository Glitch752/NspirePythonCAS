from sympy import symbols
import sympy.printing.tree

# (a*b)/(c*d)
a, b, c, d = symbols('a b c d')
expr = (a*b) / (c/d**2)

sympy.printing.tree.print_tree(expr)
print(expr.as_ordered_factors())
print(expr)