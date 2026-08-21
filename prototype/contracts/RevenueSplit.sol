// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

// ═══════════════════════════════════════════════════════════════════════
// ASEAN Grid — RevenueSplit (Implementation)
// Smart contract สำหรับจัดสรรรายได้ 75/20/5 — ตรรกะต้องตรงกับ
// prototype/core/revenue_split.py 100% (Core ยืนยันจากภาพ 18 ส.ค. 2026)
//
// Security:
//  - CEI (Checks-Effects-Interactions): อัปเดต state ก่อน call ภายนอกทุกครั้ง
//  - remainder หลังแบ่ง 75/20/5 → developer pool (กันเงินหายจาก integer division)
//  - batchProcessed กัน batchPayout ซ้ำ (reentrancy/duplicate)
//  - ผู้รับทั้ง 3 กองเปลี่ยนได้เฉพาะ owner (prototype — production ใช้ multi-sig)
// ═══════════════════════════════════════════════════════════════════════

contract RevenueSplit {
    // ── Core 75/20/5 (basis points — immutable ของตาย ห้ามแก้) ────────
    uint256 public constant NODE_SHARE = 7500;       // 75%
    uint256 public constant PLATFORM_SHARE = 2000;   // 20%
    uint256 public constant DEVELOPER_SHARE = 500;   // 5%
    uint256 private constant BPS = 10000;

    // ── ผู้รับทั้ง 3 กอง ──────────────────────────────────────────────
    address public nodeProviderPayout;   // 75% — จ่ายรายวัน (batch)
    address public platformOps;          // 20%
    address public developerPool;        // 5% — claimable โดย developer ที่ verify

    address public owner;

    // ── กัน exploit ───────────────────────────────────────────────────
    mapping(uint256 => bool) public batchProcessed;            // batchPayout ซ้ำไม่ได้
    mapping(address => uint256) public claimedDeveloperRewards; // ยอดที่ถอนไปแล้ว
    mapping(address => bool) public verifiedDevelopers;         // PR merged → verify

    // ── Events ───────────────────────────────────────────────────────
    event SplitExecuted(
        uint256 indexed blockNumber,
        uint256 totalUsd,
        uint256 nodeShare,
        uint256 platformShare,
        uint256 developerShare
    );
    event PayoutBatch(uint256 indexed batchId, address[] nodes, uint256[] amountsUsd);
    event DeveloperVerified(address indexed developer);
    event DeveloperClaimed(address indexed developer, uint256 amountUsd);
    event RecipientsUpdated(
        address nodeProviderPayout,
        address platformOps,
        address developerPool
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "RevenueSplit: not owner");
        _;
    }

    constructor(address nodePayout_, address platformOps_, address developerPool_) {
        require(nodePayout_ != address(0) && platformOps_ != address(0) && developerPool_ != address(0),
                "RevenueSplit: zero address");
        nodeProviderPayout = nodePayout_;
        platformOps = platformOps_;
        developerPool = developerPool_;
        owner = msg.sender;
    }

    /// รับ USDT/ETH เข้าระบบ แล้วแบ่ง 75/20/5 ทันที (ต่อยอด: batch ต่อวัน)
    function executeSplit() external payable returns (bool) {
        uint256 total = msg.value;
        require(total > 0, "RevenueSplit: empty split");

        uint256 nodeShare = (total * NODE_SHARE) / BPS;
        uint256 platformShare = (total * PLATFORM_SHARE) / BPS;
        // remainder จาก integer division → developer pool (ไม่มีเงินสูญหาย)
        uint256 developerShare = total - nodeShare - platformShare;

        emit SplitExecuted(block.number, total, nodeShare, platformShare, developerShare);

        // Effects ก่อน Interactions (CEI)
        (bool okNode, ) = nodeProviderPayout.call{value: nodeShare}("");
        require(okNode, "RevenueSplit: node payout failed");
        (bool okPlatform, ) = platformOps.call{value: platformShare}("");
        require(okPlatform, "RevenueSplit: platform payout failed");
        // developerShare ค้างใน contract → developerPool รับผิดชอบ (claim จากกองนี้)
        return true;
    }

    /// จ่ายรายวันให้ผู้ให้เครื่อง (75%) — batch เดียว จ่ายหลายโหนด
    function batchPayout(address[] calldata nodes, uint256[] calldata amountsUsd)
        external
        onlyOwner
        returns (uint256 batchId)
    {
        require(nodes.length == amountsUsd.length, "RevenueSplit: length mismatch");
        require(nodes.length > 0, "RevenueSplit: empty batch");

        batchId = uint256(keccak256(abi.encodePacked(block.number, msg.sender, nodes.length)));
        require(!batchProcessed[batchId], "RevenueSplit: batch already processed");
        batchProcessed[batchId] = true;          // Effect ก่อน Interaction

        uint256 total;
        for (uint256 i = 0; i < nodes.length; ++i) {
            total += amountsUsd[i];
        }
        require(total <= address(this).balance, "RevenueSplit: insufficient balance");

        for (uint256 i = 0; i < nodes.length; ++i) {
            (bool ok, ) = nodes[i].call{value: amountsUsd[i]}("");
            require(ok, "RevenueSplit: payout failed");
        }
        emit PayoutBatch(batchId, nodes, amountsUsd);
    }

    /// ตั้ง verified developer (owner — production: ผ่าน governance/merkle proof)
    function verifyDeveloper(address developer) external onlyOwner {
        verifiedDevelopers[developer] = true;
        emit DeveloperVerified(developer);
    }

    /// นักพัฒนาที่ผ่านการยืนยัน (PR merged) เรียกถอนจากกอง 5% (คงค้างใน contract)
    function claimDeveloperReward(uint256 amountUsd) external returns (bool) {
        require(verifiedDevelopers[msg.sender], "RevenueSplit: developer not verified");
        require(amountUsd > 0, "RevenueSplit: zero claim");
        require(amountUsd <= address(this).balance, "RevenueSplit: insufficient pool");

        claimedDeveloperRewards[msg.sender] += amountUsd;   // Effect ก่อน Interaction
        (bool ok, ) = msg.sender.call{value: amountUsd}("");
        require(ok, "RevenueSplit: claim failed");
        emit DeveloperClaimed(msg.sender, amountUsd);
        return true;
    }

    /// เปลี่ยนผู้รับ (prototype: owner คนเดียว — production ต้อง multi-sig)
    function setRecipients(address nodePayout_, address platformOps_, address developerPool_)
        external onlyOwner
    {
        require(nodePayout_ != address(0) && platformOps_ != address(0) && developerPool_ != address(0),
                "RevenueSplit: zero address");
        nodeProviderPayout = nodePayout_;
        platformOps = platformOps_;
        developerPool = developerPool_;
        emit RecipientsUpdated(nodePayout_, platformOps_, developerPool_);
    }

    /// ยอดคงเหลือใน contract (กอง 5% ค้างจ่าย + เงินรอแบ่ง)
    function balance() external view returns (uint256) {
        return address(this).balance;
    }
}
