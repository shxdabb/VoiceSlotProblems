from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Iterable
import uuid


@dataclass
class Voice:
    id: int
    user_name: str
    name: str
    original_audio_url: str
    external_voice_id: Optional[str] = None
    last_used_at: Optional[datetime] = None
    is_deleted: bool = False


class VoiceSlotManager:
    def __init__(self, max_slots: int = 5):
        self.max_slots = max_slots
        self._voices: List[Voice] = []

    def _clone_voice(self, name, audio_url) -> str:
        return f"voice_{uuid.uuid4().hex[:8]}"

    def _delete_from_api(self, external_voice_id) -> bool:
        return True

    def _occupied_count(self) -> int:
        return sum(1 for v in self._voices if v.external_voice_id and not v.is_deleted)

    def _evict_lru(self, exclude_ids: Optional[Iterable[int]] = None) -> bool:
        exclude_ids = set(exclude_ids or [])
        candidates = [v for v in self._voices if v.external_voice_id and not v.is_deleted and v.id not in exclude_ids]
        if not candidates:
            return False
        lru_voice = min(candidates, key=lambda v: v.last_used_at or datetime.min)
        self._delete_from_api(lru_voice.external_voice_id)
        lru_voice.external_voice_id = None
        return True

    def add_voice(self, voice: Voice) -> str:
        self._voices.append(voice)
        if self._occupied_count() >= self.max_slots:
            self._evict_lru()
        voice.external_voice_id = self._clone_voice(voice.name, voice.original_audio_url)
        voice.last_used_at = datetime.now()
        return voice.external_voice_id

    def use_voice(self, voice: Voice) -> str:
        if voice.external_voice_id:
            voice.last_used_at = datetime.now()
            return voice.external_voice_id
        if self._occupied_count() >= self.max_slots:
            self._evict_lru(exclude_ids=[voice.id])
        voice.external_voice_id = self._clone_voice(voice.name, voice.original_audio_url)
        voice.last_used_at = datetime.now()
        return voice.external_voice_id

    def delete_voice(self, voice: Voice) -> None:
        if voice.external_voice_id:
            self._delete_from_api(voice.external_voice_id)
        voice.external_voice_id = None
        voice.is_deleted = True