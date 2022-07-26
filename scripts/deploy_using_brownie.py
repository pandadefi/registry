from pathlib import Path
from brownie import config, project, accounts, Contract, VaultRegistry, ReleaseRegistry
import sys

sys.path.append("..")
from scripts.fetch_all_vaults import *


def main():
    account = accounts.load("deployer")

    release_registry = account.deploy(ReleaseRegistry)

    legacy_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")
    vault_registry = account.deploy(VaultRegistry, release_registry, legacy_registry)

    releases = []
    n_releases = legacy_registry.numReleases()
    for i in range(n_releases):
        releases.append(Contract(legacy_registry.releases(i)))

    for release in releases:
        tx = release_registry.newRelease(release, {"from": account})
