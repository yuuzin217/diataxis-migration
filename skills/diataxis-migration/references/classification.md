# Classification guidance

Diátaxis organizes technical documentation around four different reader needs. Use the primary need served by a passage or page to classify it; titles and directory names are clues, not proof. The framework guides improvement from the content outward. It does not require four populated sections, and application source code is not reorganized into four categories.

| Category | Reader need | Typical content | Check |
| --- | --- | --- | --- |
| Tutorial | Learn by doing | A guided, supported learning experience with a clear beginning and outcome | Does the reader gain a skill or understanding by following it? |
| How-to | Complete a task | Focused procedures for a reader who already has some context | Does it help a reader solve a specific problem or reach a concrete goal? |
| Reference | Look up facts | API contracts, commands, configuration, schemas, constraints, and behavior | Is it structured for accurate lookup and grounded in current implementation? |
| Explanation | Understand context | Architecture, rationale, trade-offs, limitations, and adopted decisions | Does it help the reader understand why or how the system is shaped? |

An installation procedure is usually a how-to, not a tutorial. A list of commands or API fields is reference. An explanation of an architectural decision is explanation only when the decision was actually adopted. A single page can combine categories; split it only when the different needs are substantial enough to justify separate pages and the information can be kept coherent.

## Decide what to do

For each document, capture its path, current category, primary purpose, target category, decision, evidence, reason, and action. Use one of these decisions:

- `KEEP`: current placement and content serve the reader need.
- `MOVE`: placement is the main problem.
- `SPLIT`: substantial, distinct needs are mixed together.
- `MERGE`: competing documents duplicate the same canonical information.
- `REWRITE`: claims or structure need correction.
- `CROSS-LINK`: retain a short useful summary and point to its canonical source.
- `ARCHIVE / DEPRECATE`: obsolete material needs an explicit status and safe handling.
- `FOLLOW-UP`: the issue needs an implementation change or evidence unavailable now.

Do not create a tutorial merely to fill a category. Do not remove a concise summary solely because it overlaps with a canonical page; remove or link redundant independent specifications that can drift. Prefer small, evidence-backed changes and update navigation when a document moves.

## Official guidance

- [Diátaxis overview](https://diataxis.fr/) describes the four needs and the framework's role in content, style, and architecture.
- [Diátaxis as a guide to work](https://diataxis.fr/how-to-use-diataxis/) says to use the framework as a guide rather than a top-down plan, avoid empty category structures, and improve documentation in small steps.
- [Tutorials](https://diataxis.fr/tutorials/), [How-to guides](https://diataxis.fr/how-to-guides/), [Reference](https://diataxis.fr/reference/), and [Explanation](https://diataxis.fr/explanation/) describe each form in detail.

These links point to the framework authors' published guidance. Apply it alongside the user's explicit scope and the evidence in the target repository.
