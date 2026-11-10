```
[
    SearchFlights,
    GetFlightDetails,
    SearchAccommodations,
    Booking,
    SearchReservations,
    CancelReservations,
    RetrieveSavedInformation
]
```

```

from agents import Agent, Runner
from toolkits.real.expedia_toolkit.openai_agent.expedia_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

expedia_toolkit_agent = Agent(
    name="expedia_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchFlights,
    GetFlightDetails,
    SearchAccommodations,
    Booking,
    SearchReservations,
    CancelReservations,
    RetrieveSavedInformation
]
)

def main():
    prompt = ""
    response = Runner.run_sync(expedia_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

