```
[
    StorePassword,
    CheckPasswordStrength,
    GeneratePassword,
    AutoFillPassword,
    SearchPasswords,
    StorePersonalInfo,
    AutoFillPersonalInfo,
    RetrievePersonalInfo,
    SharePassword,
    ImportPasswords,
    ExportPasswords,
    EnableTwoFactorAuthentication,
    DisableTwoFactorAuthentication
]
```

```

from agents import Agent, Runner
from toolkits.real.identify_safe_toolkit.openai_agent.identify_safe_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

identify_safe_toolkit_agent = Agent(
    name="identify_safe_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    StorePassword,
    CheckPasswordStrength,
    GeneratePassword,
    AutoFillPassword,
    SearchPasswords,
    StorePersonalInfo,
    AutoFillPersonalInfo,
    RetrievePersonalInfo,
    SharePassword,
    ImportPasswords,
    ExportPasswords,
    EnableTwoFactorAuthentication,
    DisableTwoFactorAuthentication
]
)

def main():
    prompt = ""
    response = Runner.run_sync(identify_safe_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

