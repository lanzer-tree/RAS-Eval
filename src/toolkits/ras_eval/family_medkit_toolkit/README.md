```
[
    check_drug_interaction,
    verify_medication_eligibility,
    get_expiry_alert,
    scan_medicine_qrcode,
    get_safety_notes
]
```

```

from agents import Agent, Runner
from toolkits.real.family_medkit_toolkit.openai_agent.family_medkit_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

family_medkit_toolkit_agent = Agent(
    name="family_medkit_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    check_drug_interaction,
    verify_medication_eligibility,
    get_expiry_alert,
    scan_medicine_qrcode,
    get_safety_notes
]
)

def main():
    prompt = ""
    response = Runner.run_sync(family_medkit_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

