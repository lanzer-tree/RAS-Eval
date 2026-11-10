```
[
    save_health_profile,
    get_health_profile,
    update_health_profile,
    save_health_records,
    get_health_records,
    generate_health_summary,
    connect_smart_devices,
    get_medication_reminder,
    record_medication_taken,
    search_nearby_hospitals,
    book_doctor_appointment,
    notify_emergency_contact
]
```

```

from agents import Agent, Runner
from toolkits.real.elderly_care_toolkit.openai_agent.elderly_care_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

elderly_care_toolkit_agent = Agent(
    name="elderly_care_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    save_health_profile,
    get_health_profile,
    update_health_profile,
    save_health_records,
    get_health_records,
    generate_health_summary,
    connect_smart_devices,
    get_medication_reminder,
    record_medication_taken,
    search_nearby_hospitals,
    book_doctor_appointment,
    notify_emergency_contact
]
)

def main():
    prompt = ""
    response = Runner.run_sync(elderly_care_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

