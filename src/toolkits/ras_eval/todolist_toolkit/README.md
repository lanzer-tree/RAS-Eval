```
[
    CreateTask,
    UpdateTask,
    DeleteTask,
    SearchTasks,
    SetReminder,
    ShareTask,
    GetTaskIdsByName
]
```

```

from agents import Agent, Runner
from toolkits.real.todolist_toolkit.openai_agent.todolist_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

todolist_toolkit_agent = Agent(
    name="todolist_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    CreateTask,
    UpdateTask,
    DeleteTask,
    SearchTasks,
    SetReminder,
    ShareTask,
    GetTaskIdsByName
]
)

def main():
    prompt = ""
    response = Runner.run_sync(todolist_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

