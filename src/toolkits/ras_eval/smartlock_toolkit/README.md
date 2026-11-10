```
[
    find_guest_id_by_name,
    check_lock_status,
    lock_door,
    unlock_door,
    search_guests,
    add_guest,
    delete_guest,
    grant_guest_access,
    revoke_guest_access,
    generate_temporary_access_code,
    revoke_temporary_access_code,
    view_access_history
]
```

```

from agents import Agent, Runner
from toolkits.real.smartlock_toolkit.openai_agent.smartlock_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

smartlock_toolkit_agent = Agent(
    name="smartlock_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    find_guest_id_by_name,
    check_lock_status,
    lock_door,
    unlock_door,
    search_guests,
    add_guest,
    delete_guest,
    grant_guest_access,
    revoke_guest_access,
    generate_temporary_access_code,
    revoke_temporary_access_code,
    view_access_history
]
)

def main():
    prompt = ""
    response = Runner.run_sync(smartlock_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

