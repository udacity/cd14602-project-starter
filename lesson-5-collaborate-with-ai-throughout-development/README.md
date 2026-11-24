# Lesson 5 Exercises: Collaborate with AI Throughout the Development Cycle

You build one application across five exercises, an expense tracker CLI: plan it, generate its code, test it,
refactor it, and document it, with an AI assistant and with every engineering decision kept yours.

## Exercise structure

| Folder | Exercise | You produce |
|---|---|---|
| `exercises/concept1-ai-planning-collaboration/` | AI Planning Collaboration | `architecture_plan.md`, `interfaces.py`, `project_structure.txt` |
| `exercises/concept2-ai-code-generation/` | AI Code Generation | the CSV loader and the report strategies |
| `exercises/concept3-ai-test-creation/` | AI Test Creation | `test_report_engine.py` |
| `exercises/concept4-ai-refactoring-collaboration/` | AI Refactoring Collaboration | `cli_interface_v2.py`, `refactoring_notes.md` |
| `exercises/concept5-ai-documentation-generation/` | AI Documentation Generation | `README.md`, `ARCHITECTURE.md`, better docstrings |

Each concept folder holds a `starter/` (where you work), a `solution/` (to compare with when you finish), a
`README.md` (the commands and the results to expect) and a `PROMPTS.md` (the solution video's prompts, matched to the exercise's files).
The steps for each exercise are on its Exercise page in the classroom.

## Prerequisites

- Python 3.10 or higher, and pytest
- An AI assistant (Claude, ChatGPT, GitHub Copilot, or similar)
- Lesson 3's structured XML prompting

## Getting started

```bash
cd exercises/concept1-ai-planning-collaboration/starter
pytest test_planning_process.py -v
```

Each exercise starts with a test run that fails or reports what is missing, and ends when the same run passes.
Refactoring is the exception: its tests pass from the start, and they must keep passing while you change the code.

## Tips for success

1. **Apply structured XML prompting** - Use the techniques from Lesson 3 throughout all exercises
2. **Maintain engineering ownership** - You make the decisions, AI provides assistance
3. **Focus on quality, not speed** - Good collaboration practices matter more than fast results
4. **Validate everything** - Test and review all AI-generated code
