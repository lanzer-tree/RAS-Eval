```
[
    SearchLocations,
    GetRoadDetails,
    GetIntersectionDetails,
    SearchRoute,
    CheckTrafficLightsStates,
    ManageTrafficLightState,
    MonitorTrafficCongestion,
    PredictTrafficCongestion,
    AnalyzeTrafficPatterns,
    GivePriorityToEmergencyVehicle,
    GivePriorityToPublicTransportation,
    ScheduleRoadMaintenance
]
```

```

from agents import Agent, Runner
from toolkits.real.traffic_control_toolkit.openai_agent.traffic_control_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

traffic_control_toolkit_agent = Agent(
    name="traffic_control_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchLocations,
    GetRoadDetails,
    GetIntersectionDetails,
    SearchRoute,
    CheckTrafficLightsStates,
    ManageTrafficLightState,
    MonitorTrafficCongestion,
    PredictTrafficCongestion,
    AnalyzeTrafficPatterns,
    GivePriorityToEmergencyVehicle,
    GivePriorityToPublicTransportation,
    ScheduleRoadMaintenance
]
)

def main():
    prompt = ""
    response = Runner.run_sync(traffic_control_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

