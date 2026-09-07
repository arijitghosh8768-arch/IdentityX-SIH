import { expect } from "chai";
import hre from "hardhat";

describe("AuditTrail", function () {
  let auditTrail;
  let owner;
  let addr1;

  beforeEach(async function () {
    [owner, addr1] = await hre.ethers.getSigners();
    const AuditTrail = await hre.ethers.getContractFactory("AuditTrail");
    auditTrail = await AuditTrail.deploy();
  });

  it("Should log a report successfully", async function () {
    const reportId = "REP123";
    const docHash = "0x123456789abcdef";
    const reportHash = "0x987654321fedcba";

    await expect(auditTrail.logReport(reportId, docHash, reportHash))
      .to.emit(auditTrail, "ReportLogged");

    const log = await auditTrail.auditLogs(reportId);
    expect(log.reportId).to.equal(reportId);
    expect(log.documentHash).to.equal(docHash);
    expect(log.reportHash).to.equal(reportHash);
    expect(log.officerAddress).to.equal(owner.address);
  });

  it("Should fail if reportId is already logged", async function () {
    const reportId = "REP123";
    const docHash = "0x123456789abcdef";
    const reportHash = "0x987654321fedcba";

    await auditTrail.logReport(reportId, docHash, reportHash);
    await expect(
      auditTrail.logReport(reportId, docHash, reportHash)
    ).to.be.revertedWith("Report already logged!");
  });

  it("Should verify a matching report hash", async function () {
    const reportId = "REP123";
    const docHash = "0x123456789abcdef";
    const reportHash = "0x987654321fedcba";

    await auditTrail.logReport(reportId, docHash, reportHash);
    const isVerified = await auditTrail.verifyReport(reportId, reportHash);
    expect(isVerified).to.be.true;

    const isWrongVerified = await auditTrail.verifyReport(reportId, "0xwrong");
    expect(isWrongVerified).to.be.false;
  });

  it("Should revert verification if reportId is not found", async function () {
    await expect(
      auditTrail.verifyReport("NONEXISTENT", "0x123")
    ).to.be.revertedWith("Report not found");
  });
});
