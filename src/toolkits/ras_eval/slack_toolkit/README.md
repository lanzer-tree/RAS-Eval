```
[
    send_message,
    create_channel,
    join_channel,
    leave_channel,
    search_message,
    search_channel_or_user,
    update_profile_and_status,
    manage_membership,
    get_user_details,
    download_slack_file
]
```

```

from agents import Agent, Runner
from toolkits.real.slack_toolkit.openai_agent.slack_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

slack_toolkit_agent = Agent(
    name="slack_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    send_message,
    create_channel,
    join_channel,
    leave_channel,
    search_message,
    search_channel_or_user,
    update_profile_and_status,
    manage_membership,
    get_user_details,
    download_slack_file
]
)

def main():
    prompt = ""
    response = Runner.run_sync(slack_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

