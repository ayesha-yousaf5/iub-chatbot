from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="iub-rag-assistant")

response = llm.invoke("Say hello in one short sentence.")

print(response)