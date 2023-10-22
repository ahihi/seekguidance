# seekguidance

## requirements

python 3.7 or later

## installation

in the repository root directory:

```
$ pip install .
```

## examples

```
$ seekguidance darksouls
Imminent elation…
```

```
$ seekguidance darksouls2
Be wary of two-handing but Try sorcery
```

```
$ seekguidance demonssouls
Don't bother with curved swords.
```

```
$ seekguidance bloodborne
treat Grand Cathedral with care
```

```
$ seekguidance darksouls3
Huh, it's a friendship… in short be wary of locking-on
```

```
$ seekguidance eldenring
Didn't expect sorcery…, turn back, O turn back
```

## usage as a library

import:

```python
import seekguidance
```

list available presets:

```python
print(seekguidance.PRESETS.keys())
```

generate messages:

```python
das_generate_message = seekguidance.from_preset("darksouls")

print(das_generate_message())
print(das_generate_message())
print(das_generate_message())
```
