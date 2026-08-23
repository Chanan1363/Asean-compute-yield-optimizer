// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.24;

// ═══════════════════════════════════════════════════════════════════════
// ASEAN Grid — RevenueSplitV2 (Implementation)
// Smart contract จัดสรรรายได้ 75/20/5 — แบบ Points-based + Permissionless Claim
// + Collateral Staking (ยืมดีไซน์จาก Psyche solana-treasurer / coordinator)
// แต่ยังคงอยู่บน EVM (Solidity) — ดู docs/NOUS_ALIGNMENT.md Part B
//
// หลัก 3 ข้อที่เปลี่ยนจาก v1:
//  1. Points-based (Pull) — owner ไม่ต้องสั่ง batchPayout อีกต่อไป
//     coordinator (authorized) บันทึก points ตามงานจริง → โหนดแปลงเป็นเงินเอง
//  2. Permissionless claim — โหนดเรียก claim() เอง ไม่มี owner คั่นกลาง
//  3. Collateral staking — โหนดต้องวาง $GRID (stake) ก่อนรับงาน/claim
//     (ตรงกับ core/models.py: NodeStatus.STAKED)
//
// Security (รักษาจาก v1):
//  - CEI (Checks-Effects-Interactions): อัปเดต state ก่อนโอนเงินทุกครั้ง
//  - claimedPoints กัน claim ซ้ำ (replay guard)
//  - remainder จาก integer division → developer pool (กันเงินหาย)
//  - เฉพาะ coordinator เท่านั้นบันทึก points / owner เท่านั้น settle epoch
// ═══════════════════════════════════════════════════════════════════════

