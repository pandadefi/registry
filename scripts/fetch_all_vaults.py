import requests

# pretty print is used to print the output in the console in an easy to read format
from pprint import pprint


# function to use requests.post to make an API call to the subgraph url
def run_query(q):

    # endpoint where you are making the request
    request = requests.post(
        "https://api.thegraph.com/subgraphs/name/rareweasel/yearn-vaults-v2-subgraph-mainnet"
        "",
        json={"query": query},
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed. return code is {}.      {}".format(
                request.status_code, query
            )
        )


# The Graph query - Query aave for a list of the last 10 flash loans by time stamp
query = """
{
  registries {
    id
    vaults {
     id
      apiVersion
      token {
        id
      }
    }
  }
}
"""


def unique(list):
    unique_list = []

    for x in list:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

def fetch_data():
    result = run_query(query)
    # # pretty print the results to make it easier to read
    # pprint(result)
    return (
        result["data"]["registries"][0]["vaults"]
        + result["data"]["registries"][1]["vaults"]
    )


def order_vaults(data):
    vaults = {
        "0.4.3": [],
        "0.4.2": [],
        "0.4.1": [],
        "0.4.0": [],
        "0.3.5": [],
        "0.3.4": [],
        "0.3.3": [],
        "0.3.2": [],
        "0.3.1": [],
        "0.3.0": [],
        "0.2.2": [],
    }
    for vault in data:
        vaults[vault["apiVersion"]].append(vault)

    return vaults

    for i, release in enumerate(releases[::-1]):
        deltas[release.apiVersion()] = i
    vaultsAddresses = {}
    for version in VERSIONS:
        toAdd = []
        for v in vaults[version]:
            if legacy_registry.isRegistered(v["token"]["id"]):
                for n in range(legacy_registry.numVaults(v["token"]["id"])):
                    if (
                        legacy_registry.vaults(v["token"]["id"], n).lower()
                        == v["id"].lower()
                    ):
                        toAdd.append(v["id"])
        vaultsAddresses[version] = toAdd

    for version in VERSIONS:
        if len(vaultsAddresses[version]) > 0:
            vault_registry.batchEndorseVault(
                vaultsAddresses[version], deltas[version], 0, {"from": account}
            )