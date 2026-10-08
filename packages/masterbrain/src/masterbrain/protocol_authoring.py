"""Shared authoring policy; host permissions and execution remain host-owned."""

ASSIGNER_RUNTIME_POLICY = """
## Assigner runtime and file placement

When the host sets prefer_client_assigners=true, prefer client-side assigners for small, deterministic calculations over declared
Record inputs: arithmetic, ratios, unit conversions and explicit classifications.
Keep these in protocol.aimd using `assigner runtime=client` fences. Do not create
model.py or assigner.py just for a calculation expressible in this single file.
Use one named function per block, unique IDs and outputs, and no dependency cycles:

```assigner runtime=client
assigner(
  {mode: "auto", dependent_fields: ["length", "width"], assigned_fields: ["area"]},
  function calculate_area({length, width}) { return {area: length * width}; }
);
```

This is restricted synchronous JavaScript, NOT Python. Supported client modes are
auto, auto_first and manual. Return a plain object with exactly the declared outputs.
Declare every input/output using AIMD variables and constrain invalid denominators
with field metadata. Do not invent missing observations, replace missing values with
zero, invent scientific thresholds or silently coerce invalid inputs. Never use
network/file/DOM access, secrets, imports, async, Date, randomness, eval or Function.

Use server-side Python for external APIs, file/data access, scientific libraries,
heavy computation, secrets, or calculations requiring trusted server verification.
Use a plain `assigner` fence for Python in a single-file Protocol, or the existing
assigner.py in a multi-file workspace; never duplicate the same server implementation
in both places. Client and server assigners must not write the same output field.
Python uses module-level @assigner functions returning AssignerResult, not JavaScript.
Browser calculations are convenience, not an authorization or scientific integrity
boundary. API/CSV imports must supply derived values; do not claim browser code runs
on headless imports. Respect a host's explicit server-only runtime constraint.
Preserve existing runtime choices when editing unless the requested change requires
migration. Never put JavaScript in assigner.py.
If prefer_client_assigners is false or absent, use server Python for NEW calculations
even where the examples below show client syntax. Preserve existing client blocks.
""".strip()


def assigner_host_context(prefer_client_assigners: bool) -> str:
    return "Host capability: prefer_client_assigners=" + str(prefer_client_assigners).lower()
