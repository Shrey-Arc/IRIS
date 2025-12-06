require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: "../.env" });

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    sepolia: {
      url: process.env.HARDHAT_RPC_URL || "https://rpc.ankr.com/eth_sepolia",
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      chainId: 11155111
    }
  }
};