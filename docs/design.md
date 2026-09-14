# Design notes

## Keep rules separate from narration

`server.py` exposes MCP tools and delegates to ordinary Python services. Dice notation, attack resolution, spell arithmetic, and encounter tables can therefore be tested without a language model. Normal dice rolls are random; the offline example supplies fixed faces so its output is repeatable.

Exact lookups use the bundled SRD JSON and return a citation or a missing result. Semantic retrieval is a separate, optional path for prose. A search snippet should not override an exact rule value.

## Store campaign state in files

Notes use Markdown with YAML frontmatter. They can be inspected with a text editor or Obsidian. `StateService` handles hit points, turn order, and campaign flags; it resolves write destinations against its configured root. This keeps state outside the model's conversation context.

Plain files are convenient for one local campaign. Concurrent editing and authenticated access from several users would need a different storage and access design.

## Keep clients interchangeable

The Python server does not call a chat model. A compatible MCP client chooses and calls tools. The optional workflow documents describe that procedure; moving them into `examples/workflows` makes the examples independent of a particular client's configuration folder. Clients that support skill files can install the selected workflow using their own documented process.

## Tests to read first

- `tests/test_dice.py`: parsing and dice behavior.
- `tests/test_encounter.py`: encounter calculations.
- `tests/test_state.py`: persisted game state.
- `tests/test_demo_offline.py`: fixed calculations, state readback, and temporary-folder cleanup.

The offline example calls the underlying services. It does not test a live model choosing tools or the MCP transport.
