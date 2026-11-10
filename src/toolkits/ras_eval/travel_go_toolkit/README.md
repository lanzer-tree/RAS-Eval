```
[
    search_destination,
    plan_itinerary,
    book_transportation,
    book_accommodation,
    get_travel_weather,
    update_itinerary,
    track_travel_orders,
    get_local_services,
    handle_travel_issue
]
```

```

from agents import Agent, Runner
from toolkits.real.travel_go_toolkit.openai_agent.travel_go_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

travel_go_toolkit_agent = Agent(
    name="travel_go_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    search_destination,
    plan_itinerary,
    book_transportation,
    book_accommodation,
    get_travel_weather,
    update_itinerary,
    track_travel_orders,
    get_local_services,
    handle_travel_issue
]
)

def main():
    prompt = ""
    response = Runner.run_sync(travel_go_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

