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

interface IReleaseRegistry:
    def numReleases() -> uint256: view
    def releases(version: uint256) -> address: view
    def newVault(
        token: address,
        governance: address,
        guardian: address,
        rewards: address,
        name: String[64],
        symbol: String[32],
        releaseDelta: uint256
    ) -> address: nonpayable

DEFAULT_TYPE: constant(uint256) = 1
LEGACY_REGISTRY: immutable(address)

releaseRegistry: public(address)
# token => vaults
vaults: public(HashMap[address, DynArray[address, 256]])
tokens: public(DynArray[address, 2048])
# Inclusion check for token
isRegistered: public(HashMap[address, bool])
# Vault -> type of the vault
vaultType: public(HashMap[address, uint256])
approvedVaultsGovernance: public(HashMap[address, bool])
isVaultEndorsed: public(HashMap[address, bool])
vaultEndorsers: public(HashMap[address, bool])
governance: public(address)
pendingGovernance: public(address)

event NewVault:
    token: indexed(address)
    vault_id: indexed(uint256)
    vault_type: uint256
    vault: address
    api_version: String[28]


event ApprovedVaultGovernanceUpdated:
    governance: address
    approved: bool

event ApprovedVaultEndorser:
    account: address
    can_endorse: bool

event ReleaseRegistryUpdated:
    new_registry: address

event UpdateGovernance:
    governance: address # New active governance

event NewPendingGovernance:
    pendingGovernance: indexed(address)

@external
def __init__(releaseRegistry: address, legacyRegistry: address):
    self.governance = msg.sender
    self.releaseRegistry = releaseRegistry
    LEGACY_REGISTRY = legacyRegistry
    log ReleaseRegistryUpdated(releaseRegistry)


@external
@view
def numTokens() -> uint256:
        return len(self.tokens)

@internal
@view 
def _numVaults(token: address) -> uint256:
    return len(self.vaults[token])

@external
@view 
def numVaults(token: address) -> uint256:
    return self._numVaults(token)

@internal
@view
def _latestVault(token: address) -> address:
    length: uint256 = self._numVaults(token)
    if length == 0:
        return self._fetchFromLegacy(token)
    return self.vaults[token][length - 1]
    
@internal
@view
def _latestVaultOfType(token: address, type: uint256) -> address:
    length: uint256 = self._numVaults(token)
    if length == 0:
        return empty(address)

    for i in range(256):
        if i == length:
            break
        vault: address = self.vaults[token][length - i - 1]
        if self.vaultType[vault] == type:
            return vault
    
    return empty(address)

@internal
@view
def _fetchFromLegacy(token: address) -> address:
    success: bool = False
    response: Bytes[32] = b""

    success, response = raw_call(
        LEGACY_REGISTRY,
        concat(
            method_id("latestVault(address)"),
            convert(token, bytes32),
        ),
        max_outsize=32,
        is_static_call=True,
        revert_on_failure=False
        )

    if success:
        return convert(response, address)
    return empty(address)

@external
@view
def latestVault(token: address) -> address:
    """
    @notice Returns the latest deployed vault for the given token.
    @dev Return zero if no vault is associated with the token
    @param token The token address to find the latest vault for.
    @return The address of the latest vault for the given token.
    """
    return self._latestVault(token)


@external
@view
def latestVaultOfType(token: address, type: uint256) -> address:
    """
    @notice Returns the latest deployed vault for the given token and type.
    @dev Return zero if no vault exists for both token and type.
    @param token The token address to find the latest vault for.
    @param type The vault type to find the latest vault for.
    @return The address of the latest vault found matching both token and type.
    """
    return self._latestVaultOfType(token, type)

@internal
def _registerVault(token: address, vault: address, type: uint256):
    # Check if there is an existing deployment for this token + type combination at the particular api version
    # NOTE: This doesn't check for strict semver-style linearly increasing release versions
    assert self.vaultType[vault] == 0 # dev: VaultAlreadyEndorsed
    assert type != 0 #dev: InvalidVaultType


    latest: address = self._latestVaultOfType(token, type)
    if latest != empty(address):
        assert (
            Vault(latest).apiVersion()
            != Vault(vault).apiVersion()
        )  # dev: same api version


    vault_id: uint256 = self._numVaults(token)
    # Update the latest deployment

    self.vaults[token].append(vault)
    self.vaultType[vault] = type

    # Register tokens for endorsed vaults
    if self.isRegistered[token] == False:
        self.isRegistered[token] = True
        self.tokens.append(token)
    
    self.isVaultEndorsed[vault] = True
    log NewVault(token, vault_id, type, vault, Vault(vault).apiVersion())

