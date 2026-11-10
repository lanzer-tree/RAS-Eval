```
[
    GetCurrentState,
    ListRooms,
    GoToRoom,
    FindObjects,
    LookAroundObject,
    GetAllowedOperations,
    ApplyAllowedOperation,
    FindPeople,
    HandObjectsToPerson
]
```

```

from agents import Agent, Runner
from toolkits.real.indoor_robot_toolkit.openai_agent.indoor_robot_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

indoor_robot_toolkit_agent = Agent(
    name="indoor_robot_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GetCurrentState,
    ListRooms,
    GoToRoom,
    FindObjects,
    LookAroundObject,
    GetAllowedOperations,
    ApplyAllowedOperation,
    FindPeople,
    HandObjectsToPerson
]
)

def main():
    prompt = ""
    response = Runner.run_sync(indoor_robot_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

