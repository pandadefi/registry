from nis import cat
import pytest
from web3 import Web3

from ape import project, Contract
import sys

sys.path.append("..")
from scripts.deploy import *


@pytest.fixture(scope="session")
def legacy_registry():
    yield Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")


@pytest.fixture(scope="session")
def dai():
    yield Contract("0x6b175474e89094c44da98b954eedeac495271d0f")


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
def release_registry(gov, project, legacy_registry):
    release_registry = gov.deploy(project.ReleaseRegistry)
    init_release_registry(legacy_registry, release_registry, gov)
    yield release_registry


@pytest.fixture(scope="session")
def vault_registry(gov, project, release_registry, legacy_registry):
    yield gov.deploy(project.VaultRegistry, release_registry, legacy_registry)


@pytest.fixture()
def token(gov, project):
    yield gov.deploy(project.Token, "test")
