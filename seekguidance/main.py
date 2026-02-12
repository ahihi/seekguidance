#!/usr/bin/env python
import os
import sys

import seekguidance

def main():
    if len(sys.argv) < 2:
        print("Usage: {prog} {grammars}".format(
            prog = os.path.basename(sys.argv[0]),
            grammars = "|".join(sorted(seekguidance.PRESETS.keys()))
        ), file=sys.stderr)
        sys.exit(1)
    
    preset = sys.argv[1]
    
    generate_sentence = seekguidance.from_preset(preset)
    print(generate_sentence())

if __name__ == "__main__":
    main()
