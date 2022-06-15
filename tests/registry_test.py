import pytest
from ape import chain, project
import ape


def test_version_mutch_match(legacy_registry, release_registry):
    legacy_n_releases = legacy_registry.numReleases()
    n_releases = release_registry.numReleases()
    assert legacy_n_releases == n_releases

    for i in range(n_releases):
        assert legacy_registry.releases(i) == release_registry.releases(i)


def test_create_new_vault(vault_registry, token, gov):
    vault_registry.setRole(gov, True, True, sender=gov)
    vault_registry.setApprovedVaultsOwner(gov, True, sender=gov)
    vault_registry.newVault(token, gov, gov, gov, "test", "test", 0, 0, sender=gov)


def test_create_new_vault_fail_not_allowed(vault_registry, token, gov, rando):
    with ape.reverts("unauthorized"):
        vault_registry.newVault(
            token, gov, gov, gov, "test", "test", 0, 0, sender=rando
        )


def test_create_new_vault_fail_not_allowed_vault_owner(
    vault_registry, token, gov, rando
):
    vault_registry.setRole(gov, True, True, sender=gov)
    with ape.reverts("not allowed vault owner"):
        vault_registry.newVault(
            token, rando, gov, gov, "test", "test", 0, 0, sender=gov
        )


def test_create_different_types(vault_registry, token, gov, project):
    Vault = project.dependencies["vault"]["0.4.3"].Vault
    vault_registry.setRole(gov, True, True, sender=gov)
    vault_registry.setApprovedVaultsOwner(gov, True, sender=gov)
    vault_registry.newVault(
        token, gov, gov, gov, "test default", "test default", 0, 0, sender=gov
    )
    vault_registry.newVault(
        token, gov, gov, gov, "test FT", "test FT", 0, 1, sender=gov
    )
    vault_registry.newVault(
        token, gov, gov, gov, "test experimental", "test experimental", 0, 2, sender=gov
    )
    assert vault_registry.latestVault(token) == vault_registry.latestVault(token, 0)

    assert Vault.at(vault_registry.latestVault(token, 0)).name() == "test default"
    assert Vault.at(vault_registry.latestVault(token, 1)).name() == "test FT"
    assert Vault.at(vault_registry.latestVault(token, 2)).name() == "test experimental"

    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test default", "test default", 0, 0, sender=gov
        )
    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test FT", "test FT", 0, 1, sender=gov
        )
    with ape.reverts():
        vault_registry.newVault(
            token, gov, gov, gov, "test experimental", "test experimental", 0, 2, sender=gov
        )
