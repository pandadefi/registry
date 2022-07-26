from pathlib import Path
from readline import append_history_file

import click
from ape import accounts, project, chain, Contract
from ape.cli import NetworkBoundCommand, network_option, account_option
from web3 import Web3
import sys

sys.path.append("..")


@click.group(short_help="Deploy the project")
def cli():
    pass


@cli.command(cls=NetworkBoundCommand)
@network_option()
@account_option()
def main(network, account):

    account.set_autosign(True, "panda")

    release_registry = account.deploy(project.ReleaseRegistry)
    legacy_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")
    vault_registry = account.deploy(
        project.VaultRegistry, release_registry, legacy_registry
    )

    click.echo("=======")
    click.echo(f"vault_registry: {vault_registry}")
    click.echo(f"release_registry: {release_registry}")
    click.echo("=======")


def init_release_registry(legacy_registry, release_registry, account):
    releases = []
    n_releases = legacy_registry.numReleases()
    for i in range(n_releases):
        releases.append(Contract(legacy_registry.releases(i)))

    for release in releases:
        release_registry.newRelease(release, sender=account)
