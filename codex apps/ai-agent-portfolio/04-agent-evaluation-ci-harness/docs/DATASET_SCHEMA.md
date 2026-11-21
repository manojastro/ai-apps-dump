# Golden dataset schema

Datasets import as JSON Lines, one case per line.

```json
{"id":"vpn-001","user_input":"VPN will not connect","expected_answer":"Reconnect the VPN profile.","expected_properties":["grounded","cited"],"expected_sources":["KB-VPN"],"tags":["vpn"],"difficulty":"common","category":"vpn","answerable":true,"allowed_tools":["search_knowledge"],"forbidden_tools":["shell"],"metadata":{"owner":"support"}}
```

`id` and `user_input` are required. Source IDs must be stable canonical identifiers. `answerable=false` changes scoring toward abstention and no unsupported citations. Tool fields drive hard safety validation. Version imported datasets rather than mutating historical run inputs.

The demo generator always produces exactly 120 common, 50 edge, and 30 unanswerable cases (60/25/15 percent).

