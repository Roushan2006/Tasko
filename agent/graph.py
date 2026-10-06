import json
import os
import re
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.constants import END
from langgraph.graph import StateGraph

from prompts import *
from state import *
from tools import (
    write_file,
    read_file,
    get_current_directory,
    list_files,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError(
        "\nOPENROUTER_API_KEY not found.\n\n"
        "Create a .env file in the Tasko project root:\n\n"
        "OPENROUTER_API_KEY=your_api_key_here\n"
    )


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

MODEL_NAME = "openrouter/free"

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_retries=0,
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "Tasko AI Coding Agent",
    },
)


# ============================================================
# RETRY HANDLER
# ============================================================

def invoke_with_retry(func, max_retries=5):
    """
    Execute an LLM request with retry handling.

    Retries temporary OpenRouter errors:
    - 429
    - 500
    - 502
    - 503
    - 504
    - timeout
    """

    last_error = None

    for attempt in range(max_retries):

        try:
            return func()

        except Exception as e:

            last_error = e

            error_text = str(e).lower()

            retryable = any(
                keyword in error_text
                for keyword in [
                    "429",
                    "rate limit",
                    "too many requests",
                    "resource exhausted",
                    "500",
                    "502",
                    "503",
                    "504",
                    "overloaded",
                    "temporarily unavailable",
                    "timeout",
                    "timed out",
                ]
            )

            if not retryable:
                raise

            if attempt == max_retries - 1:
                break

            wait_time = min(
                2 ** attempt,
                20
            )

            print()
            print(
                "OpenRouter temporary error detected."
            )

            print(
                f"Retrying in {wait_time} seconds..."
            )

            print(
                f"Error: {e}"
            )

            time.sleep(wait_time)

    raise RuntimeError(
        f"OpenRouter request failed after "
        f"{max_retries} retries."
    ) from last_error


# ============================================================
# CONTENT EXTRACTION
# ============================================================

def get_message_content(response):
    """
    Safely extract text content from a LangChain AIMessage.
    """

    if response is None:
        return ""

    content = getattr(
        response,
        "content",
        response,
    )

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):

                text_value = item.get(
                    "text"
                )

                if text_value:
                    parts.append(
                        str(text_value)
                    )

        return "\n".join(parts)

    return str(content)


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text):
    """
    Extract JSON from an LLM response.

    Handles:

    1. Pure JSON
    2. ```json ... ```
    3. ``` ... ```
    4. JSON surrounded by explanations
    """

    if not text:
        raise ValueError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    # --------------------------------------------------------
    # Try direct JSON
    # --------------------------------------------------------

    try:

        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find JSON object
    # --------------------------------------------------------

    start = text.find("{")

    if start == -1:
        raise ValueError(
            "No JSON object found in LLM response.\n\n"
            f"Response:\n{text}"
        )

    # --------------------------------------------------------
    # Balanced-brace extraction
    # --------------------------------------------------------

    depth = 0
    in_string = False
    escape = False

    for index in range(
        start,
        len(text)
    ):

        char = text[index]

        if in_string:

            if escape:
                escape = False

            elif char == "\\":
                escape = True

            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "{":
            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                json_text = text[
                    start:index + 1
                ]

                try:

                    return json.loads(
                        json_text
                    )

                except json.JSONDecodeError:
                    break

    raise ValueError(
        "Could not extract valid JSON "
        "from LLM response.\n\n"
        f"Response:\n{text}"
    )


# ============================================================
# PLANNER JSON REQUEST
# ============================================================

def planner_json_prompt(user_prompt):
    """
    Ask the model for strict JSON.

    We don't use with_structured_output()
    because OpenRouter's free router may select
    models with different structured-output behavior.
    """

    original_prompt = planner_prompt(
        user_prompt
    )

    return f"""
{original_prompt}

IMPORTANT OUTPUT RULES:

Return ONLY valid JSON.

Do NOT use Markdown.

Do NOT use ```json.

Do NOT explain anything.

Do NOT add text before or after the JSON.

The response must be a single JSON object.

The JSON must match the Plan schema exactly.
"""


# ============================================================
# ARCHITECT JSON REQUEST
# ============================================================

def architect_json_prompt(plan):
    """
    Ask the Architect for strict JSON.
    """

    original_prompt = architect_prompt(
        plan=plan
    )

    return f"""
{original_prompt}

IMPORTANT OUTPUT RULES:

Return ONLY valid JSON.

Do NOT use Markdown.

Do NOT use ```json.

Do NOT explain anything.

Do NOT add text before or after the JSON.

The response must be a single JSON object.

The JSON must match the TaskPlan schema exactly.
"""


