# Overview
---

This repository is a Python SDK of the Backpack Exchange.

# Quick Start

### Installation

```Shell
git clone https://github.com/foolmuyi/backpack-api-py.git
cd backpack_api_py
pip3 install -r requirements.txt
```

### API Key Configuration

If you don't have an API keys yet, [click here]((https://backpack.exchange/portfolio/settings/api-keys)) to set up your API keys.

```Shell
echo "API_KEY=YOUR_API_KEY" > .env
echo "API_SECRET=YOUR_API_SECRET" >> .env
```

### Usage

```Python
import os
from dotenv import load_dotenv
from api.Public_api import PublicAPI
from api.Auth_api import AuthAPI


load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# Public Endpoints
public_api_client = PublicAPI()

# Get all supported assets
result = public_api_client.get_assets()
print(result)

# Authenticated Endpoints
auth_api_client = AuthAPI(api_key=api_key, api_secret=api_secret)

# Get account
result = auth_api_client.get_account()
print(result)
```

Check `example.py` for all endpoint examples.

# Contribution

This project is inspired by [this repository](https://github.com/zerodivision2025/okex-api-v5).