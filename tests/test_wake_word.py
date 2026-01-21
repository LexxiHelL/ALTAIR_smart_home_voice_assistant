"""
Тест для автоматической активации по wake word "Карма".
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.utils.wake_word_detector import WakeWordDetector
from src.data.audio_utils import record_audio_vad_with_stop
from src.models.speech_to_text import SpeechToText
from src.utils.text_segments import segment_command
from src.utils.location_extractor import resolve_location_reference
from src.utils.task_extractor import extract_task
from datetime import datetime

TEST_DIR = "data/custom_dataset/voice_commands/"

def process_command():
    """Обрабатывает голосовую команду после активации wake word."""
    TEST_FILE = os.path.join(TEST_DIR, f"voice_command_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
    
    stt = SpeechToText(backend="vosk", model_path="models/asr/vosk/vosk-model-small-ru-0.22")
    
    print("Записываю команду...")
    success = record_audio_vad_with_stop(TEST_FILE, stt, max_duration=10.0, pause_threshold=1.0)
    
    # Если запись была отменена по стоп-слову, не обрабатываем команду
    if not success:
        # Удаляем файл, если он был создан
        if os.path.exists(TEST_FILE):
            try:
                os.unlink(TEST_FILE)
            except:
                pass
        print("Запись отменена. Возвращаюсь к прослушиванию wake word...")
        return
    
    result = stt.transcribe(TEST_FILE)
    print(f"\nРаспознанный текст: {result['text']}")
    
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

def main():
    """Основная функция для тестирования wake word detection."""
    detector = WakeWordDetector()
    
    print("=" * 60)
    print("Голосовой ассистент активируется по слову 'Карма'")
    print("Скажите 'Карма' для активации, затем произнесите команду")
    print("Скажите 'Стоп' во время записи для отмены без сохранения")
    print("Скажите 'Стоп' во время прослушивания для полной остановки скрипта")
    print("Нажмите Ctrl+C для выхода")
    print("=" * 60)
    
    while True:
        detector.listen_for_wake_word(callback=process_command)
        
        # Проверяем, нужно ли полностью остановить скрипт
        if detector.should_stop:
            print("\nСкрипт остановлен.")
            break
        
        print("\nВозвращаюсь к прослушиванию wake word...\n")

if __name__ == "__main__":
    main()