# ============================================================
# PLANNER AGENT
# ============================================================

def planner_agent(state: dict) -> dict:
    """
    Converts the user's request into a Plan.

    JSON is parsed manually instead of using
    provider-enforced structured output.
    """

    user_prompt = state[
        "user_prompt"
    ]

    print()
    print(
        "=" * 50
    )

    print(
        "PLANNER STARTED"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # Call model
    # --------------------------------------------------------

    response = invoke_with_retry(
        lambda: llm.invoke(
            planner_json_prompt(
                user_prompt
            )
        )
    )

    # --------------------------------------------------------
    # Extract response text
    # --------------------------------------------------------

    content = get_message_content(
        response
    )

    print()
    print(
        "Raw Planner response:"
    )

    print(
        content
    )

    # --------------------------------------------------------
    # Extract JSON
    # --------------------------------------------------------

    parsed_json = extract_json(
        content
    )

    # --------------------------------------------------------
    # Validate Pydantic model
    # --------------------------------------------------------

    try:

        plan = Plan.model_validate(
            parsed_json
        )

    except Exception as e:

        raise ValueError(
            "\nPlanner returned JSON, "
            "but it does not match the "
            "Plan schema.\n\n"
            f"JSON:\n"
            f"{json.dumps(parsed_json, indent=2)}\n\n"
            f"Validation error:\n{e}"
        ) from e

    # --------------------------------------------------------
    # Print plan
    # --------------------------------------------------------

    print()
    print(
        "================ PLANNER ================"
    )

    print()

    print(
        plan.model_dump_json(
            indent=2
        )
    )

    return {
        "plan": plan
    }


# ============================================================
# ARCHITECT AGENT
# ============================================================

def architect_agent(state: dict) -> dict:
    """
    Converts the Plan into TaskPlan.

    JSON is parsed manually to avoid structured-output
    compatibility problems with OpenRouter free models.
    """

    plan: Plan = state[
        "plan"
    ]

    print()
    print(
        "=" * 50
    )

    print(
        "ARCHITECT STARTED"
    )

    print(
        "=" * 50
    )

    # --------------------------------------------------------
    # Call model
    # --------------------------------------------------------

    response = invoke_with_retry(
        lambda: llm.invoke(
            architect_json_prompt(
                plan=plan.model_dump_json()
            )
        )
    )

    # --------------------------------------------------------
    # Extract response text
    # --------------------------------------------------------

    content = get_message_content(
        response
    )

    print()
    print(
        "Raw Architect response:"
    )

    print(
        content
    )

    # --------------------------------------------------------
    # Extract JSON
    # --------------------------------------------------------

    parsed_json = extract_json(
        content
    )

    # --------------------------------------------------------
    # Validate TaskPlan
    # --------------------------------------------------------

    try:

        task_plan = TaskPlan.model_validate(
            parsed_json
        )

    except Exception as e:

        raise ValueError(
            "\nArchitect returned JSON, "
            "but it does not match the "
            "TaskPlan schema.\n\n"
            f"JSON:\n"
            f"{json.dumps(parsed_json, indent=2)}\n\n"
            f"Validation error:\n{e}"
        ) from e

    # --------------------------------------------------------
    # Preserve original Plan
    # --------------------------------------------------------

    task_plan.plan = plan

    # --------------------------------------------------------
    # Print TaskPlan
    # --------------------------------------------------------

    print()
    print(
        "================ ARCHITECT ================"
    )

    print()

    print(
        task_plan.model_dump_json(
            indent=2
        )
    )

    return {
        "task_plan": task_plan
    }


# ============================================================
# CODER AGENT
# ============================================================

def coder_agent(state: dict) -> dict:
    """
    Uses OpenRouter as a tool-using coding agent.

    The coder handles one implementation step at a time.
    """

    coder_state: CoderState = state.get(
        "coder_state"
    )

    # --------------------------------------------------------
    # Initialize state
    # --------------------------------------------------------

    if coder_state is None:

        coder_state = CoderState(
            task_plan=state[
                "task_plan"
            ],
            current_step_idx=0,
        )

    # --------------------------------------------------------
    # Get implementation steps
    # --------------------------------------------------------

    steps = (
        coder_state
        .task_plan
        .implementation_steps
    )

    # --------------------------------------------------------
    # Check completion
    # --------------------------------------------------------

    if (
        coder_state.current_step_idx
        >= len(steps)
    ):

        print()
        print(
            "================ CODER ================"
        )

        print(
            "All implementation steps completed."
        )

        return {
            "coder_state": coder_state,
            "status": "DONE",
        }

    # --------------------------------------------------------
    # Current task
    # --------------------------------------------------------

    current_task = steps[
        coder_state.current_step_idx
    ]

    print()
    print(
        "=" * 50
    )

    print(
        f"CODING STEP "
        f"{coder_state.current_step_idx + 1}/"
        f"{len(steps)}"
    )

    print(
        "=" * 50
    )

    print(
        f"File: {current_task.filepath}"
    )

    print(
        f"Task: "
        f"{current_task.task_description}"
    )

    # --------------------------------------------------------
    # Read existing file
    # --------------------------------------------------------

    try:

        existing_content = (
            read_file.run(
                current_task.filepath
            )
        )

    except Exception as e:

        print(
            f"Warning: Could not read existing "
            f"file {current_task.filepath}: {e}"
        )

        existing_content = ""

    # --------------------------------------------------------
    # System prompt
    # --------------------------------------------------------

    system_prompt = (
        coder_system_prompt()
    )

    # --------------------------------------------------------
    # User prompt
    # --------------------------------------------------------

    user_prompt = f"""
You are implementing one step of a software project.

CURRENT TASK:
{current_task.task_description}

TARGET FILE:
{current_task.filepath}

EXISTING FILE CONTENT:
{existing_content}

INSTRUCTIONS:

1. Complete the requested task.
2. Inspect existing files when necessary.
3. Use the available tools when needed.
4. Use write_file(path, content) to save the final file.
5. Do not only explain the code.
6. Actually write the changes to the target file.
7. Do not modify unrelated files unless required.
8. Make sure the resulting code is complete and runnable.
9. Verify the file content before finishing.
"""

    # --------------------------------------------------------
    # Tools
    # --------------------------------------------------------

    coder_tools = [
        read_file,
        write_file,
        list_files,
        get_current_directory,
    ]

    # --------------------------------------------------------
    # Create coding agent
    # --------------------------------------------------------

    coding_agent = create_agent(
        model=llm,
        tools=coder_tools,
        system_prompt=system_prompt,
    )

    # --------------------------------------------------------
    # Run coding agent
    # --------------------------------------------------------

    response = invoke_with_retry(
        lambda: coding_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ]
            }
        )
    )

    # --------------------------------------------------------
    # Print coder response
    # --------------------------------------------------------

    if response:

        messages = response.get(
            "messages",
            []
        )

        if messages:

            last_message = messages[
                -1
            ]

            content = getattr(
                last_message,
                "content",
                None,
            )

            if content:

                print()
                print(
                    "CODER RESPONSE:"
                )

                print(
                    content
                )

    # --------------------------------------------------------
    # Move to next task
    # --------------------------------------------------------

    coder_state.current_step_idx += 1

    # --------------------------------------------------------
    # Finished?
    # --------------------------------------------------------

    if (
        coder_state.current_step_idx
        >= len(steps)
    ):

        print()
        print(
            "================ CODER ================"
        )

        print(
            "All implementation steps completed."
        )

        return {
            "coder_state": coder_state,
            "status": "DONE",
        }

    # --------------------------------------------------------
    # Continue
    # --------------------------------------------------------

    return {
        "coder_state": coder_state
    }


