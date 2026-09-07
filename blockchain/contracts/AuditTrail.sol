// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title IdentityX Audit Trail
 * @dev Stores immutable verification report hashes on the blockchain
 */
contract AuditTrail {
    
    struct LogEntry {
        uint256 timestamp;
        string reportId;
        string documentHash;
        string reportHash;
        address officerAddress;
    }
    
    // Mapping from reportId to the LogEntry
    mapping(string => LogEntry) public auditLogs;
    
    // Event emitted when a new report is logged
    event ReportLogged(
        string indexed reportId,
        string documentHash,
        string reportHash,
        uint256 timestamp
    );
    
    /**
     * @dev Log a new verification report hash to the blockchain
     */
    function logReport(
        string memory _reportId, 
        string memory _documentHash, 
        string memory _reportHash
    ) public {
        // Ensure this report ID hasn't been logged already
        require(auditLogs[_reportId].timestamp == 0, "Report already logged!");
        
        LogEntry memory newLog = LogEntry({
            timestamp: block.timestamp,
            reportId: _reportId,
            documentHash: _documentHash,
            reportHash: _reportHash,
            officerAddress: msg.sender
        });
        
        auditLogs[_reportId] = newLog;
        
        emit ReportLogged(_reportId, _documentHash, _reportHash, block.timestamp);
    }
    
    /**
     * @dev Verify if a report hash exists and matches
     */
    function verifyReport(string memory _reportId, string memory _reportHash) public view returns (bool) {
        require(auditLogs[_reportId].timestamp != 0, "Report not found");
        
        // Compare the stored hash with the provided hash
        return (keccak256(abi.encodePacked(auditLogs[_reportId].reportHash)) == keccak256(abi.encodePacked(_reportHash)));
    }
}
