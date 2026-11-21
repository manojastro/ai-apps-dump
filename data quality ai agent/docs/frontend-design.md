# Investigation console design

The primary audience is an engineer investigating a pipeline failure. The workflow and rejected
attempt are the focal points. There is no marketing landing page.

- Palette: navy #142b43 navigation; slate #526579 text; paper #f4f7fa background; white #ffffff
  work surfaces; cobalt #315bea selected controls; red #b93939 rejected checks; green #15715a passed.
- Type: system Segoe UI for labels and prose; Cascadia Code / Consolas for evidence IDs and patches.
- Layout: a narrow navigation rail, incident table at left, spacious investigation workspace at right.
  A dependency graph shows five parallel branches. Attempts sit immediately below it. Evidence and
  verifier details are available in named tabs; approvals stay beside the selected incident.
- Alignment: left-aligned content, right-aligned numeric table data, no ornamental dashboards.
- Interaction: real scenario injection, search/filter, graph node inspection, validation expansion,
  artifact download, approval and rejection. Empty states instruct the user to inject an incident.

The first design pass used generic KPI cards. Revised to prioritize a single incident's execution
graph and loop result because those are the actual engineering story. Counts remain in a restrained
toolbar; the graph is the only visually prominent structural element.
