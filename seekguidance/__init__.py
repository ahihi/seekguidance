import collections
import json
import os
import random
import re
import string

# TODO: support backrefs when generating

backref_re = re.compile(r"^\$([0-9]+)$")

def parse_backref(symbol):
    m = backref_re.match(symbol)
    return int(m.group(1)) if m else None

def is_backref(symbol):
    return backref_re.match(symbol) is not None

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
            if format_proc is not None:
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
        if is_backref(symbol):
            weight = 1
        elif symbol not in w_grammar:
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
        for i in range(production_count):
            accum_weight += production_weight(i)
            if accum_weight > threshold:
                production = rule.productions[i]
                break
        
        assert production is not None

        expanded = []
        def _make_expand(field):
            i = parse_backref(field)
            if i is not None:
                def _refer():
                    return expanded[i-1]
                return _refer
            else:
                def _expand():
                    sentence = _generate_sentence(field)
                    expanded.append(sentence)
                    return sentence
                return _expand
            
        expansions = [(field, _make_expand(field)) for field in production.fields]
        expansions_dict = {k: v for k, v in expansions}
        return gf.format(production.text, **expansions_dict)
    
    _generate_sentence.grammar = w_grammar
    return _generate_sentence

def from_file(path, weights = {}):
    with open(path, "rb") as file:
        grammar = json.load(file)
    
    return from_grammar(grammar, weights)

Preset = collections.namedtuple("Preset", ["initial_symbol", "weights"])

PRESET_DIR = os.path.join(os.path.dirname(__file__), "presets")
PRESETS = {
    "darksouls": Preset("message", {}),
    "darksouls2": Preset("message", {"message": [7, 1, 1, 1, 1, 1, 1, 1]}),
    "darksouls2patch": Preset("message", {"message": [7, 1, 1, 1, 1, 1, 1, 1]}),
    "darksouls3": Preset("message", {"message": [1, 1]}),
    "demonssouls": Preset("message", {"message": [2, 2, 2, 2, 2, 1]}),
    "bloodborne": Preset("message", {}),
    "eldenring": Preset("message", {"message": [1, 1]}),
    "lanternrite": Preset("message", {}),
}

def from_preset(name):
    preset = PRESETS[name]
    path = os.path.join(PRESET_DIR, name + ".json")
    
    _generate = from_file(path, preset.weights)
    _preset_generate = lambda: _generate(preset.initial_symbol)
    _preset_generate.grammar = _generate.grammar
    
    return _preset_generate
