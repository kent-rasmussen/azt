# azt/harmony_sync.py

from uuid import UUID
from harmony_client import HarmonyClient
import asyncio
import logging

class AZTHarmonyBridge:
    """
    Integrates Harmony sync into AZT's phonetic analysis workflow.
    """
    
    def __init__(self, harmony_server_url: str = "http://localhost:5000"):
        self.harmony = HarmonyClient(server_url=harmony_server_url)
        self.logger = logging.getLogger(__name__)
    
    async def sync_to_harmony(self):
        """
        Sync all local changes to Harmony server.
        Call this when user clicks "Sync" button or after recording audio.
        """
        try:
            result = await self.harmony.sync_with_server()
            self.logger.info(f"Sync successful: "
                f"{len(result.missing_from_local)} changes received, "
                f"{len(result.missing_from_remote)} changes sent")
            return result
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            raise
    
    async def on_audio_recorded(
        self,
        sense_id: UUID,
        frame: str,
        audio_blob_ref: str,
        phonetic_form: str,
        quality_score: float
    ):
        """
        Called when AZT records new audio.
        Submits as a Harmony change.
        """
        change_data = {
            "senseId": str(sense_id),
            "frame": frame,
            "phonetic_form": phonetic_form,
            "audio_blob_ref": audio_blob_ref,
            "quality_score": quality_score
        }
        
        recording_id = UUID(int=0)  # Generate unique ID
        
        commit = await self.harmony.add_change(
            change_type="RecordPhoneticAudioChange",
            entity_id=recording_id,
            change_data=change_data
        )
        
        self.logger.info(f"Audio recorded: {sense_id}/{frame} (commit: {commit.id})")
        
        # Auto-sync if online
        # Or queue for later if offline
        if self._is_online():
            await self.sync_to_harmony()
    
    def _is_online(self) -> bool:
        """Check if Harmony server is reachable."""
        try:
            self.harmony.session.get(f"{self.harmony.server_url}/health", timeout=2)
            return True
        except:
            return False

# In AZT's main GUI (main.App()):

class AZTMainWindow:
    def __init__(self):
        # ... existing AZT setup ...
        self.harmony_bridge = AZTHarmonyBridge()
    
    def on_record_audio_button_clicked(self):
        """User records audio for a sense."""
        sense_id, frame, audio_path = self.get_ui_inputs()
        
        # ... existing audio processing ...
        
        # Submit to Harmony
        asyncio.create_task(
            self.harmony_bridge.on_audio_recorded(
                sense_id=sense_id,
                frame=frame,
                audio_blob_ref=f"s3://...",
                phonetic_form="[kɔ̀tɔ̀]",
                quality_score=0.92
            )
        )
    
    def on_sync_button_clicked(self):
        """User clicks 'Sync with Harmony' button."""
        asyncio.create_task(self.harmony_bridge.sync_to_harmony())
