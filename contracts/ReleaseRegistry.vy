# @version 0.3.7

interface Vault:
    def token() -> address: view
    def apiVersion() -> String[28]: view
    def governance() -> address: view
    def initialize(
        token: address,
        governance: address,
        rewards: address,
        name: String[64],
        symbol: String[32],
        guardian: address,
    ): nonpayable

governance: public(address)
numReleases: public(uint256)
releases: public(HashMap[uint256, address])

event NewRelease:
    release_id: indexed(uint256)
    template: address
    api_version: String[28]

event NewClone:
    vault: indexed(address)


@view
@external
def latestRelease() -> String[28]:
    """
    @notice Returns the api version of the latest release.
    @dev Throws if no releases are registered yet.
    @return The api version of the latest release.
    NOTE: Throws if there has not been a release yet
    """
    return Vault(self.releases[self.numReleases - 1]).apiVersion()  # dev: no release



@external
def newRelease(vault: address):
    """
    @notice
        Add a previously deployed Vault as the template contract for the latest release,
        to be used by further "forwarder-style" delegatecall proxy contracts that can be
        deployed from the registry throw other methods (to save gas).
    @dev
        Throws if caller isn't `governance`.
        Throws if `vault`'s governance isn't `governance`.
        Throws if the api version is the same as the previous release.
        Emits a `NewVault` event.
    @param vault The vault that will be used as the template contract for the next release.
    """
    assert msg.sender == self.governance #dev: not allowed
    # Check if the release is different from the current one
    # NOTE: This doesn't check for strict semver-style linearly increasing release versions

    release_id: uint256 = self.numReleases # Next id in series
    if release_id > 0:
        assert (
            Vault(self.releases[release_id - 1]).apiVersion()
            != Vault(vault).apiVersion()
        ) # dev: same api version
        # Update latest release
    self.releases[release_id] = vault
    self.numReleases = release_id + 1

        
    # Log the release for external listeners (e.g. Graph)
    log NewRelease(release_id, vault, Vault(vault).apiVersion())

@internal
def _newProxyVault(
    token: address,
    governance: address,
    rewards: address,
    guardian: address,
    name: String[64],
    symbol: String[32],
    releaseTarget: uint256,
) -> address:
    release: address = self.releases[releaseTarget]
    assert release != ZERO_ADDRESS  # dev: unknown release
    vault: address = create_forwarder_to(release)

    # NOTE: Must initialize the Vault atomically with deploying it
    Vault(vault).initialize(token, governance, rewards, name, symbol, guardian)

    return vault

@external
def newVault(
    token: address,
    governance: address,
    guardian: address,
    rewards: address,
    name: String[64],
    symbol: String[32],
    releaseDelta: uint256 = 0,  # NOTE: Uses latest by default
    ) -> address:
    """
    @notice
        Create a new vault for the given token using the latest release in the registry,
        as a simple "forwarder-style" delegatecall proxy to the latest release.
    @dev
        `governance` is set in the new vault as `self.governance`, with no ability to override.
        Throws if caller isn't `self.governance`.
        Throws if no releases are registered yet.
        Throws if there already is a registered vault for the given token with the latest api version.
        Emits a `NewVault` event.
    @param token The token that may be deposited into the new Vault.
    @param governance vault governance
    @param guardian The address authorized for guardian interactions in the new Vault.
    @param rewards The address to use for collecting rewards in the new Vault
    @param name Specify a custom Vault name. Set to empty string for default choice.
    @param symbol Specify a custom Vault symbol name. Set to empty string for default choice.
    @param releaseDelta Specify the number of releases prior to the latest to use as a target. Default is latest.
    @return The address of the newly-deployed vault
    """
    # NOTE: Underflow if no releases created yet, or targeting prior to release history
    releaseTarget: uint256 = self.numReleases - 1 - releaseDelta  # dev: no releases
    vault: address = self._newProxyVault(token, governance, rewards, guardian, name, symbol, releaseTarget)

    return vault
