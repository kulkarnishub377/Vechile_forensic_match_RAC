name: Feature Request
description: Suggest an idea for this project
title: "[FEATURE] "
labels: ["enhancement", "needs-triage"]

body:
  - type: markdown
    attributes:
      value: |
        Thank you for suggesting a feature! Share your idea to help us improve.

  - type: textarea
    id: description
    attributes:
      label: Feature Description
      description: Clear description of the feature
      placeholder: What would you like to see?
    validations:
      required: true

  - type: textarea
    id: motivation
    attributes:
      label: Motivation
      description: Why is this feature important?
      placeholder: What problem would this solve?
    validations:
      required: true

  - type: textarea
    id: implementation
    attributes:
      label: Suggested Implementation
      description: How could this be implemented?
      placeholder: Any ideas on how to implement this?
    validations:
      required: false

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Any alternative approaches?
      placeholder: Other ways to solve this...
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Any other information
      placeholder: Screenshots, references, etc.
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: I have searched for similar feature requests
          required: true
        - label: This feature is not in the roadmap
          required: false
