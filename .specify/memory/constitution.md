<!--
Sync Impact Report (temporary review material; remove before committing)
Version change: 1.0.0 -> 1.1.0 (additive engineering obligations)
Modified principles: I-IX retained unchanged; X-XIV added.
Added principles: HSV Segmentation Remains Core; Backward Compatibility;
  Explicit Configuration; Preserve the Existing Python Architecture;
  Acceptance Criteria for Every Feature.
Added sections: principle subsections X-XIV only.
Removed sections: none.
Follow-up TODOs: none.
Dependent templates and application files: unchanged.
-->
# Mini-Project-HSV-Segmentation Constitution

## Core Principles

### I. Algorithm Correctness and Clarity

Image processing algorithms MUST prioritize mathematically correct, explainable behavior.
Each core operation MUST document its inputs, outputs, assumptions, and relevant equations or
algorithm steps. Color spaces, channel order, numeric ranges, data types, and boundary behavior
MUST be explicit wherever they affect results. Optimizations MUST preserve validated behavior
and MUST NOT obscure the algorithm without documented justification.

### II. Modular Architecture

Code MUST be organized into cohesive modules with explicit responsibilities and interfaces.
Shared processing logic MUST have one authoritative implementation. Dependencies MUST follow
the separation of concerns in Principle III, and circular dependencies MUST NOT be introduced.
New abstractions MUST address an existing responsibility or duplication, rather than a
hypothetical future requirement.

### III. Separation of GUI, Processing, and File I/O

GUI code MUST handle interaction, parameter collection, and result presentation. Image
processing code MUST operate on in-memory image data and explicit parameters. File I/O code
MUST handle reading, writing, and file-related errors. Core processing modules MUST NOT import
GUI modules, open dialogs, or access files. GUI handlers MUST delegate algorithms and file
operations to their respective modules so that each concern can be understood and changed
independently.

### IV. Student-Friendly Simplicity and Maintainability

Implementations MUST use the simplest design that satisfies the documented academic
requirements. Contributors MUST prefer readable control flow and small, focused functions
over clever shortcuts or speculative abstraction. Dependencies and architectural additions
MUST have a documented purpose and a maintenance cost appropriate for university students.
Setup and execution instructions MUST be sufficient for another student to run the project.

### V. Consistent Naming and Clean Code

Modules, functions, variables, and parameters MUST use consistent naming conventions within
the chosen language. Names MUST communicate purpose; image parameters MUST identify units or
ranges when ambiguity could change results. Code MUST avoid duplicated logic, unexplained
constants, unused code, and comments that merely restate operations. Comments MUST explain
algorithmic reasoning, assumptions, or non-obvious decisions.

### VI. Independently Testable Core Functions

Every core image processing function MUST be callable and testable without starting a GUI,
opening a dialog, or reading or writing files. Inputs and configurable parameters MUST be
explicit, and outputs MUST be inspectable in memory. Functions MUST NOT depend on hidden GUI
state or mutable global configuration. Any randomness MUST be controllable through an explicit
seed or supplied generator so tests can reproduce results.

### VII. Automated Tests and Reproducible Experiments

Every core image processing function MUST have automated tests for normal behavior and
applicable boundary or invalid inputs. Tests MUST use known expected results, analytical
properties, or justified reference comparisons; visual inspection alone is insufficient.
Numerical comparisons MUST state tolerances where exact equality is inappropriate.
Experiments supporting reported results MUST record input data or how to obtain it, parameters,
dependency versions, execution steps, random seeds when applicable, and evaluation criteria.
Synthetic test images MUST be used where they make expected behavior easier to verify.

### VIII. Strict Academic Scope

Changes MUST support the documented image processing project and its academic evaluation.
Unnecessary frameworks, databases, backend services, and unrelated features MUST NOT be
introduced. A proposed dependency or feature MUST identify the requirement it satisfies and
explain why existing code or a simpler approach is insufficient. Infrastructure MUST remain
limited to what is necessary to run, test, and demonstrate the project.

### IX. Presentation-Ready Code and Documentation

