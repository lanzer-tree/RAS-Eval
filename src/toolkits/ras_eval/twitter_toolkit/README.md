```
[
    PostTweet,
    SearchTweets,
    ReadTweet,
    DeleteTweets,
    FollowUsers,
    UnfollowUsers,
    GetUserProfile,
    LikeTweet,
    UnlikeTweet,
    Retweet,
    ReplyToTweet
]
```

```

from agents import Agent, Runner
from toolkits.real.twitter_toolkit.openai_agent.twitter_toolkit import *
import os
from agents.extensions.models.litellm_model import LitellmModel

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_API_BASE"] = ""

model = ""

twitter_toolkit_agent = Agent(
    name="twitter_toolkit_agent",
    instructions="You are a helpful assistant.",
    model=LitellmModel(model=model, api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_API_BASE"]),
    tools=[
    PostTweet,
    SearchTweets,
    ReadTweet,
    DeleteTweets,
    FollowUsers,
    UnfollowUsers,
    GetUserProfile,
    LikeTweet,
    UnlikeTweet,
    Retweet,
    ReplyToTweet
]
)

def main():
    prompt = ""
    response = Runner.run_sync(twitter_toolkit_agent, prompt)
    print(response.final_output)

if __name__ == "__main__":
    main()

```

