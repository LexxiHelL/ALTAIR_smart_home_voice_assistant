import serial
import json
import time
import threading
import queue
import speech_recognition as sr
from datetime import datetime

class ArduinoVoiceController:
    def __init__(self, port='COM3', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.data_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.running = True
        self.last_data = {}
        time.sleep(2)  # Ожидание инициализации Arduino
        
        # Запуск потоков
        self.read_thread = threading.Thread(target=self._read_serial)
        self.process_thread = threading.Thread(target=self._process_data)
        self.voice_thread = threading.Thread(target=self._voice_listener)
        
        self.read_thread.start()
        self.process_thread.start()
        self.voice_thread.start()
        
        print("Система голосового управления Arduino запущена")
        print("Скажите 'помощь' для списка команд")
    
    def _read_serial(self):
        """Чтение данных из Serial в отдельном потоке"""
        buffer = ""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    char = self.ser.read().decode('utf-8', errors='ignore')
                    buffer += char
                    
                    if char == '\n' or char == '\r':
                        if buffer.strip():
                            self.data_queue.put(buffer.strip())
                        buffer = ""
            except:
                pass
            time.sleep(0.01)
    
    def _process_data(self):
        """Обработка полученных данных"""
        while self.running:
            try:
                if not self.data_queue.empty():
                    line = self.data_queue.get_nowait()
                    self._handle_message(line)
            except queue.Empty:
                pass
            time.sleep(0.01)
    
    def _handle_message(self, message):
        """Обработка разных типов сообщений от Arduino"""
        if message.startswith("DATA:"):
            try:
                json_str = message[5:]  # Убираем "DATA:"
                data = json.loads(json_str)
                self.last_data = data
                self._display_data(data)
            except json.JSONDecodeError:
                print(f"Ошибка JSON: {message}")
        
        elif message.startswith("RESPONSE:"):
            response = message[9:]  # Убираем "RESPONSE:"
            print(f"Ардуино: {response}")
            
            # Сохранение важных ответов в файл лога
            if "ALARM_TRIGGERED" in response:
                self._log_event("ТРЕВОГА!", "Сработала сигнализация")
        
        elif message.startswith("INFO:") or message.startswith("WARNING:"):
            print(f"Ардуино: {message}")
        
        elif message.startswith("COMMANDS:"):
            # Игнорируем список команд при старте
            pass
        
        else:
            print(f"Ардуино: {message}")
    
    def _display_data(self, data):
        """Отображение данных в консоли"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}]")
        print(f"  Температура: {data['temperature']}°C")
        print(f"  Расстояние: {data['distance']} см")
        print(f"  Сигнализация: {'ВКЛ' if data['alarm_enabled'] else 'ВЫКЛ'}")
        if data['alarm_triggered']:
            print("  ⚠️  ТРЕВОГА АКТИВНА!")
        print(f"  Обогреватель: {'ВКЛ' if data['heater'] else 'ВЫКЛ'}")
        print(f"  Вентилятор: {'ВКЛ' if data['fan'] else 'ВЫКЛ'}")
        print(f"  Свет: {'ВКЛ' if data['light'] else 'ВЫКЛ'}")
        print(f"  Окно: {data['window_angle']}°")
    
    def _voice_listener(self):
        """Прослушивание голосовых команд"""
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        with microphone as source:
            print("Калибровка микрофона...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Микрофон готов. Говорите...")
            
            while self.running:
                try:
                    print("\nСлушаю... (скажите 'стоп' для выхода)")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    # Распознавание речи
                    try:
                        # Для русского
                        text = recognizer.recognize_google(audio, language="ru-RU")
                        print(f"Вы сказали: {text}")
                        
                        # Проверка команды остановки
                        if "стоп" in text.lower() or "stop" in text.lower():
                            print("Останавливаю систему...")
                            self.stop()
                            break
                        
                        # Отправка команды на Arduino
                        self.send_command(text)
                        
                        # Локальная обработка некоторых команд
                        self._process_voice_command(text.lower())
                        
                    except sr.UnknownValueError:
                        print("Не понял, повторите")
                        self.send_command("UNKNOWN")
                    except sr.RequestError:
                        print("Ошибка сервиса распознавания")
                        # Попробуем офлайн распознавание
                        try:
                            text = recognizer.recognize_sphinx(audio, language="ru-RU")
                            print(f"Офлайн: {text}")
                            self.send_command(text)
                        except:
                            pass
                            
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"Ошибка микрофона: {e}")
    
    def _process_voice_command(self, command):
        """Локальная обработка голосовых команд"""
        command = command.lower()
        
        if "температура" in command or "сколько градусов" in command:
            if self.last_data:
                print(f"Сейчас {self.last_data['temperature']}°C")
        
        elif "статус" in command or "как дела" in command:
            if self.last_data:
                self._display_data(self.last_data)
    
    def send_command(self, command):
        """Отправка команды на Arduino"""
        try:
            self.ser.write(f"{command}\n".encode('utf-8'))
            print(f"Отправлено: {command}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    
    def send_direct_command(self, command):
        """Отправка прямой команды (не голосовой)"""
        commands = {
            "alarm_on": "ALARM_ON",
            "alarm_off": "ALARM_OFF",
            "light_on": "LIGHT_ON",
            "light_off": "LIGHT_OFF",
            "window_open": "WINDOW_OPEN",
            "window_close": "WINDOW_CLOSE",
            "heater_on": "HEATER_ON",
            "heater_off": "HEATER_OFF",
            "fan_on": "FAN_ON",
            "fan_off": "FAN_OFF",
            "status": "STATUS",
            "help": "HELP"
        }
        
        if command in commands:
            self.send_command(commands[command])
        else:
            self.send_command(command)
    
    def _log_event(self, event_type, message):
        """Логирование событий в файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("arduino_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {event_type}: {message}\n")
        print(f"Событие записано в лог: {event_type}")
    
    def stop(self):
        """Остановка системы"""
        self.running = False
        time.sleep(0.5)
        
        if self.ser.is_open:
            self.ser.close()
        
        print("Система остановлена")
    
    def monitor(self):
        """Основной цикл мониторинга"""
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

# Упрощенная версия без speech recognition
class ArduinoSimpleController:
    def __init__(self, port='COM3', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        print("Простой контроллер Arduino запущен")
    
    def read_data(self):
        """Чтение данных от Arduino"""
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            return line
        except Exception as e:
            print(f"Ошибка чтения: {e}")
            return None
    
    def send_command(self, command):
        """Отправка команды"""
        self.ser.write(f"{command}\n".encode('utf-8'))
    
    def interactive_mode(self):
        """Интерактивный режим с командной строки"""
        print("\nИнтерактивный режим")
        print("Команды: alarm_on, alarm_off, light_on, light_off")
        print("         window_open, window_close, status, help")
        print("         или голосовая команда на русском")
        print("Введите 'exit' для выхода\n")
        
        while True:
            # Чтение данных
            data = self.read_data()
            if data and data.startswith("DATA:"):
                try:
                    json_str = data[5:]
                    data_dict = json.loads(json_str)
                    print(f"\nТемпература: {data_dict['temperature']}°C")
                except:
                    pass
            
            # Проверка ввода команды
            try:
                user_input = input("Команда > ").strip()
                if user_input.lower() == 'exit':
                    break
                elif user_input:
                    self.send_command(user_input)
            except KeyboardInterrupt:
                break
        
        self.ser.close()

# Использование
if __name__ == "__main__":
    # Выбор режима работы
    print("Выберите режим работы:")
    print("1. Голосовое управление (требует микрофон и интернет)")
    print("2. Командная строка")
    
    choice = input("Ваш выбор (1/2): ").strip()
    
    # Замените 'COM3' на нужный порт
    port = input("Порт Arduino (по умолчанию COM3): ").strip() or 'COM3'
    
    try:
        if choice == "1":
            # Установите: pip install SpeechRecognition pyaudio
            controller = ArduinoVoiceController(port=port)
            controller.monitor()
        else:
            controller = ArduinoSimpleController(port=port)
            controller.interactive_mode()
            
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Проверьте порт Arduino и установленные библиотеки")