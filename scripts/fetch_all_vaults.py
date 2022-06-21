import requests

# pretty print is used to print the output in the console in an easy to read format
from pprint import pprint


# function to use requests.post to make an API call to the subgraph url
def run_query(q):

    # endpoint where you are making the request
    request = requests.post(
        "https://gateway.thegraph.com/api/b512f1f71e67d50f59e7563496d8e530/subgraphs/id/5xMSe3wTNLgFQqsAc5SCVVwT4MiRb5AogJCuSN9PjzXF"
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


def blacklist():
    blacklist = [
        "0x5737022626c282a89d105fd2e89ed6928ebdae93",
        "0x5b189d92983e941273b26e3b46e5a16206c08827",
        "0x71955515adf20cbdc699b8bc556fc7fd726b31b0",
        "0xf4fdbc7c66dc9832d672ffe6242b6a386cead5de",
        "0x662fbf2c1e4b04342eeba6371ec1c7420042b86f",
        "0x19b8bc5ccf9700e16f2780bea152f01c449f45d0",
        "0xfe8a3837cff919c800bdc5d1ac6136f84497d679",
        "0x0ff3773a6984ad900f7fb23a9acbf07ac3adfb06",
        "0x722f76f34cb5c3b008a50e0664e55a53f4f461ab",
        "0x3408324dbb537886cadc180f6ffcf674ee215f67",
        "0x5b707472eef1553646740a7e5becfd41b9b4ef4c",
        "0x8b58aa42a4aa222b684078459ce03dd0a43342b1",
        "0x846e211e8ba920b353fb717631c015cf04061cc9",
        "0x1f6bdffbadd98e410f83c66d1278241375f5199f",
        "0x3c26de7e22613a31b77e93f011d804d8a7821581",
        "0x416ebadc07cc7efa94d9110a5b932089bbd49931",
        "0x4c4a6a22bce915c724a66b82128577f1b24831ed",
        "0x63859212aa05d60295a2f18a9e0c707040605bad"
        "0x6aefd381c0aef49baaff58ebc70534b3941c61bf",
        "0x902cf5373317bb3e42660e9f4e85aa21532c0e44",
    ]
    return [entry.lower() for entry in blacklist]


def fetch_data():
    result = run_query(query)
    # print('Print Result - {}'.format(result))
    # print('#############')
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
