# SolidWorks Macro Architecture Pack
Rules:
- Separate input validation, document creation, sketch creation, feature creation, rebuild, export, and error handling.
- Always define units and document type.
- Avoid destructive operations without confirmation.
Required inputs:
- Part/assembly/drawing target, units, dimensions, output folder, overwrite policy.
