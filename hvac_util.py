from dotenv import load_dotenv, find_dotenv
import hvac
import os
import sys

sys.path.append('.')
_ = load_dotenv(find_dotenv())


def get_openai_key():
    client = hvac.Client(
        url='https://vault.abbank.vn',
        token=os.environ.get("VAULT_TOKEN"),)

    read_response = client.secrets.kv.read_secret_version(
        path='ai', mount_point='ai-platform')
    api_key = read_response['data']['data']['ChatGPTKey']
    os.environ['OPENAI_API_KEY'] = api_key
    return api_key