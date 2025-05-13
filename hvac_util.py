from dotenv import load_dotenv, find_dotenv
import hvac
import os
import sys

sys.path.append('.')
_ = load_dotenv(find_dotenv())

def get_azure_openai_config():
    """
    Lấy thông tin cấu hình Azure OpenAI từ file .env
    """
    #
    client = hvac.Client(
        url='https://vault.abbank.vn',
        token=os.environ.get("VAULT_TOKEN"),)

    read_response = client.secrets.kv.read_secret_version(
        path='ai', mount_point='ai-platform')
    api_key = read_response['data']['data']['ChatGPTKey']
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    
    #api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

    if not api_key or not endpoint or not deployment_name:
        raise ValueError("AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, or AZURE_OPENAI_DEPLOYMENT_NAME is not set in the environment variables.")

    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "deployment_name": deployment_name,
        "api_version": api_version
    }