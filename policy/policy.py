import json
import logging
import operator
import os
import unittest
import copy
import numbers

logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.DEBUG)

POLICY_DIR = "pib/examples/"


class NEATPropertyError(Exception):
    pass


class NEATProperty(object):
    """Properties are (key,value) tuples"""

    IMMUTABLE = 2
    REQUESTED = 1
    INFORMATIONAL = 0

    def __init__(self, prop, level=REQUESTED, score=0.0):
        self.key, self._value = prop
        if isinstance(self.value, (tuple, list)):
            self.value = tuple((float(i) for i in self.value))
            if self.value[0] > self.value[1]:
                raise IndexError("Invalid property range")
        self.level = level
        self.score = score
        # TODO experimental meta data
        # specify relationship type between key and value, e.g., using some comparison operator
        self.relation = '=='  # e.g., 'lt', 'gt', 'ge', '==', 'range', ??
        # mark if property has been updated during a lookup
        self.evaluated = False
        # attach more weight to property score
        self.weight = 1.0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        old_value = self._value
        self._value = value
        if isinstance(old_value, (tuple, numbers.Number)) and isinstance(old_value, (tuple, numbers.Number)):
            new_value = self._range_overlap(old_value)
            if new_value:
                self._value = new_value
        print(self._value)

    @property
    def required(self):
        return self.level == NEATProperty.IMMUTABLE

    @property
    def requested(self):
        return self.level == NEATProperty.REQUESTED

    @property
    def informational(self):
        return self.level == NEATProperty.INFORMATIONAL

    @property
    def property(self):
        return self.key, self.value

    def items(self):
        return self.property

    def __iter__(self):
        for p in self.property:
            yield p

    def __eq__(self, other):
        """Return true if a single value is in range, or if two ranges have an overlapping region."""
        assert isinstance(other, NEATProperty)

        if not isinstance(other.value, tuple) and not isinstance(self.value, tuple):
            return (self.key, self.value) == (other.key, other.value)

        if not (self.key == other.key):
            logging.debug("Property key mismatch")
            return False

        return self._range_overlap(other.value)

    def __hash__(self):
        return hash(self.property)

    def _range_overlap(self, other_range):
        self_range = self.value

        # create a tuple if one of the ranges is a single numerical value
        if isinstance(other_range, numbers.Number):
            other_range = other_range, other_range
        if isinstance(self_range, numbers.Number):
            self_range = self_range, self_range

        # check if ranges have an overlapping region
        overlap = other_range[0] <= self_range[1] and other_range[1] >= self_range[0]
        if not overlap:
            return False
        else:
            # return actual range
            overlap_range = max(other_range[0], self_range[0]), min(other_range[1], self_range[1])
            if overlap_range[0] == overlap_range[1]:
                return overlap_range[0]
            else:
                return overlap_range

    def update(self, other):
        """ Update the current property value with a different one and update the score."""
        assert isinstance(other, NEATProperty)

        if not other.key == self.key:
            logging.debug("Property key mismatch")
            return

        self.evaluated = True

        if other.level >= self.level:
            property_changed = not self == other

            self.value = other.value
            self.level = other.level
            if property_changed:
                self.score += -(1.0 + self.level)
                logging.debug("property %s updated to %s." % (self.key, self.value))
            else:
                self.score += +(1.0 + self.level)
                logging.debug("property %s is already %s" % (self.key, self.value))
        else:
            self.score = -9999.0  # FIXME
            logging.debug("property %s is _immutable_: won't update." % (self.key))
            raise NEATPropertyError('Immutable property')

        logging.debug("updated %s" % (self))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if isinstance(self.value, tuple):
            val_str = '%s-%s' % self.value
        else:
            val_str = str(self._value)

        keyval_str = '%s|%s' % (self.key, val_str)
        if self.score > 0.0:
            score_str = '%+.1f' % self.score
        else:
            score_str = ''

        if self.level == NEATProperty.IMMUTABLE:
            return '[%s]%s' % (keyval_str, score_str)
        elif self.level == NEATProperty.REQUESTED:
            return '(%s)%s' % (keyval_str, score_str)
        elif self.level == NEATProperty.INFORMATIONAL:
            return '<%s>%s' % (keyval_str, score_str)
        else:
            return '?%s?%s' % (keyval_str, score_str)


