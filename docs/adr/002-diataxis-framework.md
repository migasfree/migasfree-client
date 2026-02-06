# ADR 002: Adoption of Diátaxis Framework for Documentation

## Status

Accepted

## Context

Technical documentation often suffers from "instruction soup," where tutorials, reference material, and conceptual explanations are mixed together, leading to user confusion and poor searchability.

## Decision

We adopt the **Diátaxis Framework** to structure all technical documentation.

The documentation is divided into four strictly separated quadrants:

1. **Tutorials**: Learning-oriented, step-by-step guides for beginners.
2. **How-To Guides**: Problem-oriented, focused on specific tasks for users with some experience.
3. **Reference**: Information-oriented, technical specifications, and API documentation.
4. **Explanation**: Understanding-oriented, clarifying concepts and architectural background.

## Consequences

### Positive

- **Improved Clarity**: Users know exactly what to expect from a document based on its location and label.
- **Maintainability**: Clear boundaries make it easier to identify missing or outdated content.
- **Onboarding**: New contributors have a clear template for where to add different types of information.

### Negative

- **Rigidity**: Some content might feel like it "crosses borders," requiring careful editing to maintain separation.
- **Initial Effort**: Requires reorganizing existing documentation into the new structure.
