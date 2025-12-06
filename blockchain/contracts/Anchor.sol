// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Anchor {
    event Anchored(bytes32 indexed hash, uint256 timestamp, address indexed anchorer);

    struct AnchorRecord {
        uint256 timestamp;
        address anchorer;
        bool exists;
    }

    mapping(bytes32 => AnchorRecord) public anchors;

    function anchor(bytes32 hash) external returns (uint256 timestamp) {
        require(!anchors[hash].exists, "Hash already anchored");
        require(hash != bytes32(0), "Invalid hash");

        timestamp = block.timestamp;

        anchors[hash] = AnchorRecord({
            timestamp: timestamp,
            anchorer: msg.sender,
            exists: true
        });

        emit Anchored(hash, timestamp, msg.sender);
        return timestamp;
    }

    function isAnchored(bytes32 hash) 
        external 
        view 
        returns (bool exists, uint256 timestamp, address anchorer) 
    {
        AnchorRecord memory record = anchors[hash];
        return (record.exists, record.timestamp, record.anchorer);
    }
}