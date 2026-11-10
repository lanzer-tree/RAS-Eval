```
[
    create_sql_database,
    insert_data,
    query_all_data,
    query_data,
    clear_sql_database,
    delete_data
]
```

```

from agents import Agent, Runner
from toolkits.real.sql_toolkit.openai_agent.sql_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

sql_toolkit_agent = Agent(
    name="sql_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    create_sql_database,
    insert_data,
    query_all_data,
    query_data,
    clear_sql_database,
    delete_data
]
)

def main():
    prompt = ""
    response = Runner.run_sync(sql_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

