import pytest
from ape import chain, project
import ape

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_version_mutch_match(legacy_registry, release_registry):
    legacy_n_releases = legacy_registry.numReleases()
    n_releases = release_registry.numReleases()
    assert legacy_n_releases == n_releases

    for i in range(n_releases):
        assert legacy_registry.releases(i) == release_registry.releases(i)


def test_create_new_vault(vault_registry, token, gov):
    vault_registry.setApprovedVaultsOwner(gov, True, sender=gov)
    vault_registry.setVaultEndorsers(gov, True, sender=gov)
    vault_registry.newVault(token, gov, gov, gov, "test", "test", 0, 1, sender=gov)


def test_create_new_vault_fail_not_allowed(vault_registry, token, gov, rando):
    with ape.reverts("unauthorized"):
        vault_registry.newVault(
            token, gov, gov, gov, "test", "test", 0, 0, sender=rando
        )


def test_create_new_vault_fail_not_allowed_vault_owner(
    vault_registry, token, gov, rando
):
    vault_registry.setVaultEndorsers(gov, True, sender=gov)
    with ape.reverts("not allowed vault owner"):
        vault_registry.newVault(
            token, rando, gov, gov, "test", "test", 0, 1, sender=gov
        )


def test_create_different_types(vault_registry, token, gov, project):
    Vault = project.dependencies["vault"]["0.4.3"].Vault
    vault_registry.setApprovedVaultsOwner(gov, True, sender=gov)
    vault_registry.setVaultEndorsers(gov, True, sender=gov)
    vault_registry.newVault(
        token, gov, gov, gov, "test default", "test default", 0, 1, sender=gov
    )
    vault_registry.newVault(
        token, gov, gov, gov, "test Auto", "test Auto", 0, 2, sender=gov
    )
    vault_registry.newVault(
        token, gov, gov, gov, "test FT", "test FT", 0, 3, sender=gov
    )
    vault_registry.newVault(
        token, gov, gov, gov, "test experimental", "test experimental", 0, 4, sender=gov
    )
    assert vault_registry.latestVault(token) == vault_registry.latestVaultOfType(
        token, 4
    )

    assert Vault.at(vault_registry.latestVaultOfType(token, 1)).name() == "test default"
    assert Vault.at(vault_registry.latestVaultOfType(token, 2)).name() == "test Auto"
    assert Vault.at(vault_registry.latestVaultOfType(token, 3)).name() == "test FT"
    assert (
        Vault.at(vault_registry.latestVaultOfType(token, 4)).name()
        == "test experimental"
    )
    assert vault_registry.numVaults(token) == 4

    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test default", "test default", 0, 1, sender=gov
        )
    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test Auto", "test Auto", 0, 2, sender=gov
        )
    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test FT", "test FT", 0, 3, sender=gov
        )
    with ape.reverts():
        vault_registry.newVault(
            token,
            gov,
            gov,
            gov,
            "test experimental",
            "test experimental",
            0,
            4,
            sender=gov,
        )


def test_fetch_existing_dai_vault(vault_registry, legacy_registry, dai):
    assert vault_registry.latestVault(dai) == legacy_registry.latestVault(dai)


def test_do_not_throw_if_vault_do_not_exists(vault_registry, token):
    assert vault_registry.latestVault(token) == ZERO_ADDRESS
