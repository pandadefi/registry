from pathlib import Path
from readline import append_history_file

import click
from ape import accounts, project, chain, Contract
from ape.cli import NetworkBoundCommand, network_option, account_option
from web3 import Web3
import sys

sys.path.append("..")
from scripts.fetch_all_vaults import *

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

@click.group(short_help="Deploy the project")
def cli():
    pass

@cli.command(cls=NetworkBoundCommand)
@network_option()
@account_option()
def main(network, account):
    gas = 0
    vault_registry = account.deploy(project.VaultRegistry)
    
    proxy = account.deploy(
        project.dependencies["openzeppelin"]["4.6.0"].ERC1967Proxy, vault_registry, b""
    )
    vault_registry = project.VaultRegistry.at(proxy.address)

    release_registry = account.deploy(project.ReleaseRegistry)
    proxy = account.deploy(
        project.dependencies["openzeppelin"]["4.6.0"].ERC1967Proxy,
        release_registry,
        b"",
    )
    release_registry = project.ReleaseRegistry.at(proxy.address)
    legacy_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")

    data = fetch_data()
    vaults = order_vaults(data)
    gas += initialize_vaults(account, release_registry, vault_registry, legacy_registry, vaults)

def initialize_vaults(account, release_registry, vault_registry, legacy_registry, vaults):
    gas = 0
    tx = vault_registry.initialize(release_registry, sender=account)
    gas +=tx.gas_used
    tx = vault_registry.setApprovedVaultsOwner(
        "0xfeb4acf3df3cdea7399794d0869ef76a6efaff52", True, sender=account
    )
    gas +=tx.gas_used
    tx = release_registry.initialize(vault_registry, sender=account)
    gas +=tx.gas_used

    releases = []
    n_releases = legacy_registry.numReleases()
    for i in range(n_releases):
        releases.append(Contract(legacy_registry.releases(i)))
    for release in releases:
        tx = release_registry.newRelease(release, sender=account)
        gas +=tx.gas_used
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
        tx = vault_registry.batchEndorseVault(
            vaultsAddresses[version], deltas[version], 0, sender=account
        )
        gas +=tx.gas_used
    return gas