from nis import cat
import pytest
from web3 import Web3

from ape import project, Contract
import sys

sys.path.append("..")
from scripts.fetch_all_vaults import *
from scripts.deploy import *

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
    initialize_vaults(gov, release_registry, vault_registry, legacy_registry, vaults)