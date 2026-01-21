"""
Тесты для распознавания голосовых команд по аудио.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.models.speech_to_text import SpeechToText
from src.data.audio_utils import record_audio_vad as record_audio

TEST_DIR = "data/custom_dataset/voice_commands/"
from datetime import datetime
TEST_FILE = os.path.join(TEST_DIR, f"voice_command_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")

# Запишем файл с микрофона с автостопом по тишине (макс. 10 сек, стоп при паузе 1 сек)
def test_record_voice_and_stt():
    record_audio(TEST_FILE, max_duration=10.0, pause_threshold=1.0)
    stt = SpeechToText(backend="vosk", model_path="models/asr/vosk/vosk-model-small-ru-0.22")
    result = stt.transcribe(TEST_FILE)
    print(f"Распознанный текст: {result['text']}")
    from src.utils.text_segments import segment_command
    from src.utils.location_extractor import resolve_location_reference
    from src.utils.task_extractor import extract_task
    
    segments = segment_command(result['text'])
    resolved_commands = resolve_location_reference(segments)
    
    print("\nСегменты команды с извлеченными данными:")
    for i, cmd_info in enumerate(resolved_commands, 1):
        task = extract_task(cmd_info['command'])
        room_info = f" [Комната: {cmd_info['room']}]" if cmd_info['room'] else " [Комната не указана]"
        action_info = f" [Действие: {task['action']}]" if task['action'] else ""
        object_info = f" [Объект: {task['object']}]" if task['object'] else ""
        value_info = f" [Значение: {task['value']}]" if task['value'] else ""
        print(f"  {i}. {cmd_info['command']}{room_info}{action_info}{object_info}{value_info}")

if __name__ == "__main__":
    test_record_voice_and_stt()
