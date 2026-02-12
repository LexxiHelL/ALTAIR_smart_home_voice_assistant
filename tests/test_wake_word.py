"""
Тест для автоматической активации по wake word "Карма" с поддержкой текстовых команд и выполнения действий.
"""
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Добавляем путь к корню проекта для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Импорты из вашей кодовой базы
try:
    from src.utils.wake_word_detector import WakeWordDetector, WAKE_WORDS
    from src.data.audio_utils import record_audio_vad
    from src.models.speech_to_text import SpeechToText
    from src.utils.text_segments import segment_command
    from src.utils.location_extractor import resolve_location_reference
    from src.utils.task_extractor import extract_task
    
except ImportError as e:
    print(f"⚠ Ошибка импорта модулей: {e}")
    print("Убедитесь, что вы находитесь в правильной директории")
    sys.exit(1)

# Константы
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "data/custom_dataset/voice_commands/")
STATE_FILE = os.path.join(BASE_DIR, "home_state.json")

# Создаем директории при запуске
os.makedirs(TEST_DIR, exist_ok=True)

class HomeController:
    """Контроллер для управления устройствами умного дома."""
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.device_states = self.load_state()
        
    def load_state(self) -> Dict[str, Any]:
        """Загрузка состояния устройств из файла."""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_state()
    
    def save_state(self):
        """Сохранение состояния устройств в файл."""
        try:
            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ Ошибка при сохранении состояния: {e}")
    
    def get_default_state(self) -> Dict[str, Any]:
        """Состояние устройств по умолчанию."""
        return {
            "rooms": {
                "гостиная": {
                    "свет": {"state": "off", "brightness": 0, "last_update": ""},
                    "телевизор": {"state": "off", "volume": 30, "channel": 1, "last_update": ""},
                    "температура": {"state": "on", "value": 22, "last_update": ""},
                    "шторы": {"state": "closed", "position": 0, "last_update": ""},
                    "кондиционер": {"state": "off", "temp": 24, "mode": "cool", "last_update": ""}
                },
                "спальня": {
                    "свет": {"state": "off", "brightness": 0, "last_update": ""},
                    "температура": {"state": "on", "value": 21, "last_update": ""},
                    "шторы": {"state": "closed", "position": 0, "last_update": ""}
                },
                "кухня": {
                    "свет": {"state": "off", "brightness": 0, "last_update": ""},
                    "температура": {"state": "on", "value": 23, "last_update": ""}
                },
                "ванная": {
                    "свет": {"state": "off", "brightness": 0, "last_update": ""},
                    "вентилятор": {"state": "off", "speed": 0, "last_update": ""}
                }
            },
            "last_command": "",
            "last_update": "",
            "total_commands": 0
        }
    
    def execute_single_command(self, room: str, action: str, device: str, value: str = None) -> bool:
        """Выполнение одной команды - ТОЛЬКО ИЗМЕНЕНИЕ СОСТОЯНИЯ, без записи аудио!"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Нормализуем название комнаты
        room_normalized = room
        
        # Проверяем существование комнаты
        if room_normalized not in self.device_states.get("rooms", {}):
            # Попробуем найти похожую комнату
            for known_room in self.device_states.get("rooms", {}).keys():
                if known_room in room or room in known_room:
                    room_normalized = known_room
                    break
            else:
                print(f"⚠ Комната '{room}' не найдена. Доступные комнаты: {list(self.device_states.get('rooms', {}).keys())}")
                return False
        
        # Проверяем существование устройства
        if device not in self.device_states["rooms"][room_normalized]:
            print(f"⚠ Устройство '{device}' не найдено в комнате '{room_normalized}'. Доступные устройства: {list(self.device_states['rooms'][room_normalized].keys())}")
            return False
        
        # Получаем состояние устройства
        device_state = self.device_states["rooms"][room_normalized][device]
        device_state["last_update"] = timestamp
        
        # Обрабатываем команды
        success = False
        command_description = f"{action} {device} в {room_normalized}"
        
        try:
            if action in ["включи", "включить"]:
                device_state["state"] = "on"
                if device == "свет" and "brightness" in device_state:
                    device_state["brightness"] = 100
                success = True
                print(f"✅ {command_description}")
                
            elif action in ["выключи", "выключить"]:
                device_state["state"] = "off"
                if device == "свет" and "brightness" in device_state:
                    device_state["brightness"] = 0
                success = True
                print(f"✅ {command_description}")
                
            elif action in ["увеличь", "увеличить", "повысь", "повысить"]:
                if device == "температура" and "value" in device_state:
                    device_state["value"] += 1
                    print(f"✅ Температура в {room_normalized} увеличена до {device_state['value']}°C")
                    success = True
                elif device == "свет" and "brightness" in device_state:
                    device_state["brightness"] = min(100, device_state["brightness"] + 10)
                    print(f"✅ Яркость света в {room_normalized} увеличена до {device_state['brightness']}%")
                    success = True
                elif device == "телевизор" and "volume" in device_state:
                    device_state["volume"] = min(100, device_state["volume"] + 5)
                    print(f"✅ Громкость телевизора в {room_normalized} увеличена до {device_state['volume']}%")
                    success = True
                    
            elif action in ["уменьши", "уменьшить", "понизь", "понизить"]:
                if device == "температура" and "value" in device_state:
                    device_state["value"] -= 1
                    print(f"✅ Температура в {room_normalized} уменьшена до {device_state['value']}°C")
                    success = True
                elif device == "свет" and "brightness" in device_state:
                    device_state["brightness"] = max(0, device_state["brightness"] - 10)
                    print(f"✅ Яркость света в {room_normalized} уменьшена до {device_state['brightness']}%")
                    success = True
                elif device == "телевизор" and "volume" in device_state:
                    device_state["volume"] = max(0, device_state["volume"] - 5)
                    print(f"✅ Громкость телевизора в {room_normalized} уменьшена до {device_state['volume']}%")
                    success = True
                    
            elif action in ["установи", "поставь", "настрой"] and value:
                if "градус" in str(value):
                    try:
                        temp = int(str(value).split()[0])
                        if device == "температура":
                            device_state["value"] = temp
                            print(f"✅ Температура в {room_normalized} установлена на {temp}°C")
                            success = True
                    except ValueError:
                        print(f"⚠ Неверное значение температуры: {value}")
                        
                elif "%" in str(value):
                    try:
                        percent = int(str(value).replace("%", ""))
                        if device == "свет" and "brightness" in device_state:
                            device_state["brightness"] = percent
                            device_state["state"] = "on" if percent > 0 else "off"
                            print(f"✅ Яркость света в {room_normalized} установлена на {percent}%")
                            success = True
                        elif device == "телевизор" and "volume" in device_state:
                            device_state["volume"] = percent
                            print(f"✅ Громкость телевизора в {room_normalized} установлена на {percent}%")
                            success = True
                    except ValueError:
                        print(f"⚠ Неверное процентное значение: {value}")
                        
            elif action in ["открой", "открыть"] and device in ["шторы", "жалюзи", "ролеты"]:
                device_state["state"] = "open"
                if "position" in device_state:
                    device_state["position"] = 100
                print(f"✅ {device.capitalize()} в {room_normalized} открыты")
                success = True
                
            elif action in ["закрой", "закрыть"] and device in ["шторы", "жалюзи", "ролеты"]:
                device_state["state"] = "closed"
                if "position" in device_state:
                    device_state["position"] = 0
                print(f"✅ {device.capitalize()} в {room_normalized} закрыты")
                success = True
                
            else:
                print(f"⚠ Неизвестная команда: {command_description}")
        except Exception as e:
            print(f"⚠ Ошибка при выполнении команды: {e}")
            success = False
        
        # Обновляем глобальное состояние
        if success:
            self.device_states["last_command"] = command_description
            self.device_states["last_update"] = timestamp
            self.device_states["total_commands"] = self.device_states.get("total_commands", 0) + 1
        
        try:
            self.save_state()
        except Exception as e:
            print(f"⚠ Ошибка при сохранении состояния: {e}")
        
        return success
    
    def execute_commands(self, commands: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Выполнение списка команд - ТОЛЬКО ИЗМЕНЕНИЕ СОСТОЯНИЯ"""
        results = []
        for cmd in commands:
            if cmd.get('room') and cmd.get('command'):
                task = extract_task(cmd['command'])
                
                if task['action'] and task['object']:
                    success = self.execute_single_command(
                        room=cmd['room'],
                        action=task['action'],
                        device=task['object'],
                        value=task['value']
                    )
                    results.append({
                        'success': success,
                        'room': cmd['room'],
                        'action': task['action'],
                        'device': task['object'],
                        'value': task['value'],
                        'original': cmd['command']
                    })
        
        return results
    
    def show_status(self):
        """Показать текущее состояние всех устройств."""
        print("\n" + "="*60)
        print("ТЕКУЩЕЕ СОСТОЯНИЕ УСТРОЙСТВ")
        print("="*60)
        
        try:
            for room_name, devices in self.device_states.get("rooms", {}).items():
                print(f"\n📍 {room_name.upper()}:")
                for device_name, device_info in devices.items():
                    state = device_info.get('state', 'unknown')
                    if device_name == "свет":
                        brightness = device_info.get('brightness', 0)
                        print(f"  💡 Свет: {state} (яркость: {brightness}%)")
                    elif device_name == "температура":
                        value = device_info.get('value', 0)
                        print(f"  🌡️ Температура: {state} ({value}°C)")
                    elif device_name == "телевизор":
                        volume = device_info.get('volume', 0)
                        print(f"  📺 Телевизор: {state} (громкость: {volume}%)")
                    elif device_name in ["шторы", "жалюзи", "ролеты"]:
                        position = device_info.get('position', 0)
                        print(f"  🪟 {device_name.capitalize()}: {state} (позиция: {position}%)")
                    elif device_name == "кондиционер":
                        temp = device_info.get('temp', 0)
                        mode = device_info.get('mode', 'unknown')
                        print(f"  ❄️ Кондиционер: {state} ({temp}°C, режим: {mode})")
                    elif device_name == "вентилятор":
                        speed = device_info.get('speed', 0)
                        print(f"  💨 Вентилятор: {state} (скорость: {speed})")
            
            print(f"\n📊 Статистика:")
            print(f"  Последняя команда: {self.device_states.get('last_command', 'нет')}")
            print(f"  Последнее обновление: {self.device_states.get('last_update', 'нет')}")
            print(f"  Всего выполнено команд: {self.device_states.get('total_commands', 0)}")
        except Exception as e:
            print(f"⚠ Ошибка при отображении статуса: {e}")
        
        print("="*60)

