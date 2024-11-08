# TI-NSpire Python CAS

A simple Python program I've been developing on my TI-NSpire CX II calculator to replicate the abilities of the CAS software. It's a work in progress, and it will probably never get very good, but it can take simple derivatives and simplify expressions in some ways.

It consists of a simple tokenizer, parser, and evaluator with support for arithmetic, variables, and built-in functions (currently only `sin` and `cos`). For example, it can parse, evaluate, take the derivative of, and simplify something like `2*cos(5 + x*2) + 6*x*y`.

The simplification is relatively basic; it supports constant folding, basic identities (e.g. `0*x = 0`, `1*x = x`, `x + 0 = x`, etc.), associative expression factoring (e.g. `2*x*y + 4*x*x*y` -> `2*x*y*(1 + 2*x)`), and some simple term rewriting (e.g. `x*y/x/x*y` -> `y*y/x`).

Most of the code in this repository is written on my calculator and exported to my computer, but I'm trying to avoid TI-specific Python modules to make it portable.

The code isn't structured very well, but it's mostly me messing around, so I'm not super worried about making a robust codebase.

## Future ideas
- [ ] Add better error handling for the tokenizer and parser
- [ ] Make negative numbers in expressions more elegant; for example, we currently output stuff like `2+-3x` instead of `2-3x` and `-2+3x` instead of `3x-2`
- [ ] Add more built-in functions
- [ ] Support decimals and other number representations
  - [ ] When parsing, decide between subtract and negative number so we don't need to use the `−` character
- [ ] Add other functions (e.g. `tan`, `log`)
- [ ] Add trig identities
- [ ] Add exponentiation support
- [X] Internally represent numbers as rationals to avoid floating-point errors and allow exact simplification in more cases
- [ ] Add support for symbolic constants like `pi`, `e`, etc.
- [X] Add support for non-primary variables of differentiation so we can take partial derivatives
- [ ] Add the ability to solve equations for specific variables symbolically
- [ ] Add the ability to solve systems of equations symbolically
- [ ] Add support for integrals (probably not going to happen)
- [ ] Add support for limits (probably not going to happen)
- [ ] Add support for complex numbers (probably not going to happen)

# Running
You don't need to have a TI-NSpire to run this code; it's regular Python.
You can run my (small) test suite with `python src/cas_tests.py`, or you can run the REPL with `python src/cas_repl.py`.
`src/caslol.py` is just a file I use for testing.

# Note
I'm not certain the simplification or differentiation are perfect, so I wouldn't trust this for anything important. I've extensively compared its outputs to those of Wolfram|Alpha, though, and it seems to be correct.