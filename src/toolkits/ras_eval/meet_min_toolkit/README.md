```
[
    init_meeting,
    record_meeting_content,
    extract_key_points,
    generate_meeting_minutes,
    assign_meeting_tasks,
    track_task_progress,
    update_meeting_minutes,
    distribute_meeting_minutes,
    query_meeting_history
]
```

```

from agents import Agent, Runner
from toolkits.real.meet_min_toolkit.openai_agent.meet_min_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

meet_min_toolkit_agent = Agent(
    name="meet_min_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    init_meeting,
    record_meeting_content,
    extract_key_points,
    generate_meeting_minutes,
    assign_meeting_tasks,
    track_task_progress,
    update_meeting_minutes,
    distribute_meeting_minutes,
    query_meeting_history
]
)

def main():
    prompt = ""
    response = Runner.run_sync(meet_min_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

