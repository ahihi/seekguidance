#!/usr/bin/env python
from collections import namedtuple
import json
import os
import random
import string
import sys

def on_first(f):
    def _apply(text):
        if text:
            return f(text[0]) + text[1:]
        else:
            return text
    
    return _apply

class GrammarFormatter(string.Formatter):    
    def get_value(self, key, args, kwargs):
        value = string.Formatter.get_value(self, key, args, kwargs)
        if hasattr(value, "__call__"):
            value = value()
        
        return value
    
    def format_field(self, value, format_spec):
        try:
            return string.Formatter.format_field(self, value, format_spec)
        except ValueError:
            uppercase = lambda s: s.upper()
            lowercase = lambda s: s.lower()
            format_specs = {
                "A": on_first(uppercase),
                "u": uppercase,
                "l": lowercase
            }
            format_proc = format_specs.get(format_spec, None)
            if format_proc != None:
                return format_proc(value)
            else:
                raise
    
Production = namedtuple("Production", ["text", "fields", "weight"])
Rule = namedtuple("Rule", ["productions", "weight"])

def get_format_fields(formatter, format):
    return [fld for lit, fld, fmt, cnv in formatter.parse(format) if fld != None]

def weigh_grammar(formatter, grammar):
    w_grammar = {}
    
    def _weigh(symbol):
        if symbol not in w_grammar:
            productions = grammar[symbol]
            weight = 0
            w_productions = []
            for production in productions:
                production_weight = 1
                fields = get_format_fields(formatter, production)
                for field in fields:
                    production_weight *= _weigh(field)
                w_productions.append(Production(production, fields, production_weight))
                weight += production_weight
            
            w_grammar[symbol] = Rule(w_productions, weight)
        else:
            weight = w_grammar[symbol].weight
        
        return weight
    
    for symbol in grammar:
        _weigh(symbol)
    
    return w_grammar

def new_generator(grammar, weights = {}):
    gf = GrammarFormatter()
    w_grammar = weigh_grammar(gf, grammar)
    
    def _generate_sentence(symbol):
        rule = w_grammar[symbol]
        production_count = len(rule.productions)
        
        symbol_weights = weights.get(symbol, None)
        if symbol_weights != None:
            if len(symbol_weights) != production_count:
                raise ValueError("weights length mismatch")
        
            total_weight = sum(symbol_weights)
            production_weight = lambda i: symbol_weights[i]
        else:
            total_weight = rule.weight
            production_weight = lambda i: rule.productions[i].weight
        
        threshold = random.randrange(total_weight)
        accum_weight = 0
        production = None
        for i in xrange(production_count):
            accum_weight += production_weight(i)
            if accum_weight > threshold:
                production = rule.productions[i]
                break
        
        assert production != None
        
        expansions = {field: lambda: _generate_sentence(field) for field in production.fields}
        return gf.format(production.text, **expansions)
    
    return _generate_sentence

GrammarSpec = namedtuple("GrammarSpec", ["initial_symbol", "weights"])

grammars = {
    "darksouls2": GrammarSpec(u"message", {u"message": [7, 1, 1, 1, 1, 1, 1, 1]})
}

def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, u"Usage: {prog} {grammars}".format(
            prog = os.path.basename(sys.argv[0]),
            grammars = u"|".join(sorted(grammars.keys()))
        )
        sys.exit(1)
    
    grammar_name = sys.argv[1]
    grammar_spec = grammars.get(grammar_name, None)
    
    if grammar_spec == None:
        print >> sys.stderr, u"Unknown grammar: \"{grammar\"".format(
            grammar = grammar_name
        )
        sys.exit(2)
        
    json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "grammars", "{grammar}.json".format(grammar = grammar_name))
    with open(json_path, "rb") as file:
        grammar = json.load(file)
        
    generate_sentence = new_generator(grammar, grammar_spec.weights)
    print generate_sentence(grammar_spec.initial_symbol)

if __name__ == "__main__":
    main()
