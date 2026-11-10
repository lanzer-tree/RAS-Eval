```
[
    add_event_to_calendar,
    get_events_from_calendar,
    search_event,
    remove_event_from_calendar,
    get_today_date,
    clear_calendar
]
```

```

from agents import Agent, Runner
from toolkits.real.calendar_toolkit.openai_agent.calendar_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

calendar_toolkit_agent = Agent(
    name="calendar_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    add_event_to_calendar,
    get_events_from_calendar,
    search_event,
    remove_event_from_calendar,
    get_today_date,
    clear_calendar
]
)

def main():
    prompt = ""
    response = Runner.run_sync(calendar_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

