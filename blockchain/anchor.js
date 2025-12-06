const { ethers } = require('ethers');

const ANCHOR_ABI = [
    "function anchor(bytes32 hash) external returns (uint256 timestamp)",
    "function isAnchored(bytes32 hash) external view returns (bool exists, uint256 timestamp, address anchorer)",
    "event Anchored(bytes32 indexed hash, uint256 timestamp, address indexed anchorer)"
];

async function anchorHash(dossierHash, contractAddress, privateKey, rpcUrl) {
    try {
        console.error(`📡 Connecting to Sepolia...`);
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        const wallet = new ethers.Wallet(privateKey, provider);
        const contract = new ethers.Contract(contractAddress, ANCHOR_ABI, wallet);
        
        // Format hash
        let hashBytes32;
        if (dossierHash.startsWith('0x')) {
            hashBytes32 = dossierHash;
        } else {
            hashBytes32 = '0x' + dossierHash.padStart(64, '0');
        }
        
        console.error(`🔍 Checking if already anchored...`);
        const [exists] = await contract.isAnchored(hashBytes32);
        if (exists) {
            throw new Error('Hash already anchored');
        }
        
        console.error(`📤 Sending transaction...`);
        const tx = await contract.anchor(hashBytes32);
        
        console.error(`⏳ Waiting for confirmation: ${tx.hash}`);
        const receipt = await tx.wait(1);
        
        if (receipt.status === 0) {
            throw new Error('Transaction failed');
        }
        
        console.error(`✅ Confirmed in block ${receipt.blockNumber}`);
        
        const result = {
            success: true,
            tx_hash: receipt.hash,
            block_number: receipt.blockNumber,
            timestamp: Math.floor(Date.now() / 1000),
            gas_used: receipt.gasUsed.toString(),
            explorer_url: `https://sepolia.etherscan.io/tx/${receipt.hash}`
        };
        
        console.log(JSON.stringify(result));
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log(JSON.stringify({ success: false, error: error.message }));
        process.exit(1);
    }
}

if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length < 4) {
        console.error('Usage: node anchor.js <hash> <contract> <private_key> <rpc_url>');
        process.exit(1);
    }
    anchorHash(args[0], args[1], args[2], args[3]);
}

module.exports = { anchorHash };