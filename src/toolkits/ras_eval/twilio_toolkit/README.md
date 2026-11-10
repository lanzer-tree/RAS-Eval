```
[
    SendSms,
    GetSmsHistory,
    GetReceivedSmsMessages,
    GetSmsPricing,
    GetPhoneNumberInfo,
    GetScheduledActions,
    CancelScheduledAction
]
```

```

from agents import Agent, Runner
from toolkits.real.twilio_toolkit.openai_agent.twilio_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

twilio_toolkit_agent = Agent(
    name="twilio_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    SendSms,
    GetSmsHistory,
    GetReceivedSmsMessages,
    GetSmsPricing,
    GetPhoneNumberInfo,
    GetScheduledActions,
    CancelScheduledAction
]
)

def main():
    prompt = ""
    response = Runner.run_sync(twilio_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

