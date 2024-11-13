# TI-NSpire Python CAS

A small Python program I've been developing on my TI-NSpire CX II calculator to replicate the abilities of the CAS software. It's a work in progress, and it will probably never get very good, but it can take derivatives and simplify expressions in some ways.

It consists of a simple tokenizer, parser, and evaluator with support for arithmetic, variables, and built-in functions. For example, it can parse, evaluate, take the derivative of, and simplify something like `2*cos(5 + x*2) + 6*x*y`.

The simplification is relatively basic; it supports constant folding, basic identities (e.g. `0*x = 0`, `1*x = x`, `x + 0 = x`, etc.), associative expression factoring (e.g. `2*x*y + 4*x*x*y` -> `2*x*y*(1 + 2*x)`), and some simple term rewriting (e.g. `x*y/x/x*y` -> `y*y/x`).

It also optionally supports internally representing all operations as rationals to avoid floating-point errors and allow exact simplification in more cases.

Most of the initial code was written on my calculator and exported to my computer, but I'm avoiding TI-specific Python modules to make it portable.
Some parts, like most unit tests and some of the later code, were written on my computer and tested on my calculator to make things easier.

The code isn't structured very well, but it's mostly me messing around, so I'm not super worried about making a robust codebase.

# Running
You don't need to have a TI-NSpire to run this code; it's regular Python.
You can run my (small) test suite with `python src/cas_tests.py`, or you can run the REPL with `python src/cas_repl.py`.  

You should also be able to run it with the Windows or Unix ports of [MicroPython](https://github.com/micropython/micropython) (the interpreter TI-NSpire python is based on) with `micropython src/cas_repl.py`, but due to the recursive nature of the parser and evaluator, you [may run into stack size issues](https://github.com/micropython/micropython/issues/2927)--especially if you're using the MSVC build. This fortunately isn't an issue in the NSpire environment, but it's something to be aware of. I've had success setting `MICROPY_STACK_CHECK` to `0` in `ports/windows/mpconfigport.h` and running a release build when using MSVC. The Linux builds I used have a slightly low recursion limit (~40 levels), but it's enough to make it through the test suite and relatively complex expressions. There isn't a great reason to use MicroPython on a powerful computer except testing for compatibility with the calculator, but it's an option.

`src/caslol.py` is just a file I use for testing.

## Future ideas
- [ ] Add better error handling for the tokenizer and parser
- [X] Add a better REPL that lets you pick operations instead of returning information about expressions
- [X] Make negative numbers in expressions more elegant; for example, we currently output stuff like `2+-3x` instead of `2-3x` and `-2+3x` instead of `3x-2`
- [ ] Add more built-in functions
  - [X] All main trig functions: `tan`, `csc`, `sec`, `cot`
  - [ ] All main inverse trig functions: `asin`, `acos`, `atan`, `acsc`, `asec`, `acot`
- [ ] Improve code for functions
  - [ ] Refactor into separate file, maybe use classes and inheritance?
  - [ ] Add support for user-defined functions
  - [ ] Add name aliases for functions (e.g. `arcsin` for `asin`)
- [ ] Support decimals and other number representations
  - [ ] When parsing, decide between subtract and negative number so we don't need to use the `−` character
- [ ] Improve simplification
  - [ ] Add trig identities
- [ ] Add exponentiation support
  - [ ] Add support for logarithms (maybe not a built-in function? Would need support for multiple arguments)
- [X] Internally represent numbers as rationals to avoid floating-point errors and allow exact simplification in more cases
- [ ] Add support for symbolic constants like `pi`, `e`, etc. (probably regular variables with special names?)
- [X] Add support for non-primary variables of differentiation so we can take partial derivatives
- [ ] Store and calculate function domains and ranges
- [ ] Add the ability to solve equations for specific variables symbolically
- [ ] Add the ability to solve systems of equations symbolically
- [ ] Add support for integrals (probably not going to happen)
- [ ] Add support for limits (probably not going to happen)
- [ ] Add support for complex numbers (probably not going to happen)

# Note
I'm not certain the simplification or differentiation are perfect, so I wouldn't trust this for anything important yet. I've extensively compared its outputs to those of Wolfram|Alpha, though, and it seems to be correct.