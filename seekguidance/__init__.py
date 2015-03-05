import collections
import json
import os
import random
import string

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
    
Production = collections.namedtuple("Production", ["text", "fields", "weight"])
Rule = collections.namedtuple("Rule", ["productions", "weight"])

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

def from_grammar(grammar, weights = {}):
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
    
    _generate_sentence.grammar = w_grammar
    return _generate_sentence

def from_file(path, weights = {}):
    with open(path, "rb") as file:
        grammar = json.load(file)
    
    return from_grammar(grammar, weights)

Preset = collections.namedtuple("Preset", ["initial_symbol", "weights"])

PRESET_DIR = os.path.join(os.path.dirname(__file__), "presets")
PRESETS = {
    "darksouls": Preset(u"message", {}),
    "darksouls2": Preset(u"message", {u"message": [7, 1, 1, 1, 1, 1, 1, 1]}),
    "darksouls2patch": Preset(u"message", {u"message": [7, 1, 1, 1, 1, 1, 1, 1]}),
    "demonssouls": Preset(u"message", {u"message": [2, 2, 2, 2, 2, 1]})
}

def from_preset(name):
    preset = PRESETS[name]
    path = os.path.join(PRESET_DIR, name + ".json")
    
    _generate = from_file(path, preset.weights)
    _preset_generate = lambda: _generate(preset.initial_symbol)
    _preset_generate.grammar = _generate.grammar
    
    return _preset_generate