class PropertyDict(dict):
    """Convenience class for storing NEATProperties."""

    def __init__(self, iterable={}):
        self.update(iterable, level=NEATProperty.REQUESTED)

    def __getitem__(self, item):
        if isinstance(item, NEATProperty):
            key = item.key
        else:
            key = item
        return super().__getitem__(key)

    def update(self, iterable, level=NEATProperty.REQUESTED):
        if isinstance(iterable, dict):
            for k, v in iterable.items():
                self.insert(NEATProperty((k, v), level=level))
        else:
            for i in iterable:
                if isinstance(i, NEATProperty):
                    self.insert(i)
                else:
                    k, v, *l = i
                    if l:
                        level = l[0]
                        # TODO initialize score as well
                    self.insert(NEATProperty((k, v), level=level))

    def intersection(self, other):
        """Return a new PropertyDict containing the intersection of two objects."""
        properties = PropertyDict()
        properties.update({p.key: p.value for k, p in self.items() & other.items()})
        return properties

    def insert(self, property):  # TODO
        """
        Insert a new NEATProperty tuple into the dict or update an existing one.

        :rtype: None
        """
        if not isinstance(property, NEATProperty):
            logging.warning("only NEATProperty objects may be inserted to PropertyDict.")
            return

        if property.key in self.keys():
            self[property.key].update(property)
        else:
            self.__setitem__(property.key, property)

    def __repr__(self):
        return '{' + ', '.join([str(i) for i in self.values()]) + '}'


class NEATPolicy(object):
    """NEAT policy representation"""

    def __init__(self, policy_json={}, name='NA'):
        # set default values
        self.idx = id(self)
        self.name = name
        for k, v in policy_json.items():
            if isinstance(v, str):
                setattr(self, k, v)

        self.priority = int(policy_json.get('priority', 0))  # TODO not sure if we need priorities

        self.match = PropertyDict()
        self.properties = PropertyDict()

        match = policy_json.get('match', {})
        for k, v in match.get('informational', {}).items():
            self.match[k] = NEATProperty((k, v), level=NEATProperty.INFORMATIONAL)
        for k, v in match.get('requested', {}).items():
            self.match[k] = NEATProperty((k, v), level=NEATProperty.REQUESTED)
        for k, v in match.get('immutable', {}).items():
            self.match[k] = NEATProperty((k, v), level=NEATProperty.IMMUTABLE)

        properties = policy_json.get('properties', {})
        for k, v in properties.get('informational', {}).items():
            self.properties[k] = NEATProperty((k, v), level=NEATProperty.INFORMATIONAL)
        for k, v in properties.get('requested', {}).items():
            self.properties[k] = NEATProperty((k, v), level=NEATProperty.REQUESTED)
        for k, v in properties.get('immutable', {}).items():
            self.properties[k] = NEATProperty((k, v), level=NEATProperty.IMMUTABLE)

    def match_len(self):
        """Use the number of match elements to sort the entries in the PIB.
        Entries with the smallest number of elements are matched first."""
        return len(self.match)

    def compare(self, properties, strict=True):
        """Check if the match properties are completely covered by the properties of a query.

        If strict flag is set match only properties with levels that are higher or equal to the level
        of the corresponding match property.
        """

        # always return True if the match field is empty (wildcard)
        if not self.match:
            return True

        # import code; code.interact(local=locals()) # XXX

        # find intersection
        matching_props = self.match.items() & properties.items()
        if strict:
            # ignore properties with a lower level than the associated match property
            return bool({k for k, v in matching_props if properties[k].level >= self.match[k].level})
        else:
            return bool(matching_props)

    def apply(self, properties: PropertyDict):
        """Apply policy properties to a set of candidate properties."""
        for p in self.properties.values():
            logging.info("applying property %s" % p)
            properties.insert(p)

    def __str__(self):
        return "POLICY %s: %s  ==>  %s" % (self.name, self.match, self.properties)

    def __repr__(self):
        return repr({a: getattr(self, a) for a in ['name', 'match', 'properties']})


