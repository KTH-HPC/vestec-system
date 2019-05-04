import json
from mproxy.api.serialisation import JsonObjHelper, JsonSerialisable

def roundtrip(obj):
    j = JsonObjHelper.py2j(obj)
    s = json.dumps(j)
    restored = json.loads(s)
    return JsonObjHelper.j2py(type(obj), restored)

def assert_roundtrip(orig):
    restored = roundtrip(orig)
    assert orig == restored
    return

def test_simple():
    assert_roundtrip('hello')
    assert_roundtrip(1)
    assert_roundtrip(3.14)
    assert_roundtrip(True)
    assert_roundtrip(None)

def test_simple_container():
    assert_roundtrip([None, False, 1, 2.0])
    assert_roundtrip({
        'key': 'value',
        'integer': 99,
        'bool': True
        })

class SimpleObject(JsonSerialisable):
    _JSON_ATTRS = ('foo', 'bar')
    def __init__(self, foo=None, bar=None):
        self.foo = 0 if foo is None else foo
        self.bar = '' if bar is None else bar
    def __eq__(self, other):
        return (self.foo == other.foo) and (self.bar == other.bar)

def test_simpleobject():
    assert_roundtrip(SimpleObject(2))

class ComplexObject(JsonSerialisable):
    _JSON_ATTRS = ('name', 'children', 'binary')
    def __init__(self, name='bar', children=(), binary=b''):
        self.name = name
        self.children = children
        self.binary = binary

    @classmethod
    def _from_json(cls, obj):
        name = obj.pop('name')
        # tup = JsonObjHelper.j2py(tuple, obj.pop('tup'))
        children = tuple(JsonObjHelper.j2py(cls, o) for o in obj.pop('children'))
        binary = JsonObjHelper.j2py(bytes, obj.pop('binary'))
        return cls(name, children, binary)

    def __eq__(self, other):
        return (self.name == other.name) and (self.children == other.children) and (self.binary == other.binary)

def test_complex():
    assert_roundtrip(ComplexObject('This is a string', binary=b'Complex binary data'))