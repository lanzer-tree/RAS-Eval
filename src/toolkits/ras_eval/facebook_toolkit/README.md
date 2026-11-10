```
[
    GetFacebookUserProfile,
    UpdateUserProfile,
    SearchFriends,
    CreatePost,
    SearchPosts,
    SearchMyPosts,
    GetPost,
    UpdatePost,
    DeletePost,
    CreateComment,
    GetMessages,
    SendFacebookMessage
]
```

```

from agents import Agent, Runner
from toolkits.real.facebook_toolkit.openai_agent.facebook_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

facebook_toolkit_agent = Agent(
    name="facebook_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    GetFacebookUserProfile,
    UpdateUserProfile,
    SearchFriends,
    CreatePost,
    SearchPosts,
    SearchMyPosts,
    GetPost,
    UpdatePost,
    DeletePost,
    CreateComment,
    GetMessages,
    SendFacebookMessage
]
)

def main():
    prompt = ""
    response = Runner.run_sync(facebook_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

