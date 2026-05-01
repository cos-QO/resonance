Create a supervised UI work kickoff from `$ARGUMENTS`.

Do this in order:

1. Resolve the Linear issue, Figma reference, and visual reference inputs.
2. Create a local context bundle for the task.
3. Read the relevant QO standards and existing reusable component context.
4. Identify any missing required inputs.
5. Stop and ask the user if the issue lacks any of:
   - product requirement
   - Figma URL
   - visual reference code or screenshots
   - acceptance criteria
6. When inputs are sufficient, prepare the task for `/qo-ui-analyze`.

Do not implement code in this command.
