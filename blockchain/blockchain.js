import { ethers } from 'ethers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read ABI from hardhat compilation artifact
const contractJsonPath = path.join(__dirname, 'artifacts', 'contracts', 'AuditTrail.sol', 'AuditTrail.json');
const contractArtifact = JSON.parse(fs.readFileSync(contractJsonPath, 'utf8'));

export const CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
export const CONTRACT_ABI = contractArtifact.abi;

/**
 * Returns an instance of the AuditTrail contract attached to the given signer or provider.
 */
export function getContractInstance(providerOrSigner, address = CONTRACT_ADDRESS) {
  return new ethers.Contract(address, CONTRACT_ABI, providerOrSigner);
}

/**
 * Stores a verification report hash on the blockchain.
 */
export async function storeVerification(signer, reportId, documentHash, reportHash, address = CONTRACT_ADDRESS) {
  const contract = getContractInstance(signer, address);
  const tx = await contract.logReport(reportId, documentHash, reportHash);
  const receipt = await tx.wait();
  return receipt;
}

/**
 * Retrieves a logged verification report from the blockchain.
 */
export async function getVerification(providerOrSigner, reportId, address = CONTRACT_ADDRESS) {
  const contract = getContractInstance(providerOrSigner, address);
  const log = await contract.auditLogs(reportId);
  return {
    timestamp: log.timestamp.toString(),
    reportId: log.reportId,
    documentHash: log.documentHash,
    reportHash: log.reportHash,
    officerAddress: log.officerAddress
  };
}
