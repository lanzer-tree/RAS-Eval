```
[
    register_vehicle,
    get_vehicle_info,
    update_vehicle_status,
    delete_vehicle,
    get_available_spots,
    allocate_spot,
    release_spot,
    get_spot_status,
    calculate_parking_fee,
    process_payment,
    get_payment_history,
    get_daily_statistics,
    get_occupancy_rate,
    get_revenue_report
]
```

```

from agents import Agent, Runner
from toolkits.real.carpark_toolkit.openai_agent.carpark_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

carpark_toolkit_agent = Agent(
    name="carpark_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    register_vehicle,
    get_vehicle_info,
    update_vehicle_status,
    delete_vehicle,
    get_available_spots,
    allocate_spot,
    release_spot,
    get_spot_status,
    calculate_parking_fee,
    process_payment,
    get_payment_history,
    get_daily_statistics,
    get_occupancy_rate,
    get_revenue_report
]
)

def main():
    prompt = ""
    response = Runner.run_sync(carpark_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

