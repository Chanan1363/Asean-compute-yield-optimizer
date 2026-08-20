// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

// ═══════════════════════════════════════════════════════════════════════
// ASEAN Grid — RevenueSplit (Interface Stub)
// Smart contract สำหรับจัดสรรรายได้ 75/20/5 — ตรรกะต้องตรงกับ
// prototype/core/revenue_split.py 100% (Core ยืนยันจากภาพ 18 ส.ค. 2026)
//
// สถานะ: INTERFACE ONLY — Dev เขียน implementation จริง
// (ดู prototype/ai/prompts/agents.md ข้อ 3 สำหรับ spec เต็ม)
// ═══════════════════════════════════════════════════════════════════════

interface IRevenueSplit {
    /// ผู้รับทั้ง 3 กอง — อัปเดตได้เฉพาะผ่าน multi-sig
    struct Recipients {
        address nodeProviderPayout;    // 75% — จ่ายรายวัน (batch)
        address platformOps;           // 20%
        address developerPool;         // 5% — claimable โดย contributor ที่ verify
    }

    event SplitExecuted(
        uint256 indexed blockNumber,
        uint256 totalUsd,
        uint256 nodeShare,
        uint256 platformShare,
        uint256 developerShare
    );
    event PayoutBatch(uint256 indexed batchId, address[] nodes, uint256[] amountsUsd);

    /// รับ USDT เข้าระบบ แล้วแบ่ง 75/20/5 ทันที (ต่อยอด: batch ต่อวัน)
    function executeSplit(uint256 amountUsd) external returns (bool);

    /// จ่ายรายวันให้ผู้ให้เครื่อง (75%) — ต้องตรงกับ ledger ของ off-chain
    function batchPayout(address[] calldata nodes, uint256[] calldata amountsUsd)
        external returns (uint256 batchId);

    /// นักพัฒนาที่ผ่านการยืนยัน (PR merged) เรียกถอนจากกอง 5%
    function claimDeveloperReward(address developer, uint256 amountUsd) external returns (bool);

    /// สัดส่วน 75/20/5 เป็น immutable — ไม่มีฟังก์ชันแก้ (core ของตาย)
    function NODE_SHARE() external view returns (uint256);      // 7500 (basis points)
    function PLATFORM_SHARE() external view returns (uint256);  // 2000
    function DEVELOPER_SHARE() external view returns (uint256); // 500
}
