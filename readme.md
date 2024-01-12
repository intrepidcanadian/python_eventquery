# This looks to create a website to see the balances of an address.

- First install streamlit and virtualenv so that it can be used to run python and set up a virtual environment for dependencies

pip install streamlit
pip install virtualenv

- Setup your virtual environment. The terminal and folder should reflect the virtual environment created, in this case it is venv.

virtualenv venv

- Activate your virtual environment

source venv/bin/activate

- Install dependencies 

pip freeze > requirements.txt
pip install -r requirements.txt
pip install python-dotenv


#### Some helpful links and guides:

- Need to get set up with a node to query data? [link](https://docs.alchemy.com/docs/alchemy-quickstart-guide)

- web3.py [guide](https://web3py.readthedocs.io/en/stable/quickstart.html)

- a deep dive into ethereum logs [guide](https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371)

- gho [docs](https://docs.gho.xyz/developer-docs/overview)

- aave [docs](https://docs.aave.com/developers/getting-started/readme)
