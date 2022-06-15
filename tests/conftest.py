from nis import cat
import pytest
from web3 import Web3

from ape import project, Contract
import sys

sys.path.append("..")
from scripts.fetch_all_vaults import *

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
VERSIONS = [
    "0.2.2",
    "0.3.0",
    "0.3.1",
    "0.3.2",
    "0.3.3",
    "0.3.4",
    "0.3.5",
    "0.4.1",
    "0.4.2",
    "0.4.3",
]


@pytest.fixture(scope="session")
def legacy_registry():
    yield Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")


@pytest.fixture(scope="session")
def gov(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def rando(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def panda(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def fish(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def release_registry(gov, project):
    release_registry = gov.deploy(project.ReleaseRegistry)
    proxy = gov.deploy(
        project.dependencies["openzeppelin"]["4.6.0"].ERC1967Proxy,
        release_registry,
        b"",
    )
    yield project.ReleaseRegistry.at(proxy.address)


@pytest.fixture(scope="session")
def vault_registry(gov, project):
    vault_registry = gov.deploy(project.VaultRegistry)
    proxy = gov.deploy(
        project.dependencies["openzeppelin"]["4.6.0"].ERC1967Proxy, vault_registry, b""
    )
    yield project.VaultRegistry.at(proxy.address)


@pytest.fixture(scope="session")
def data():
    yield fetch_data()


@pytest.fixture(scope="session")
def vaults(data):
    yield order_vaults(data)


@pytest.fixture()
def token(gov, project):
    yield gov.deploy(project.Token, "test")


@pytest.fixture(scope="session", autouse=True)
def initialize(gov, release_registry, vault_registry, legacy_registry, vaults):
    vault_registry.initialize(release_registry, sender=gov)
    vault_registry.setApprovedVaultsOwner(
        "0xfeb4acf3df3cdea7399794d0869ef76a6efaff52", True, sender=gov
    )

    release_registry.initialize(vault_registry, sender=gov)

    releases = []
    n_releases = legacy_registry.numReleases()
    for i in range(n_releases):
        releases.append(Contract(legacy_registry.releases(i)))
    for release in releases:
        release_registry.newRelease(release, sender=gov)
    deltas = {}

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
        try:
            vault_registry.batchEndorseVault(
                vaultsAddresses[version], deltas[version], 0, sender=gov
            )
        except Exception as e:
            print("FAIL: ", vaultsAddresses[version])
            for v in vaultsAddresses[version]:
                try:
                    vault_registry.batchEndorseVault(
                        [v], deltas[version], 0, sender=gov
                    )
                except Exception as e:
                    print(v["id"])
                    v = Contract(Web3.toChecksumAddress(v))
                    token = v.token()
                    print(v.apiVersion())
                    print("owner: ", v.governance())
                    print("token: ", token)
                    try:
                        print("latestVault: ", vault_registry.latestVault(token))
                    except Exception as e:
                        print("latestVault: None")
                    print("====================")
