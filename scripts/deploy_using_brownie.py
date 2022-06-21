from pathlib import Path
from brownie import config, project, accounts, Contract, VaultRegistry, ReleaseRegistry
import sys

sys.path.append("..")
from scripts.fetch_all_vaults import *

oz = project.load(Path.home() / ".brownie" / "packages" / config["dependencies"][1])

VERSIONS = [
    # "0.2.2",
    # "0.3.0",
    # "0.3.1",
    # "0.3.2",
    # "0.3.3",
    # "0.3.4",
    # "0.3.5",
    # "0.4.0",
    "0.4.1",
    "0.4.2",
    "0.4.3",
]


def main():
    account = accounts.load("deployer")

    vault_registry = Contract.from_abi(
        "VaultRegistry", "0x78f73705105A63e06B932611643E0b210fAE93E9", VaultRegistry.abi
    )

    release_registry = Contract.from_abi(
        "ReleaseRegistry",
        "0xb2e69b79a9d3e0a4830369f6d3930ef7b8c5a295",
        ReleaseRegistry.abi,
    )

    legacy_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")

    data = fetch_data()
    vaults = order_vaults(data)
    initialize_vaults(
        account, release_registry, vault_registry, legacy_registry, vaults
    )


def initialize_vaults(
    account, release_registry, vault_registry, legacy_registry, vaults
):
    # gas = 0
    # tx = vault_registry.initialize(release_registry, {"from": account})
    # gas += tx.gas_used
    # tx = vault_registry.setApprovedVaultsOwner(
    #     "0xfeb4acf3df3cdea7399794d0869ef76a6efaff52", True, {"from": account}
    # )
    # gas += tx.gas_used
    # tx = release_registry.initialize(vault_registry, {"from": account})
    # gas += tx.gas_used

    releases = []
    n_releases = legacy_registry.numReleases()
    for i in range(n_releases):
        releases.append(Contract(legacy_registry.releases(i)))
    # for release in releases:
    #     tx = release_registry.newRelease(release, {"from": account})
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
        if len(vaultsAddresses[version]) > 0:
            vault_registry.batchEndorseVault(
                vaultsAddresses[version], deltas[version], 0, {"from": account}
            )