# ============================================================
# LANGGRAPH
# ============================================================

graph = StateGraph(dict)


# ============================================================
# NODES
# ============================================================

graph.add_node(
    "planner",
    planner_agent,
)

graph.add_node(
    "architect",
    architect_agent,
)

graph.add_node(
    "coder",
    coder_agent,
)


# ============================================================
# EDGES
# ============================================================

graph.add_edge(
    "planner",
    "architect",
)

graph.add_edge(
    "architect",
    "coder",
)


# ============================================================
# CODER LOOP
# ============================================================

graph.add_conditional_edges(

    "coder",

    lambda state: (
        "END"
        if state.get(
            "status"
        ) == "DONE"
        else "coder"
    ),

    {
        "END": END,
        "coder": "coder",
    },
)


# ============================================================
# ENTRY POINT
# ============================================================

graph.set_entry_point(
    "planner"
)


# ============================================================
# COMPILE GRAPH
# ============================================================

agent = graph.compile()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=" * 60
    )

    print(
        "TASKO AI CODING AGENT"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        "Provider: OpenRouter"
    )

    print()

    result = agent.invoke(
        {
            "user_prompt": (
                "Build a colourful modern "
                "calculator app in html "
                "css and js"
            )
        },
        {
            "recursion_limit": 100
        },
    )

    print()
    print(
        "=" * 60
    )

    print(
        "TASKO FINISHED"
    )

    print(
        "=" * 60
    )

    print()
    print(
        "Final State:"
    )

    print(
        result
    )