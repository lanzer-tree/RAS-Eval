```
[
    SearchDoctors,
    ConsultDoctor,
    ScheduleAppointment,
    ManageAppointments,
    AccessUserInfo,
    AccessMedicalHistory,
    RequestPrescription,
    ViewPrescriptions,
    SendMessage,
    LeaveReview,
    ViewReviews
]
```

```

from agents import Agent, Runner
from toolkits.real.teladoc_toolkit.openai_agent.teladoc_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

teladoc_toolkit_agent = Agent(
    name="teladoc_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SearchDoctors,
    ConsultDoctor,
    ScheduleAppointment,
    ManageAppointments,
    AccessUserInfo,
    AccessMedicalHistory,
    RequestPrescription,
    ViewPrescriptions,
    SendMessage,
    LeaveReview,
    ViewReviews
]
)

def main():
    prompt = ""
    response = Runner.run_sync(teladoc_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

