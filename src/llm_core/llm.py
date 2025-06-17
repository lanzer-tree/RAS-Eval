from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_qwq import ChatQwQ
from pydantic import BaseModel
import json
from colorama import Fore
import os
from dotenv import load_dotenv, find_dotenv


find_dotenv()
load_dotenv()


tool_support_llm = [
    "ollama/qwen2.5:0.5b",
    "ollama/qwen2.5:1.5b",
    "ollama/qwen2.5:3b",
    "ollama/qwen2.5:7b",
    "ollama/qwen2.5:14b",
    "ollama/qwen2.5:32b",
    "ollama/qwen2.5:72b",
    "ollama/llama3.2:3b",
    "ollama/llama3.3:70b",
    "ollama/llama3.2:1b",
    "ollama/llama3.1:8b"
    "ollama/deepseek-r1-tool:8b",
    "ollama/llama3-tool:8b"
]

online_llm = {
    "gemini-2.0-flash": "google",
    "glm-4-flash": "zhipu",
    "qwq-32b": "aliyun",
    "qwen-plus": "aliyun",
    "qwen-turbo": "aliyun",
    "qwen-max": "aliyun",
    "deepseek-v3": "aliyun",
    "qwen2.5-1.5b-instruct": "aliyun",
    "qwen2.5-7b-instruct": "aliyun",
    "llama-4-scout-17b-16e-instruct": "aliyun",
    "llama3.3-70b-instruct": "aliyun",
    "llama3.2-3b-instruct": "aliyun",
    "llama3.1-70b-instruct": "aliyun"
}


class LLM:
    """Basic LLM implementation."""
    def __init__(self, model: str, temperature: float = 0, stream: bool = True):
        """
        Init the LLM model.
        :param model: The model name.
        :param temperature: The temperature.
        """
        self.tool_support: bool = False
        self.stream = stream
        provider = model.split("/")[0]
        model = model.split("/")[-1]
        if provider == "ollama":
            if model in tool_support_llm:
                self.llm = ChatOllama(
                    model=model,
                    temperature=temperature,
                )
                self.tool_support = True
            else:
                self.llm = OllamaFunctions(
                    model=model,
                    temperature=temperature,
                    format="json"
                )
                self.tool_support = False
        elif provider == "aliyun":
            api_key = os.environ["DASHSCOPE_API_KEY"]
            base_url = os.environ["DASHSCOPE_API_BASE"]
        elif provider == "zhipu":
            api_key = os.environ["ZHIPUAI_API_KEY"]
            base_url = os.environ["ZHIPUAI_BASE_URL"]
        elif provider == "google":
            api_key = os.environ["GEMINI_API_KEY"]
            base_url = os.environ["GEMINI_BASE_URL"]
        else:
            raise ValueError(f"Provider {provider} is not supported.")
        if "qwq" in model:
            self.llm = ChatQwQ(
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url,
                stream_usage=self.stream,
            )
        else:
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url,
                stream_usage=self.stream,
            )
        self.tool_support = True
        self.system_prompt: list[SystemMessage] = []

    def get_completion(self, prompt: str) -> BaseMessage:
        """
        Get the completion from model
        :param prompt: user prompt input
        :return: The content of model response
        """
        message = ChatPromptTemplate.from_template("{prompt}")
        chain = message | self.llm
        response = chain.invoke({"prompt": prompt})
        return response
    
    def get_json_completion(self, prompt: str, struct: BaseModel) -> dict:
        """
        Get the completion from model
        :param prompt: user prompt input
        :param struct: The struct of model response
        :return: The content of model response
        """
        chain = self.llm.with_structured_output(struct)
        response = chain.invoke(prompt)
        return json.loads(response.model_dump_json())
        