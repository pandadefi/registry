import { Wallet } from "zksync-web3";
import { HardhatRuntimeEnvironment } from "hardhat/types";
import { Deployer } from "@matterlabs/hardhat-zksync-deploy";

// An example of a deploy script that will deploy.
export default async function (hre: HardhatRuntimeEnvironment) {
  console.log(`Running deploy script for registries`);

  // Initialize the wallet.
  const wallet = new Wallet("");

  // Create deployer object and load the artifact of the contract we want to deploy.
  const deployer = new Deployer(hre, wallet);
  const rr = await deployer.loadArtifact("ReleaseRegistry");
  const vr = await deployer.loadArtifact("VaultRegistry");

  // Deploy this contract. The returned object will be of a `Contract` type, similarly to ones in `ethers`.
  // `greeting` is an argument for contract constructor.
  const releaseRegistryContract = await deployer.deploy(rr);
  const vaultRegistryContract = await deployer.deploy(vr, [releaseRegistryContract.address]);

  // Show the contract info.
  const rrAddress = releaseRegistryContract.address;
  console.log(`${rr.contractName} was deployed to ${rrAddress}`);

  const vrAddress = vaultRegistryContract.address;
  console.log(`${vr.contractName} was deployed to ${vrAddress}`);

}
