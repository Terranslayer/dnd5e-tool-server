# D&D 5e Tool Server

A Python project that connects a language model to Dungeons & Dragons rules, reference data, and saved campaign notes through the Model Context Protocol (MCP).

The idea is simple: let the model narrate, and use Python for dice rolls, rule calculations, and state changes. The server exposes 27 tools. The core tools run locally without an API key.

## Try it

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --frozen
uv run --offline --no-sync python -B -m scripts.demo_offline
uv run --offline --no-sync pytest
```

The demo uses fixed dice inputs, looks up a Goblin and Fireball in the bundled reference data, then saves and reloads an encounter in a temporary folder. It prints JSON, including an attack total of **23 against AC 15**, **7 damage**, and an encounter budget of **300 adjusted XP**. It does not require a model or change your campaign notes.

See the [demo walkthrough](docs/offline-demo.md) for the inputs, expected output, and relevant source files.

## What it does

| Area | Examples |
| --- | --- |
| Dice and rules | Advantage, attacks, damage, spell save DCs |
| Encounters | XP budgets, difficulty, monsters by challenge rating |
| Reference lookup | Monsters, spells, conditions, rules, English/Chinese terms |
| Campaign state | Notes, initiative order, hit points, locations, quest flags |
| Optional search | Semantic search over module text using embeddings and LanceDB |

The reference data is the 2014 rules / SRD 5.1. Search requires an embedding API key; ordinary rules and exact lookups do not.

## Connect a client

Start the server from this repository's root:

```sh
uv run --no-sync python -m dnd5e_engine.server
```

Configure an MCP client to launch that command with this folder as its working directory. Some clients need an absolute executable path. The included `.mcp.json` is a configuration example; support for automatically reading it depends on the client.

[Example workflows](examples/workflows/README.md) cover preparation, module parsing, and running a session. They are optional instructions to load into a compatible client, and are not automatically installed.

For semantic search, copy `.env.example` to `.env`, set `OPENAI_EMBEDDING_API_KEY`, and run `uv run python scripts/build_index.py`. Keep personal notes and credentials outside version control.

## How it is organized

```text
dnd5e_engine/       MCP wrappers, rules, lookup, retrieval, and state services
data/srd_2014/     Bundled reference data and attribution
vault/             Markdown templates and empty campaign folders
examples/workflows/ Optional client workflows
scripts/           Offline demo and reference/index loaders
tests/             Rules, lookup, state, and integration checks
```

The [design notes](docs/design.md) explain why rules, narration, and storage are separate.

## Limits and next steps

This is a local personal project. The tests cover tool behavior; they do not measure whether a model consistently selects the right tool. Campaign filtering is a search option, not a multi-user authorization system. A useful next step is a fixed set of model-only and tool-assisted scenarios, including wrong arguments and missing rules.

## License

Code: [MIT](LICENSE). SRD 5.1: © Wizards of the Coast, used under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The bundled JSON comes from [5e-bits/5e-database](https://github.com/5e-bits/5e-database); see [attribution](data/srd_2014/ATTRIBUTION.txt).