Code and documentation MUST make the processing pipeline understandable in an academic
presentation. Documentation MUST explain the problem, algorithm choices, processing stages,
parameter meanings, execution steps, results, and known limitations. Terminology MUST be
consistent with the code, and technical terms MUST be defined when first introduced.
Claims about correctness or quality MUST be supported by tests or reproducible experiments.

### X. HSV Segmentation Remains Core

HSV threshold segmentation MUST remain the primary selection algorithm. New algorithms MUST
consume or evaluate its outputs as optional stages; they MUST NOT silently replace HSV selection.
Existing numerical conventions and hue wraparound MUST remain unchanged.

### XI. Backward Compatibility

Existing image/video workflows, public call signatures, default results, exports, and saved
experiment formats MUST remain usable. New behavior MUST be opt-in with compatible defaults.
Changes MUST include regression evidence; format evolution MUST document version handling and
preserve existing records without rewriting them.

### XII. Explicit Configuration

Parameters affecting selection, filtering, markers, or evaluation MUST be explicit validated
settings with documented units, defaults, and ranges. User-adjustable values MUST be exposed
through appropriate controls and recorded when necessary to reproduce results. Unexplained
hardcoded tuning constants MUST NOT determine new algorithm behavior.

### XIII. Preserve the Existing Python Architecture

Contributors MUST retain the existing processing, application, GUI, and I/O responsibilities
and reuse suitable components. Architectural changes MUST document the concrete requirement,
alternatives, compatibility impact, and justification before implementation. Python code MUST
remain readable, maintainable, and consistent with existing conventions.

### XIV. Acceptance Criteria for Every Feature

Every new feature MUST define observable acceptance criteria before implementation and include
automated tests covering normal behavior, relevant boundaries, invalid input, and integration
with affected workflows. New algorithms MUST be testable independently of GUI and persistence.
A feature MUST NOT be marked complete solely on visual inspection or task completion.

## Academic and Technical Constraints

- The project MUST remain focused on academic image processing and HSV segmentation.
- Algorithm documentation MUST state the actual library conventions for HSV channel ranges,
  hue wraparound, and color conversion whenever those conventions affect an operation.
- Input validation MUST make unsupported shapes, data types, ranges, and parameter values
  explicit rather than silently producing misleading results.
- Sample data and experimental inputs MUST have a documented source or generation method.
- Technology choices MUST remain open until required by a documented project need; this
  constitution does not mandate a GUI toolkit, framework, or storage system.

## Development Workflow and Review

1. Define the image processing behavior, assumptions, expected outputs, and acceptance criteria
   before implementing or changing an algorithm.
2. Assign GUI, processing, and file I/O responsibilities explicitly before adding modules or
   changing their interfaces.
3. Add or update automated core tests alongside behavior changes. For defect fixes, include a
   regression test that demonstrates the corrected behavior.
4. Run the relevant automated tests and affected documented experiments before considering a
   change complete. Record execution commands and outcomes in the change review.
5. Update explanations, parameter descriptions, and demonstration instructions when behavior
   changes. Review every change for correctness, clarity, separation of concerns, and scope.
6. Resolve constitution violations before acceptance. If a requirement conflicts with this
   constitution, propose an explicit amendment rather than silently bypassing a principle.

## Governance

This constitution governs project specifications, plans, tasks, implementation, tests, and
documentation. Project practices and design decisions MUST comply with its principles.
Every change review MUST check applicable principles and record any unresolved conflict.

Amendments MUST state the proposed change, its rationale, and its impact on existing artifacts
and code. Project maintainers MUST approve amendments before adoption. An accepted amendment
MUST update this document, its version, and its last amended date, and identify any required
migration work. The original ratification date MUST remain unchanged.

Versions MUST follow semantic versioning: MAJOR for incompatible governance changes or
principle removals or redefinitions; MINOR for added principles, sections, or materially
expanded guidance; PATCH for clarifications and wording fixes that preserve obligations.
Compliance MUST be checked during specification and planning, during change review, and before
an academic demonstration or submission. Governance changes MUST NOT silently modify dependent
templates or application artifacts.

**Version**: 1.1.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-28
