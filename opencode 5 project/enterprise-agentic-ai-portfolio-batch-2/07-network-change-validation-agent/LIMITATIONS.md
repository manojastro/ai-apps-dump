# LIMITATIONS

## Simulation Fidelity

- The twin is a semantic model, not packet-level emulation. ARP/ND, DHCP,
  spanning-tree convergence, ECMP hashing and QoS are not modeled.
- Stateful firewall inspection is abstracted: rule ports match destination OR
  source port rather than tracking connection state.
- OSPF is link-state SPF with directed interface costs; LSA flooding, areas
  beyond type-0, authentication and adjacency timers are not modeled.
- BGP is modeled as neighbor-advertised prefixes with eBGP distance 20;
  path attributes (local-pref, AS-path prepending), route reflection and
  policies beyond advertisement on/off are out of scope.
- L2 switches are transparent hops; the path device sequence shows routed hops.
- Reachability probes use representative hosts per subnet, not every host.

## Scope

- One lab topology ships with the product; custom twins can be posted via
  /network/snapshot but multi-topology management is minimal.
- Config grammar covers the documented command subset (interfaces, ACLs,
  static/OSPF/BGP basics, gateway, VLAN access ports, firewall policy lines);
  unrecognized lines are surfaced as no-op ops rather than guessed at.
- Single-tenant, single-user model: no authn/authz layer in this slice.

## Engineering Constraints

- SQLite WAL is single-writer; heavy concurrent API usage should move to
  Postgres. Mutating tool calls commit before executing to avoid lock contention.
- Validation duration scales with probe count (168 flows x forward+reverse);
  large topologies need probe selection or parallelism.
- Remediation inversion covers the modeled op set; deleting an entire ACL
  object is detected but not auto-remediable (rule-level restores only).

## Detection Boundaries

- Ground truth matching requires expected regression *kinds* to be a subset of
  detected kinds; extra findings are tolerated by design but would inflate
  noise metrics in larger catalogs.
- Intents are evaluated between representative endpoints; a change that breaks
  reachability for a non-representative host within a subnet would not be caught
  unless it changes path semantics for the representatives.