def process_text_command(text: str, controller: HomeController = None):
    """Обработка текстовой команды - ТОЛЬКО АНАЛИЗ И ВЫПОЛНЕНИЕ, без записи аудио!"""
    print(f"\n📝 Текстовая команда: {text}")
    
    try:
        # Распознавание и обработка команды
        segments = segment_command(text)
        resolved_commands = resolve_location_reference(segments)
        
        print("\n📊 Анализ команды:")
        for i, cmd_info in enumerate(resolved_commands, 1):
            task = extract_task(cmd_info['command'])
            room_info = f" [Комната: {cmd_info['room']}]" if cmd_info['room'] else " [Комната не указана]"
            action_info = f" [Действие: {task['action']}]" if task['action'] else ""
            object_info = f" [Объект: {task['object']}]" if task['object'] else ""
            value_info = f" [Значение: {task['value']}]" if task['value'] else ""
            print(f"  {i}. {cmd_info['command']}{room_info}{action_info}{object_info}{value_info}")
        
        # Выполнение команд
        if controller:
            print("\n🚀 Выполнение команд:")
            try:
                results = controller.execute_commands(resolved_commands)
                successful = sum(1 for r in results if r['success'])
                print(f"\n✅ Успешно выполнено: {successful} из {len(results)} команд")
                
                # Показать обновленный статус
                controller.show_status()
            except Exception as e:
                print(f"⚠ Ошибка при выполнении команд: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠ Контроллер не доступен. Команды не выполнены.")
        
        return resolved_commands
    except Exception as e:
        print(f"⚠ Ошибка при обработке команды: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_voice_command_simple(controller: HomeController = None):
    """Упрощенная обработка голосовой команды"""
    z = 1
    try:
        # Создаем файл для записи
        TEST_FILE = os.path.join(TEST_DIR, f"voice_command_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        
        stt = SpeechToText(backend="vosk", model_path="models/asr/vosk/vosk-model-small-ru-0.22")
        
        print("\n🎤 Записываю команду (макс. 10 сек, автостоп при тишине)...")
        print("Говорите сейчас...")
        
        record_audio_vad(TEST_FILE, max_duration=10.0, pause_threshold=1.0)
        
        # Распознавание текста
        result = stt.transcribe(TEST_FILE)
        recognized_text = result['text'].strip()
        
        if not recognized_text:
            print("⚠ Не удалось распознать речь. Попробуйте еще раз.")
            try:
                os.unlink(TEST_FILE)
            except:
                pass
            return
        
        print(f"\n🗣️ Распознанный текст: {recognized_text}")
        
        if recognized_text in WAKE_WORDS:
            z = 0
            return
        # Обработка команды
        process_text_command(recognized_text, controller)
        
        # Удаляем временный файл
        os.unlink(TEST_FILE)
    except Exception as e:
        print(f"⚠ Ошибка при обработке голосовой команды: {e}")

def main():
    """Основная функция для тестирования wake word detection."""
    try:
        # Инициализируем контроллер устройств
        controller = HomeController()
        
        # Показываем начальное состояние
        controller.show_status()
        
        print("\n" + "="*60)
        print("ГОЛОСОВОЙ АССИСТЕНТ - КАРМА")
        print("="*60)
        
        detector = WakeWordDetector()
        
        while True:
            print("\nВыберите действие:")
            print("1. Активировать голосовой режим (слушаю 'Карма')")
            print("2. Ввести текстовую команду")
            print("3. Показать статус устройств")
            print("4. Выход")
            
            try:
                choice = input("\nВаш выбор (1-4): ").strip()
                
                if choice == "1":
                    print("\n🎧 Активирую голосовой режим...")
                    print("📢 Скажите 'Карма' для активации...")
                    
                    try:
                        # Упрощенный вызов wake word детектора
                        print("Слушаю wake word 'Карма'...")
                        detector.listen_for_wake_word(callback=lambda: process_voice_command_simple(controller))
                    except Exception as e:
                        print(f"⚠ Ошибка в голосовом режиме: {e}")
                    
                    # Проверяем, нужно ли полностью остановить скрипт
                    if getattr(detector, 'Стоп', False):
                        print("\n⏹️ Скрипт остановлен по команде пользователя.")
                        break
                    
                    print("\n🔁 Возвращаюсь в главное меню...")
                    
                    
                elif choice == "2":
                    text_command = input("\n📝 Введите текстовую команду: ").strip()
                    if text_command:
                        if text_command.lower() in ["выход", "exit", "quit"]:
                            break
                        process_text_command(text_command, controller)
                    else:
                        print("⚠ Команда не может быть пустой.")
                        
                elif choice == "3":
                    controller.show_status()
                    
                elif choice == "4":
                    print("\n👋 Выход из программы...")
                    break
                    
                else:
                    print("⚠ Неверный выбор. Попробуйте снова.")
                    
            except KeyboardInterrupt:
                print("\n\n⚠ Программа прервана пользователем (Ctrl+C)")
                break
            except Exception as e:
                print(f"\n⚠ Произошла ошибка: {e}")
    
    except Exception as e:
        print(f"⚠ Критическая ошибка при запуске программы: {e}")
        import traceback
        traceback.print_exc()
    
    # Показываем финальный статус
    print("\n" + "="*60)
    print("ФИНАЛЬНЫЙ СТАТУС СИСТЕМЫ")
    try:
        controller.show_status()
    except:
        print("⚠ Не удалось показать финальный статус")
    print("\n👋 До свидания!")
    print("="*60)

if __name__ == "__main__":
    main()