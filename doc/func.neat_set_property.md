## neat_set_property
```c
neat_error_code neat_set_property(
    struct neat_ctx *ctx,
    struct neat_flow *flow,
    uint64_t inMask);
```
Set NEAT property mask.
See [Property](#properties) for details.

### Availabe properties
* NEAT_PROPERTY_OPTIONAL_SECURITY
* NEAT_PROPERTY_REQUIRED_SECURITY
* NEAT_PROPERTY_MESSAGE
* NEAT_PROPERTY_IPV4_REQUIRED          
* NEAT_PROPERTY_IPV4_BANNED               
* NEAT_PROPERTY_IPV6_REQUIRED               
* NEAT_PROPERTY_IPV6_BANNED                
* NEAT_PROPERTY_SCTP_REQUIRED               
* NEAT_PROPERTY_SCTP_BANNED                
* NEAT_PROPERTY_TCP_REQUIRED                
* NEAT_PROPERTY_TCP_BANNED               
* NEAT_PROPERTY_UDP_REQUIRED      
* NEAT_PROPERTY_UDP_BANNED          
* NEAT_PROPERTY_UDPLITE_REQUIRED         
* NEAT_PROPERTY_UDPLITE_BANNED         
* NEAT_PROPERTY_CONGESTION_CONTROL_REQUIRED
* NEAT_PROPERTY_CONGESTION_CONTROL_BANNED
* NEAT_PROPERTY_RETRANSMISSIONS_REQUIRED
* NEAT_PROPERTY_RETRANSMISSIONS_BANNED

### Example
```c
neat_get_property(ctx, flow, &prop);
prop |= NEAT_PROPERTY_OPTIONAL_SECURITY;
prop |= NEAT_PROPERTY_TCP_REQUIRED; /* FIXME: Remove this once HE works */
neat_set_property(ctx, flow, prop);
```