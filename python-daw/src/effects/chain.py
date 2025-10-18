from dataclasses import dataclass
from typing import Any, List, Optional, Sequence


@dataclass
class EffectSlot:
    effect: Any
    name: Optional[str] = None
    bypass: bool = False
    wet: float = 1.0  # 0..1


class EffectChain:
    """Ordered per-track effects chain with bypass and wet/dry per slot.

    Effects are expected to implement an `apply(audio_data: List[float]) -> List[float]` method
    (see src/effects/base.py). The chain will blend each effect's output with the current
    signal using the slot's `wet` ratio.
    """

    def __init__(self) -> None:
        self.slots: List[EffectSlot] = []

    def add(self, effect: Any, name: Optional[str] = None, wet: float = 1.0) -> int:
        w = float(max(0.0, min(1.0, wet)))
        slot = EffectSlot(effect=effect, name=name or type(effect).__name__, wet=w)
        self.slots.append(slot)
        return len(self.slots) - 1

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.slots):
            self.slots.pop(index)

    def move(self, old_index: int, new_index: int) -> None:
        if old_index == new_index or not (0 <= old_index < len(self.slots)):
            return
        slot = self.slots.pop(old_index)
        new_index = max(0, min(new_index, len(self.slots)))
        self.slots.insert(new_index, slot)

    def clear(self) -> None:
        self.slots.clear()

    def process(self, buffer: Sequence[float]) -> List[float]:
        out = list(buffer)
        if not out:
            return out
        for slot in self.slots:
            if slot.bypass or slot.wet <= 0.0:
                continue
            fx = slot.effect
            wet_sig = None
            try:
                if hasattr(fx, "apply"):
                    wet_sig = fx.apply(out)
            except Exception:
                wet_sig = None
            if wet_sig is None:
                continue
            # safety: length match via zip; clamp mix
            w = float(slot.wet)
            d = 1.0 - w
            out = [max(-1.0, min(1.0, d * dry + w * wet)) for dry, wet in zip(out, wet_sig)]
        return out

    def to_config(self) -> List[dict]:
        conf: List[dict] = []
        for slot in self.slots:
            params = None
            # prefer explicit parameters dict if present
            if hasattr(slot.effect, "parameters"):
                try:
                    params = dict(getattr(slot.effect, "parameters"))
                except Exception:
                    params = None
            conf.append({
                "type": type(slot.effect).__name__,
                "name": slot.name,
                "bypass": bool(slot.bypass),
                "wet": float(slot.wet),
                "params": params,
            })
        return conf

    def from_config(self, config: List[dict], registry: Optional[dict] = None) -> None:
        self.clear()
        if not config:
            return
        reg = registry or {}
        for item in config:
            cls = reg.get(item.get("type"))
            if not cls:
                continue
            try:
                fx = cls()
            except Exception:
                continue
            params = item.get("params")
            if params and hasattr(fx, "set_parameters"):
                try:
                    fx.set_parameters(params)
                except Exception:
                    pass
            idx = self.add(fx, name=item.get("name"), wet=float(item.get("wet", 1.0)))
            self.slots[idx].bypass = bool(item.get("bypass", False))