class NEATCandidate(object):
    """Neat candidate objects store a list of properties for potential NEAT connections.
    They are created after a CIB lookup.

      NEATCandidate.cib: contains the matched cib entry
      NEATCandidate.policies: contains a list of applied policies
    """

    def __init__(self, properties=None):
        # list to store policies applied to the candidate
        self.policies = set()
        self.properties = PropertyDict()
        self.invalid = False

        if properties:
            self.properties = copy.deepcopy(properties)
            # for property in properties.values():
            #    self.properties.insert(property)

    def update(self, properties):
        """Update candidate properties from a iterable containing (key,value) tuples."""
        # TODO REMOVE
        for k, v in properties:
            self.add(NEATProperty((k, v)))

    def add(self, property):
        """Add single property to the candidate.properties list"""
        # TODO REMOVE
        self.properties.insert(property)

    @property
    def score(self):
        return sum(i.score for i in self.properties.values())

    @property
    def policy_properties(self):
        """This are the properties appended during the PIB lookup"""
        a = {}
        for p in self.policies:
            # TODO check for contradicting policies!
            a.update(p.optional)
        return a

    def __repr__(self):
        # return "<%s>" % ",".join([a+': '+repr(getattr(self,a)) for a in dir(self) if not a.startswith('__')])
        return 'properties: ' + str(self.properties) + ', applied policies: ' + str(self.policies)


from collections import namedtuple

Propertylevel = namedtuple("PropertyType", "immutable requested informational")


class NEATRequest(object):
    """NEAT query"""

    def __init__(self, requested={}, immutable={}, informational={}):
        properties = PropertyDict()
        for i in immutable.items():
            properties.insert(NEATProperty(i, level=NEATProperty.IMMUTABLE))
        for i in requested.items():
            properties.insert(NEATProperty(i, level=NEATProperty.REQUESTED))
        for i in informational.items():
            properties.insert(NEATProperty(i, level=NEATProperty.INFORMATIONAL))

        # super(NEATRequest, self).__init__(properties)
        self.properties = properties

        # Each NEATRequest contains a list of NEATCandidate objects
        self.candidates = []
        self.cib = None

        # code.interact(local=locals())

    def __repr__(self):
        return '<NEATRequest: %d candidates, %d properties>' % (len(self.candidates), len(self.properties))

    def dump(self):
        print(self.properties)
        print('=== candidates ===')
        for c in self.candidates:
            print(c)
        print('=== candidates ===')