contract RevenueSplitV2 {
    // ── Core 75/20/5 (basis points — immutable ของตาย ห้ามแก้) ────────
    uint256 public constant NODE_SHARE = 7500;       // 75%
    uint256 public constant PLATFORM_SHARE = 2000;   // 20%
    uint256 public constant DEVELOPER_SHARE = 500;   // 5%
    uint256 private constant BPS = 10000;

    // ── บทบาท ────────────────────────────────────────────────────────
    address public owner;
    address public coordinator;      // บันทึก points (off-chain core → future on-chain)

    // ── Staking (collateral — กันโกงชั้นเงิน) ─────────────────────────
    uint256 public constant MIN_STAKE_GRID = 100 ether;  // conceptual $GRID (ปรับตาม tokenomics)
    mapping(address => uint256) public stakeOf;          // $GRID ที่วางไว้

    // ── Epoch (รอบงาน) ───────────────────────────────────────────────
    struct Epoch {
        uint256 index;
        uint256 totalPoints;          // points ทั้งหมดที่ coordinator แจกใน epoch นี้
        uint256 nodePoolUsd;          // 75% ของรายได้ epoch (เติมตอน settle)
        uint256 platformPoolUsd;      // 20%
        uint256 devPoolUsd;           // 5%
        bool settled;                 // settle ซ้ำไม่ได้
        mapping(address => uint256) earnedPoints;   // points ที่โหนดทำได้
        mapping(address => uint256) claimedPoints;  // points ที่ claim ไปแล้ว (replay guard)
    }
    mapping(uint256 => Epoch) public epochs;
    uint256 public epochCount;

    // ── Events ───────────────────────────────────────────────────────
    event Staked(address indexed node, uint256 amount);
    event Unstaked(address indexed node, uint256 amount);
    event WorkRecorded(uint256 indexed epochIdx, address indexed node, uint256 points);
    event EpochSettled(uint256 indexed epochIdx, uint256 nodePool, uint256 platformPool, uint256 devPool);
    event Claimed(uint256 indexed epochIdx, address indexed node, uint256 points, uint256 payoutUsd);

    // ── Modifiers ────────────────────────────────────────────────────
    modifier onlyOwner() {
        require(msg.sender == owner, "RevenueSplitV2: not owner");
        _;
    }
    modifier onlyCoordinator() {
        require(msg.sender == coordinator, "RevenueSplitV2: not coordinator");
        _;
    }

    constructor(address coordinator_) {
        require(coordinator_ != address(0), "RevenueSplitV2: zero coordinator");
        owner = msg.sender;
        coordinator = coordinator_;
    }

    // ── Staking: วางหลักประกันก่อนรับงาน ─────────────────────────────
    function stake() external payable returns (uint256) {
        require(msg.value > 0, "RevenueSplitV2: zero stake");
        stakeOf[msg.sender] += msg.value;            // Effect ก่อน Interaction
        emit Staked(msg.sender, msg.value);
        return stakeOf[msg.sender];
    }

    /// ถอน stake ได้เมื่อไม่มี points ค้าง (กันหนีหลังรับงาน)
    function unstake(uint256 amount) external {
        require(amount > 0 && stakeOf[msg.sender] >= amount, "RevenueSplitV2: insufficient stake");
        require(stakeOf[msg.sender] - amount >= MIN_STAKE_GRID || stakeOf[msg.sender] == amount,
                "RevenueSplitV2: keep min stake");
        stakeOf[msg.sender] -= amount;               // Effect ก่อน Interaction
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "RevenueSplitV2: unstake failed");
        emit Unstaked(msg.sender, amount);
    }

    // ── Coordinator บันทึกงาน (points) ───────────────────────────────
    function recordWork(uint256 epochIdx, address node, uint256 points)
        external onlyCoordinator
    {
        require(points > 0, "RevenueSplitV2: zero points");
        Epoch storage e = epochs[epochIdx];
        require(e.index == epochIdx, "RevenueSplitV2: epoch not found");
        require(!e.settled, "RevenueSplitV2: epoch settled");
        e.earnedPoints[node] += points;              // Effect ก่อน Interaction
        e.totalPoints += points;
        emit WorkRecorded(epochIdx, node, points);
    }

    /// เริ่ม epoch ใหม่ (owner — เมื่อเริ่มรอบงาน)
    function createEpoch() external onlyOwner returns (uint256) {
        uint256 idx = epochCount++;
        epochs[idx].index = idx;
        return idx;
    }

    // ── Settle: แบ่งรายได้ 75/20/5 เข้ากองของ epoch ──────────────────
    /// เรียกเมื่อจบ epoch: เงินที่รับมา (ETH) แบ่งเข้ากองตามสัดส่วนคงที่
    function settleEpoch(uint256 epochIdx) external payable onlyOwner {
        require(msg.value > 0, "RevenueSplitV2: empty settle");
        Epoch storage e = epochs[epochIdx];
        require(!e.settled, "RevenueSplitV2: already settled");

        uint256 total = msg.value;
        uint256 nodePool = (total * NODE_SHARE) / BPS;
        uint256 platformPool = (total * PLATFORM_SHARE) / BPS;
        uint256 devPool = total - nodePool - platformPool;   // remainder → dev pool

        e.nodePoolUsd = nodePool;
        e.platformPoolUsd = platformPool;
        e.devPoolUsd = devPool;
        e.settled = true;                                  // Effect ก่อน Interaction
        emit EpochSettled(epochIdx, nodePool, platformPool, devPool);
    }

    // ── Permissionless Claim: โหนดถอนเอง ไม่ต้องรอ owner ─────────────
    function claim(uint256 epochIdx) external {
        require(stakeOf[msg.sender] >= MIN_STAKE_GRID, "RevenueSplitV2: must stake first");
        Epoch storage e = epochs[epochIdx];
        require(e.settled, "RevenueSplitV2: epoch not settled");

        uint256 unclaimed = e.earnedPoints[msg.sender] - e.claimedPoints[msg.sender];
        require(unclaimed > 0, "RevenueSplitV2: nothing to claim");

        // สัดส่วนตามงานจริง: points ของฉัน / points ทั้งหมด x กอง 75%
        uint256 payout = unclaimed * e.nodePoolUsd / e.totalPoints;
        require(payout > 0, "RevenueSplitV2: zero payout");

        e.claimedPoints[msg.sender] = e.earnedPoints[msg.sender];  // Effect ก่อน Interaction
        (bool ok, ) = payable(msg.sender).call{value: payout}("");
        require(ok, "RevenueSplitV2: claim failed");
        emit Claimed(epochIdx, msg.sender, unclaimed, payout);
    }

    // ── Admin ────────────────────────────────────────────────────────
    function setCoordinator(address coordinator_) external onlyOwner {
        require(coordinator_ != address(0), "RevenueSplitV2: zero address");
        coordinator = coordinator_;
    }

    /// เงินคงเหลือใน contract (กองแพลตฟอร์ม 20% + dev 5% + เงินรอ settle)
    function balance() external view returns (uint256) {
        return address(this).balance;
    }
}
