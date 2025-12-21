# /Users/shanzi/iemsProject/app/core/config.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    raise ValueError("API Key not found! Please check if the .env file exists and if the variable name is correct.")

llm = ChatOpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen3-max",
    temperature=0.3,
)