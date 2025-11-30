import openai, os, json
from dotenv import load_dotenv

load_dotenv()


openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_API_ENDPOINT")

data = openai.embeddings.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING"),
    input="Hello World"
)

for item in data.data:
    print(type(item.embedding))
    print(len(item.embedding))
    print(item.embedding)