"""
ASEAN Grid — AI Strategy Hooks (🧠 จุดที่ AI จูนนิ่งใส่โมเดล)
จุดตัดสินใจสำคัญทุกจุดของระบบเป็นปลั๊กอิน AI — implement interface นี้
แล้วลงทะเบียน → ระบบใช้โมเดลคุณทันที โดยไม่ต้องแตะแกนระบบ

Hook ที่มี (ดู prototype/README.md ตาราง AI Hooks):
- predict_best_channel   : เลือกช่องทางจ่ายสูงสุด (arbitrage)
- predict_price_curve    : คาดการณ์ราคา GPU ล่วงหน้า
- score_node_trust       : ให้คะแนนความน่าเชื่อถือโหนด (กันโกง)
- forecast_demand        : พยากรณ์ดีมานด์ → จัดคิวล่วงหน้า
- route_workload         : เลือกเส้นทางงานตาม latency/ราคา/ความเสี่ยง
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIStrategy(ABC):
    """Base class สำหรับโมเดล AI ทุกตัวที่แทรกเข้าระบบ"""

    name: str = "base"

    def predict_best_channel(self, features: Dict[str, Any]) -> Optional[str]:
        """คืนชื่อช่องทางที่ดีที่สุด หรือ None = ปล่อยให้ระบบตัดสินใจเอง"""
        return None

    def predict_price_curve(self, hour: int, region: str) -> float:
        """คืนราคา GPU ที่คาดการณ์ (USD/hr) สำหรับชั่วโมงนั้น"""
        raise NotImplementedError

    def score_node_trust(self, node) -> float:
        """คืนคะแนน 0-1 — ยิ่งสูงยิ่งน่าเชื่อถือ"""
        return 0.5

    def forecast_demand(self, region: str, window_hours: int) -> float:
        """คืนดีมานด์ที่คาดการณ์ (0-1 normalized)"""
        return 0.5

    def route_workload(self, workload, nodes) -> Any:
        """คืนโหนดที่เลือก (override ได้) หรือ None = ใช้ scheduler มาตรฐาน"""
        return None


class HeuristicStrategy(AIStrategy):
    """กลยุทธ์พื้นฐาน (ค่าเริ่มต้น) — ใช้สูตรคะแนนจาก channels.ChannelQuote.score
    ตัวนี้คือ 'เบสไลน์' ให้ AI จูนเทียบ: โมเดลคุณต้องดีกว่า heuristic นี้"""
    name = "heuristic"

    def predict_best_channel(self, features: Dict[str, Any]) -> Optional[str]:
        quotes = features.get("quotes", [])
        if not quotes:
            return None
        # คะแนน = price * reliability / (queue * latency) — สูงสุดชนะ
        def score(q):
            return (q["price"] * q["reliability"] * 100.0) / (
                max(1, q["queue"]) * max(1, q["latency"]))
        return max(quotes, key=score)["channel"]


class StrategyRegistry:
    """Registry กลาง — Dev/AI ทีมลงทะเบียนโมเดลที่นี่ แล้วใช้ชื่อเรียกได้"""
    _strategies: Dict[str, AIStrategy] = {
        "heuristic": HeuristicStrategy(),
    }

    @classmethod
    def register(cls, name: str, strategy: AIStrategy) -> None:
        cls._strategies[name] = strategy

    @classmethod
    def get(cls, name: str) -> AIStrategy:
        if name not in cls._strategies:
            raise KeyError(f"Unknown strategy '{name}'. Registered: {list(cls._strategies)}")
        return cls._strategies[name]

    @classmethod
    def list(cls) -> list:
        return list(cls._strategies)
