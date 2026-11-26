# Issue tracker: GitHub

Issues and specs live in Rowdydangerous/omarchy-cogitator-v2.
Use gh with --repo Rowdydangerous/omarchy-cogitator-v2 for tracker operations.

## Operations

- Create: gh issue create --title "..." --body-file <file>
- Read: gh issue view <number> --json number,title,body,labels,comments
- List: gh issue list --state open --json number,title,body,labels
- Comment: gh issue comment <number> --body-file <file>
- Label: gh issue edit <number> --add-label <label> or --remove-label <label>
- Close: explain the outcome in a comment, then gh issue close <number>.

Verify the target repository before creating issues. Product issues belong
here; the marketplace submission is a separate external review thread.

## Hierarchy and blockers

Use native GitHub sub-issues and issue dependencies when supported.
Dependency API calls require numeric database issue IDs, not issue numbers.
When unavailable, use "Part of #<parent>" and "Blocked by: #<number>"
in ticket bodies, with a task list on the parent.
A ticket is startable only when all its blockers are closed.

## Skill conventions

"Publish to the issue tracker" means create a GitHub issue.
"Fetch the relevant ticket" means read its body, labels, and comments.

PRs as a request surface: no.

For wayfinding, use a parent issue labelled wayfinder:map and linked child
issues labelled wayfinder:research, wayfinder:prototype, wayfinder:grilling,
or wayfinder:task. Claim a ready ticket by assigning it to the driving user.
Record its result before closing it and link the result from the parent.