class PIB(list):
    def __init__(self):
        super().__init__()
        self.policies = self
        self.index = {}

    def load_policies(self, policy_dir=POLICY_DIR):
        """Load all policies in policy directory."""
        for filename in os.listdir(policy_dir):
            if filename.endswith(".policy"):
                print('loading policy %s' % filename)
                p = self.load_policy(policy_dir + filename)
                self.register(p)

    def load_policy(self, filename):
        """Read and decode a .policy JSON file and return a NEATPolicy object."""
        try:
            policy_file = open(filename, 'r')
            policy = json.load(policy_file)
        except OSError as e:
            logging.error('Policy ' + filename + ' not found.')
            return
        except json.decoder.JSONDecodeError as e:
            logging.error('Error parsing policy file ' + filename)
            print(e)
            return
        p = NEATPolicy(policy)
        return p

    def register(self, policy):
        """Register new policy

        Policies are ordered
        """
        # check for existing policies with identical match properties
        if policy.match in [p.match for p in self.policies]:
            logging.warning("Policy match fields already registered. Skipping policy %s" % (policy.name))
            return
        # TODO check for overlaps and split
        self.policies.append(policy)
        # TODO sort on the fly
        self.policies.sort(key=operator.methodcaller('match_len'))
        self.index[policy.idx] = policy

    def lookup_candidates(self, candidates):
        # TODO
        pass

    def lookup_all(self, candidates):
        """ lookup all candidates in list """
        for candidate in candidates:
            try:
                self.lookup(candidate, apply=True)
            except NEATPropertyError:
                candidate.invalid = True
                i = candidates.index(candidate)
                print('Candidate %d is invalidated due to policy' % i)
        for candidate in candidates:
            if candidate.invalid:
                candidates.remove(candidate)

    def lookup(self, candidate: NEATCandidate, apply=False):
        """ Look through all installed policies to find the ones which match the properties of the given candidate.
        If apply is set to True append the matched policy properties.  """

        assert isinstance(candidate, NEATCandidate)
        logging.info("matching policies for current candidate:")
        for p in self.policies:
            if p.compare(candidate.properties):
                logging.info(p)
                if apply:
                    p.apply(candidate.properties)
                    candidate.policies.add(p.idx)
                else:
                    print(p.idx)

    def dump(self):
        s = "===== PIB START =====\n"
        for p in self.policies:
            s += str(p) + '\n'
        s += "===== PIB END ====="
        print(s)

    @property
    def matches(self):
        """Return the match fields of all installed policies"""
        return [p.match for p in self.policies]


class PropertyTests(unittest.TestCase):
    # TODO
    def test_property_logic(self):
        np2 = NEATProperty(('foo', 'bar2'), level=NEATProperty.IMMUTABLE)
        np1 = NEATProperty(('foo', 'bar1'), level=NEATProperty.REQUESTED)
        np0 = NEATProperty(('foo', 'bar0'), level=NEATProperty.INFORMATIONAL)

        # self.assertEqual(numeral, result)
        # unittest.main()


if __name__ == "__main__":
    import code

    npr1 = NEATProperty(('fu', (10, 20)))
    npr2 = NEATProperty(('fu', (15, 30)))
    npr3 = NEATProperty(('fu', 13))
    npr2._range_overlap(npr1.value)

    np = NEATProperty(('foo', 'bar'))
    pd = PropertyDict()
    pd.insert(np)

    nc = NEATCandidate()
    nc.add(np)
    nc.add(NEATProperty(('foo2', 'bar2')))

    # p = NEATPolicy({"name":"TCP","match":{"TCP":True},"optional":{"TCP_type":"cubic"},"required":{"wired_interface":True}})


    A = {"name": "A", "description": "bulk file transfer", "priority": "0",
         "match": {
             "immutable": {},
             "requested": {"is_wired_interface": True, "interface_speed_ge": 1000},
             "informational": {}},
         "properties": {
             "immutable": {"MTU": "9600"},
             "requested": {"TCP_CC": "LBE"},
             "informational": {}}}
    C = {"name": "C", "description": "foo and bar", "priority": "0",
         "match": {"requested": {'foo': 'bar'}},
         "properties": {"immutable": {'foo3': 'bar3'}}}

    p1 = NEATPolicy(A)
    p2 = NEATPolicy(C)

    #    if p2.compare(nc.properties):
    #        p2.apply(nc.properties)

    query_requested = {"TCP": True, "address": "10.10.1.1"}
    query_immutable = {"MTU": 9600, "is_wired_interface": True}

    q = NEATRequest(query_requested, query_immutable)

    pib = PIB()
    pib.load_policies()
    pib.register(p1)
    pib.register(p2)

    pib.lookup(nc, apply=False)
    # q.policies.append(p)




    code.interact(local=locals())
