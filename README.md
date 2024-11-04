# TI-NSpire Python CAS

A simple Python program I've been developing on my TI-NSpire CX II calculator to replicate the abilities of the CAS software. It's a work in progress, and it will probably never get very good, but it can take simple derivatives and simplify expressions in some ways.

It consists of a simple tokenizer, parser, and evaluator with support for arithmetic, variables, and built-in functions (currently only `sin` and `cos`). For example, it can parse, evaluate, take the derivative of, and simplify something like `2*cos(5 + x*2) + 6*x*y`.

The simplification is relatively basic; it supports constant folding, basic identities (e.g. `0*x = 0`, `1*x = x`, `x + 0 = x`, etc.), associative expression factoring (e.g. `2*x*y + 4*x*x*y` -> `2*x*y*(1 + 2*x)`), and some simple term rewriting (e.g. `x*y/x/x*y` -> `y*y/x`).

Most of the code in this repository is written on my calculator and exported to my computer, but I'm trying to avoid TI-specific Python modules to make it portable.

The code isn't structured very well, but it's mostly me messing around, so I'm not super worried about making a robust codebase.