```
[
    reset_hr_assistant_environment,
    list_candidates,
    evaluate_candidate,
    summarize_resume,
    send_candidate_message,
    schedule_interview
]
```

```

from agents import Agent, Runner
from toolkits.real.hr_assistant_toolkit.openai_agent.hr_assistant_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

hr_assistant_toolkit_agent = Agent(
    name="hr_assistant_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    reset_hr_assistant_environment,
    list_candidates,
    evaluate_candidate,
    summarize_resume,
    send_candidate_message,
    schedule_interview
]
)

def main():
    prompt = ""
    response = Runner.run_sync(hr_assistant_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

