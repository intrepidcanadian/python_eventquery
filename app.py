from web3 import Web3
import json 
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import os 
import streamlit as st

load_dotenv()

api_key = os.getenv('ALCHEMY_API_KEY')
w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.g.alchemy.com/v2/{api_key}'))

st.write("Hello Tony! This is going to be awesome!")

st.markdown("**This is to create event log graphs**")

# st.markdown(api_key)

with st.form(key='my_form'):
    st.title("Input Form")

    # Create text input fields
    newaddress = st.text_input(label="Enter your address")
    
    # Create a submit button
    submit_button = st.form_submit_button(label='Submit')

# Code to handle the data after submission
if submit_button:
    st.write("The form was submitted!")
    st.write(f"Address: {newaddress}")

# Code for initializing address
gho_contract = {}
gho_contract["address"] = w3.to_checksum_address("0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f")
with open("abis/gho_abi.json") as f:
    data = json.load(f)
    gho_contract["abi"] = data

gho = w3.eth.contract(address=gho_contract["address"], abi=gho_contract["abi"])


v3_pool_contract = {}
v3_pool_contract["address"] = w3.to_checksum_address("0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2")
with open("abis/ethereum_v3_pool.json") as f:
    data = json.load(f)
    v3_pool_contract["abi"] = data

v3_pool = w3.eth.contract(
    address=v3_pool_contract["address"], abi=v3_pool_contract["abi"]
)




variable_debt_gho_contract = {}
variable_debt_gho_contract["address"] = w3.to_checksum_address("0x786dBff3f1292ae8F92ea68Cf93c30b34B1ed04B")
with open("abis/gho_variable_debt_abi.json") as f:
    data = json.load(f)
    variable_debt_gho_contract["abi"] = data

variable_debt_gho = w3.eth.contract(
    address=variable_debt_gho_contract["address"], abi=variable_debt_gho_contract["abi"]
)



with open("abis/gho_interest_rate_strategy_abi.json") as f:
    data = json.load(f)

    GHOinterestRateStrategy = w3.eth.contract(
        address="0x00524e8E4C5FD2b8D8aa1226fA16b39Cad69B8A0", 
        abi=data
    )

with open("abis/AaveProtocolDataProvider_abi.json") as f:
    data = json.load(f)
    aaveprotocoldataprovider = w3.eth.contract(address = "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3", abi=data)

with open("abis/UiPoolDataProviderV3_abi.json") as f:
    data = json.load(f)
    UiPoolDataProviderV3 = w3.eth.contract(address = "0x91c0eA31b49B69Ea18607702c5d9aC360bf3dE7d", abi=data)
    


# print (gho)
# print (v3_pool)
# print (variable_debt_gho_contract)

gho_decimals = gho.functions.decimals().call()
gho_totalSupply = gho.functions.totalSupply().call() / (10**gho_decimals)
print(f'GHO has {gho_decimals} decimals')
print(f"GHO total supply is: {'{0:,.1f}'.format(gho_totalSupply)}")

user = "0xE831C8903de820137c13681E78A5780afDdf7697"
gho_balance = gho.functions.balanceOf(user).call() / (10**gho_decimals)
print(f"{user}'s balance: {'{0:,.0f}'.format(gho_balance)}")

getFacilitatorsList = gho.functions.getFacilitatorsList().call()
getFacilitatorsList

bucketCapacity, bucketLevel, Name = gho.functions.getFacilitator(getFacilitatorsList[0]).call()
print(Name)
print(f'bucketCapacity: {bucketCapacity/10**gho_decimals/10**6}m')
print(f'bucketLevel: {round(bucketLevel/10**gho_decimals/10**6,1)}m')

bucketCapacity, bucketLevel = gho.functions.getFacilitatorBucket("0x00907f9921424583e7ffBfEdf84F92B7B2Be4977").call()

# Transfer event signature
transfer_event_signature = w3.keccak(text="Transfer(address,address,uint256)").hex()

fromBlock = 17698470 # GHO was deployed here
toBlock = w3.eth.block_number # get all blocks  
blockRangeSize = 100000      # we search 100k blocks at a time 

events = []
currentBlock = fromBlock

# iterate through 100k block chunks to pull all gho events
# note: we are doing that because the number of logs is too much for
# the node to handle 
while currentBlock < toBlock:
    
    endBlock = min(currentBlock + blockRangeSize, toBlock)
    print(f'Processing blocks {currentBlock} to {endBlock}')

    event_filter = {
        'fromBlock': currentBlock,
        'toBlock': endBlock,
        'address': gho.address,
        'topics': [transfer_event_signature]
    }

    logs = w3.eth.get_logs(event_filter)

    for log in logs:
        event = gho.events.Transfer().process_receipt({'logs': [log]})
        event_data = dict(event[0]['args'])  # Convert AttributeDict to dict
        event_data['blockNumber'] = log['blockNumber']  # Add block number
        events.append(event_data)

    currentBlock = endBlock + 1

    # Convert events to DataFrame
transfers = [{'from': e['from'], 'to': e['to'], 'value': e['value'], 'blockNumber': e['blockNumber']} for e in events]
transfers_df = pd.DataFrame(transfers)

transfers_df.groupby('from').count().reset_index().sort_values(['value']).head(5)

address_to_track = '0x383E7ACD889bF57b0D79A584009Cb570534aB518' # uniswap V3 GHO-USDT pool

address_transfers = transfers_df[(transfers_df['to'] == address_to_track) | (transfers_df['from'] == address_to_track)].copy()
address_transfers['balance_change'] = address_transfers.apply(lambda row: row['value'] if row['to'] == address_to_track else -row['value'], axis=1)
address_transfers['rolling_balance'] = address_transfers['balance_change'].cumsum() / 10**gho_decimals
address_transfers[['from','to','value','blockNumber','balance_change', 'rolling_balance']].tail(5)
# most recent 5 transfers

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Function to format the balance in thousands
def dynamic_formatter(x, pos):
    if x >= 1e6:  # If the value is in the millions
        return '%1.1fM' % (x * 1e-6)
    else:  # If the value is less than a million (in thousands)
        return '%1.0fK' % (x * 1e-3)

def format_in_millions(x, pos):
    return '%1.1fM' % (x * 1e-6)

# Ensure your DataFrame is sorted by blockNumber
address_transfers = address_transfers.sort_values(by='blockNumber')

# Plotting
fig, ax = plt.subplots()

# Using step function for discrete changes
ax.step(address_transfers['blockNumber'], address_transfers['rolling_balance'], where='post')

# Set the title and labels
ax.set_title('GHO Balance for {}'.format(address_to_track), fontsize=14, fontweight='bold')
ax.set_xlabel('Block Number', fontsize=12)
ax.set_ylabel('Address Balance', fontsize=12)

formatter = ticker.FuncFormatter(dynamic_formatter)
ax.yaxis.set_major_formatter(formatter)
x_formatter = ticker.FuncFormatter(format_in_millions)
ax.xaxis.set_major_formatter(x_formatter)

# Improve grid visibility and style
ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')

# Display the plot in Streamlit
st.pyplot(fig)