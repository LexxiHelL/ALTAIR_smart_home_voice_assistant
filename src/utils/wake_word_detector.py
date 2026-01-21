"""
Модуль для детекции wake word (ключевого слова) "Карма" для активации голосового ассистента.
"""
import sounddevice as sd
import numpy as np
from src.models.speech_to_text import SpeechToText
import queue
import threading

WAKE_WORDS = ["карма", "карму", "карме", "кармой", "кармы", "кармой", "кармою"]
STOP_WORDS = ["стоп", "останови", "отмена", "отменить", "выход"]

class WakeWordDetector:
    def __init__(self, stt_model_path: str = "models/asr/vosk/vosk-model-small-ru-0.22", 
                 sample_rate: int = 16000, chunk_size: int = 1600):
        """
        Инициализация детектора wake word.
        :param stt_model_path: путь к модели Vosk для распознавания
        :param sample_rate: частота дискретизации
        :param chunk_size: размер чанка для обработки
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.stt = SpeechToText(backend="vosk", model_path=stt_model_path)
        self.is_listening = False
        self.should_stop = False  # Флаг для полной остановки скрипта
        self.audio_queue = queue.Queue()
        
    def _audio_callback(self, indata, frames, time, status):
        """Callback для записи аудио в очередь."""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(indata.copy())
    
    def _process_audio_chunk(self, audio_data: np.ndarray) -> tuple:
        """
        Обрабатывает чанк аудио и проверяет наличие wake word или стоп-слова.
        :param audio_data: массив аудиоданных
        :return: (wake_word_detected, stop_word_detected) - кортеж булевых значений
        """
        # Сохраняем временный файл для распознавания
        import tempfile
        import scipy.io.wavfile as wav
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            # Преобразуем в int16
            audio_int16 = np.int16(audio_data * 32767)
            wav.write(tmp_path, self.sample_rate, audio_int16)
            
            try:
                result = self.stt.transcribe(tmp_path)
                text = result.get('text', '').lower().strip()
                
                # Проверяем наличие wake word (используем регулярные выражения для точного поиска)
                import re
                for wake_word in WAKE_WORDS:
                    # Ищем wake word как отдельное слово или в начале/конце фразы
                    pattern = r'\b' + re.escape(wake_word) + r'\b|^' + re.escape(wake_word) + r'|' + re.escape(wake_word) + r'$'
                    if re.search(pattern, text):
                        return (True, False)
                
                # Проверяем наличие стоп-слова
                for stop_word in STOP_WORDS:
                    if stop_word in text:
                        return (False, True)
            except Exception as e:
                pass  # Игнорируем ошибки распознавания для отдельных чанков
            finally:
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        return (False, False)
    
    def listen_for_wake_word(self, callback=None):
        """
        Начинает прослушивание микрофона в ожидании wake word.
        :param callback: функция, которая будет вызвана при обнаружении wake word
        """
        print("Слушаю wake word 'Карма'... (скажите 'Стоп' для остановки скрипта, Ctrl+C для выхода)")
        self.is_listening = True
        
        audio_buffer = []
        buffer_duration = 4.0  # секунды для буфера (увеличено для лучшего распознавания)
        buffer_size = int(self.sample_rate * buffer_duration)
        check_interval = int(self.sample_rate * 0.8)  # Проверяем каждые 0.8 секунды
        chunks_to_check = check_interval // self.chunk_size
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                              dtype='float32', callback=self._audio_callback,
                              blocksize=self.chunk_size):
                chunk_count = 0
                while self.is_listening:
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                        audio_buffer.append(chunk.flatten())
                        chunk_count += 1
                        
                        # Ограничиваем размер буфера
                        if len(audio_buffer) * self.chunk_size > buffer_size:
                            audio_buffer.pop(0)
                        
                        # Проверяем каждые 0.8 секунды на наличие wake word или стоп-слова
                        # Используем последние 2-3 секунды для более точного распознавания
                        if chunk_count >= chunks_to_check and len(audio_buffer) >= chunks_to_check:
                            # Берем последние 2-3 секунды для проверки
                            check_chunks = min(chunks_to_check * 3, len(audio_buffer))
                            recent_audio = np.concatenate(audio_buffer[-check_chunks:])
                            wake_detected, stop_detected = self._process_audio_chunk(recent_audio)
                            chunk_count = 0  # Сбрасываем счетчик
                            
                            if stop_detected:
                                print("\n✓ Стоп-слово обнаружено! Останавливаю скрипт...")
                                self.is_listening = False
                                self.should_stop = True
                                return False
                            
                            if wake_detected:
                                print("✓ Wake word обнаружен! Активирую запись команды...")
                                self.is_listening = False
                                if callback:
                                    callback()
                                return True
                            
                            # Дополнительно проверяем весь буфер каждые 2 секунды для надежности
                            if len(audio_buffer) >= chunks_to_check * 2:
                                full_audio = np.concatenate(audio_buffer)
                                wake_detected_full, stop_detected_full = self._process_audio_chunk(full_audio)
                                
                                if stop_detected_full:
                                    print("\n✓ Стоп-слово обнаружено! Останавливаю скрипт...")
                                    self.is_listening = False
                                    self.should_stop = True
                                    return False
                                
                                if wake_detected_full:
                                    print("✓ Wake word обнаружен! Активирую запись команды...")
                                    self.is_listening = False
                                    if callback:
                                        callback()
                                    return True
                    except queue.Empty:
                        continue
        except KeyboardInterrupt:
            print("\nОстановка прослушивания...")
            self.is_listening = False
        except Exception as e:
            print(f"Ошибка при прослушивании: {e}")
            self.is_listening = False
        
        return False
    
    def stop(self):
        """Останавливает прослушивание."""
        self.is_listening = False

