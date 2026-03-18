name: Bug Report
description: Report a bug to help us improve
title: "[BUG] "
labels: ["bug", "needs-triage"]

body:
  - type: markdown
    attributes:
      value: |
        Thank you for reporting a bug! Please fill out this form to help us understand and fix the issue.

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Clear description of the bug
      placeholder: What happened?
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: How to reproduce the issue?
      placeholder: |
        1. First step
        2. Second step
        3. ...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen?
      placeholder: Expected outcome...
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happens?
      placeholder: Actual outcome...
    validations:
      required: true

  - type: dropdown
    id: python_version
    attributes:
      label: Python Version
      options:
        - "3.9"
        - "3.10"
        - "3.11"
        - "3.12"
    validations:
      required: true

  - type: dropdown
    id: backend
    attributes:
      label: YOLO Backend
      options:
        - "PyTorch"
        - "OpenVINO"
        - "Not sure"
    validations:
      required: false

  - type: dropdown
    id: os
    attributes:
      label: Operating System
      options:
        - "Windows"
        - "Linux"
        - "macOS"
        - "Docker"
    validations:
      required: true

  - type: textarea
    id: error_message
    attributes:
      label: Error Message / Logs
      description: Paste any error messages or relevant logs
      placeholder: |
        ```
        Error traceback or logs here
        ```
      render: shell
    validations:
      required: false

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Any other information that might help
      placeholder: Screenshots, environment details, etc.
    validations:
      required: false

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: I have checked the documentation
          required: true
        - label: I have searched existing issues
          required: true
        - label: I have provided reproduction steps
          required: true