@external
def _endorseVault(vault: address, releaseDelta: uint256 = 0, type: uint256 = DEFAULT_TYPE):
    """
    @notice
         Adds an existing vault to the list of "endorsed" vaults for that token.
    @dev
         `governance` is set in the new vault as `governance`, with no ability to override.
         Throws if caller isn't `governance`.
         Throws if `vault`'s governance isn't `governance`.
         Throws if no releases are registered yet.
         Throws if `vault`'s api version does not match latest release.
         Throws if there already is a deployment for the vault's token with the latest api version.
         Emits a `NewVault` event.
    @param vault The vault that will be endorsed by the Registry.
    @param releaseDelta Specify the number of releases prior to the latest to use as a target. DEFAULT_TYPE is latest.
    @param type Vault type
    """
    assert self.vaultEndorsers[msg.sender] #dev: NotAllowedToEndorse
    assert self.approvedVaultsGovernance[Vault(vault).governance()] #dev: GovernanceMismatch

    # NOTE: Underflow if no releases created yet, or targeting prior to release history

    releaseTarget: uint256 = IReleaseRegistry(self.releaseRegistry).numReleases() - 1 - releaseDelta # dev: no releases

    api_version: String[28] = Vault(IReleaseRegistry(self.releaseRegistry).releases(releaseTarget)).apiVersion()

    assert Vault(vault).apiVersion() == api_version  # dev: VersionMissmatch   
    # Add to the end of the list of vaults for token
    self._registerVault(Vault(vault).token(), vault, type)

@external
def newVault(
token: address,
governance: address,
guardian: address,
rewards: address,
name: String[64],
symbol: String[32],
releaseDelta: uint256 = 0, # NOTE: Uses latest by default
type: uint256 = DEFAULT_TYPE
) -> address:
    """
    @notice
        Create a new vault for the given token using the latest release in the registry,
        as a simple "forwarder-style" delegatecall proxy to the latest release.
    @dev
        `governance` is set in the new vault as `governance`, with no ability to override.
        Throws if caller isn't `governance`.
        Throws if no releases are registered yet.
        Throws if there already is a registered vault for the given token with the latest api version.
        Emits a `NewVault` event.
    @param token The token that may be deposited into the new Vault.
    @param governance vault governance
    @param guardian The address authorized for guardian interactions in the new Vault.
    @param rewards The address to use for collecting rewards in the new Vault
    @param name Specify a custom Vault name. Set to empty string for DEFAULT_TYPE choice.
    @param symbol Specify a custom Vault symbol name. Set to empty string for DEFAULT_TYPE choice.
    @param releaseDelta Specify the number of releases prior to the latest to use as a target. DEFAULT_TYPE is latest.
    @param type Vault type
    @return The address of the newly-deployed vault
    """

    assert self.vaultEndorsers[msg.sender] #dev: NotAllowedToEndorse
    assert self.approvedVaultsGovernance[governance] #dev: GovernanceMismatch
    vault: address = IReleaseRegistry(self.releaseRegistry).newVault(
    token,
    governance,
    guardian,
    rewards,
    name,
    symbol,
    releaseDelta
    )
    self._registerVault(token, vault, type)
    return vault

@external

def setVaultEndorsers(addr: address, approved: bool):
    """
    @notice Set the ability of a particular tagger to tag current vaults.
    @dev Throws if caller is not `governance`.
    @param addr The address to approve or deny access.
    @param approved Allowed to endorse
    """
    assert msg.sender == self.governance
    self.vaultEndorsers[addr] = approved
    log ApprovedVaultEndorser(addr, approved)


@external
def setApprovedVaultsGovernance(addr: address, approved: bool):
    """
    @notice Set the vaults governances
    @dev Throws if caller is not `governance`.
    @param addr The address to approve or deny access.
    @param approved Allowed to own vault
    """
    assert msg.sender == self.governance
    self.approvedVaultsGovernance[addr] = approved
    log ApprovedVaultGovernanceUpdated(addr, approved)
    
@external
def updateReleaseRegistry(newRegistry: address):
    assert msg.sender == self.governance
    self.releaseRegistry = newRegistry
    log ReleaseRegistryUpdated(newRegistry)


# 2-phase commit for a change in governance
@external
def setGovernance(governance: address):
    """
    @notice
        Nominate a new address to use as governance.

        The change does not go into effect immediately. This function sets a
        pending change, and the governance address is not updated until
        the proposed governance address has accepted the responsibility.

        This may only be called by the current governance address.
    @param governance The address requested to take over Vault governance.
    """
    assert msg.sender == self.governance
    log NewPendingGovernance(governance)
    self.pendingGovernance = governance


@external
def acceptGovernance():
    """
    @notice
        Once a new governance address has been proposed using setGovernance(),
        this function may be called by the proposed address to accept the
        responsibility of taking over governance for this contract.

        This may only be called by the proposed governance address.
    @dev
        setGovernance() should be called by the existing governance address,
        prior to calling this function.
    """
    assert msg.sender == self.pendingGovernance
    self.governance = msg.sender
    log UpdateGovernance(msg.sender)