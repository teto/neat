# NEAT Policies

Recall that a candidate is an object containing an arbitrary number of NEAT properties.

NEAT policies are objects which append/update NEAT properties to connection *candidates* in order to enforce a specific behaviour. Each policy contains two main keys: `match` and `properties`, as well as a number of meta attributes such as `uid`, `priority` or `description`. Policies are stored in a PIB repository.

The following table provides a description of the policy object keys:

| Key | Description |
|-----|-------------|
| `uid` | unique identifier for the policy |
| `priority` | policies with the lowest priority are applied first (default: 0.0) |
| `description` | human readable description (default: '') |
| `policy_type` | either `policy` (default) or `profile` |
| `replace_matched` | if `true` the matched properties will be removed from the candidate prior to applying the policy properties. (default: false) |
| `match` | properties that trigger the policy |
| `properties` | policy properties which will update or be appended to the candidate |

If a key is omitted the default value will be used.

+ The value of the `match` key is an object which contains a set of properties that trigger the policy. A policy is triggered only if *all* of the match properties are contained within the input candidate, i.e., the set of candidate properties is a superset of the set of match properties. If the the match key is empty or missing the policy will match *any* candidate.

+ The value of the `properties` key is an object which contains a set of properties which should be appended to the connection candidate, *if* the policy is triggered. To this end, the candidate properties are updated/appended by the *policy properties* specified in the properties object. Specifically, a candidate property will be *updated* (see [NEAT operators](doc/NEAT_properties.md)) by a policy property if it has the same key. If a policy property's key is not already in the set of candidate properties the property will be appended to the set.

The NEAT Policy Manager uses JSON to encode policies. 

==WIP==

Subsequent policies will *overwrite* any perviously applied policy properties. Conflicting policies must be identified by the NEAT logic.