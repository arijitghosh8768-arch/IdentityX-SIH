import { expect } from "chai";
import hre from "hardhat";
import { hashFile, hashReport } from "../hash.js";
import { storeVerification, getVerification } from "../blockchain.js";

describe("Ethers.js Blockchain & Hash Integration", function () {
  let auditTrail;
  let owner;

  beforeEach(async function () {
    [owner] = await hre.ethers.getSigners();
    const AuditTrail = await hre.ethers.getContractFactory("AuditTrail");
    auditTrail = await AuditTrail.deploy();
    await auditTrail.waitForDeployment();
  });

  it("Should correctly hash files and reports", function () {
    const fileBuffer = Buffer.from("Sample Document Content");
    const reportObj = { name: "John Doe", riskScore: 5 };

    const fileHash = hashFile(fileBuffer);
    const reportHash = hashReport(reportObj);

    expect(fileHash.startsWith("0x")).to.be.true;
    expect(reportHash.startsWith("0x")).to.be.true;
  });

  it("Should store and retrieve verification via blockchain.js", async function () {
    const deployedAddress = await auditTrail.getAddress();
    const fileBuffer = Buffer.from("Test Document");
    const reportObj = { name: "Alice", docType: "Passport" };

    const reportId = "REP-999";
    const docHash = hashFile(fileBuffer);
    const repHash = hashReport(reportObj);

    const receipt = await storeVerification(owner, reportId, docHash, repHash, deployedAddress);
    expect(receipt.status).to.equal(1);

    const verification = await getVerification(owner, reportId, deployedAddress);
    expect(verification.reportId).to.equal(reportId);
    expect(verification.documentHash).to.equal(docHash);
    expect(verification.reportHash).to.equal(repHash);
    expect(verification.officerAddress).to.equal(owner.address);
  });
});
