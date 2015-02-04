import json
import os
import random
import re
import sys

class Leaf(object):
    def __init__(self, text):
        self.text = text
        self.size = 1

class Sequence(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self.size = reduce(lambda s, n: s * n.size, self.nodes, 1)

class Branch(object):
    def __init__(self, name, children = ()):
        self.name = name
        self.children = []
        self.children.extend(children)        
        self.size = sum(map(lambda node: node.size, self.children))

def build_grammar_tree(grammar_dict, initial, custom_sizes = {}):
    expansions = {}
    
    def _is_nonempty(node):
        return isinstance(node, Branch) or bool(node.text)
    
    def _expand(symbol):
        if symbol not in expansions:
            productions = grammar_dict[symbol]
            children = []
            for production in productions:
                production_parts = filter(_is_nonempty, _split(symbol, production))
                if len(production_parts) == 0:
                    child = Leaf(u"")
                elif len(production_parts) == 1:
                    child = production_parts[0]
                else:
                    child = Sequence(production_parts)
                    
                children.append(child)
            
            if len(children) == 0:
                node = Leaf(u"")
            elif len(children) == 1:
                node = children[0]
            else:
                node = Branch(symbol, children)
                        
            expansions[symbol] = node
            
        return expansions[symbol]

    def _split(symbol, production):
        expand = False
        escape = False
        seq = u""
        for char in production:
            if escape:
                seq += char
                escape = False
            elif expand:
                if char == u"}":
                    node = _expand(seq)
                    yield node
                    expand = False
                    seq = u""
                elif char == u"\\":
                    escape = True
                else:
                    seq += char
            elif char == u"{":
                if seq:
                    node = Leaf(seq)
                    yield node
                expand = True
                seq = u""
            elif char == u"\\":
                escape = True
            else:
                seq += char
        
        if expand or escape:
            raise ValueError("parse error")
                
        if seq:
            node = Leaf(seq)
            yield node
    
    return _expand(initial)

def generate_sentence(node, weights = {}):
    if isinstance(node, Leaf):
        return node.text
    elif isinstance(node, Sequence):
        return u"".join(map(generate_sentence, node.nodes))
    else:
        child_count = len(node.children)
        
        node_weights = weights.get(node.name, None)
        if node_weights != None:
            if len(node_weights) != child_count:
                raise ValueError("weights length mismatch")
            
            size = sum(node_weights)
            child_size = lambda i: node_weights[i]
        else:
            size = node.size
            child_size = lambda i: node.children[i].size
        
        threshold = random.randrange(size)
        total = 0
        for i in xrange(child_count):
            total += child_size(i)
            if total > threshold:
                chosen_child = node.children[i]
                break
        
        return generate_sentence(chosen_child)

class GrammarSpec(object):
    def __init__(self, initial_symbol, weights = {}):
        self.initial_symbol = initial_symbol
        self.weights = weights

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
        grammar_dict = json.load(file)

    g = build_grammar_tree(grammar_dict, grammar_spec.initial_symbol)
    print generate_sentence(g, grammar_spec.weights)    

if __name__ == "__main__":
    main()
