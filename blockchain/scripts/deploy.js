import hre from "hardhat";

async function main() {
  const AuditTrail = await hre.ethers.getContractFactory("AuditTrail");
  const auditTrail = await AuditTrail.deploy();

  await auditTrail.waitForDeployment();

  const address = await auditTrail.getAddress();
  console.log(`AuditTrail deployed to: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
