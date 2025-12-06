const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying Anchor contract to Sepolia...");

  const [deployer] = await hre.ethers.getSigners();
  console.log("📝 Deploying with account:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Account balance:", hre.ethers.formatEther(balance), "ETH");

  if (balance === 0n) {
    console.error("❌ No ETH! Get from: https://sepoliafaucet.com/");
    process.exit(1);
  }

  const Anchor = await hre.ethers.getContractFactory("Anchor");
  const anchor = await Anchor.deploy();
  await anchor.waitForDeployment();

  const contractAddress = await anchor.getAddress();

  console.log("✅ Contract deployed!");
  console.log("📍 Address:", contractAddress);
  console.log("🔍 Etherscan:", `https://sepolia.etherscan.io/address/${contractAddress}`);
  console.log("\n📋 Add to .env:");
  console.log(`CONTRACT_ADDRESS=${contractAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });