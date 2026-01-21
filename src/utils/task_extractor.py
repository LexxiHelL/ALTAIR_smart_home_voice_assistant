"""
Модуль для извлечения задачи (действие + объект) из голосовых команд.
"""
import re
from typing import Dict, Optional, List

# Словарь действий и их синонимов
ACTIONS = {
    "включи": ["включи", "запусти", "активируй", "включить"],
    "выключи": ["выключи", "отключи", "деактивируй", "выключить", "останови"],
    "открой": ["открой", "открыть", "раскрой"],
    "закрой": ["закрой", "закрыть"],
    "поставь": ["поставь", "установи", "настрой", "поставить", "установить", "настроить"],
    "увеличь": ["увеличь", "повысь", "подними", "увеличить", "повысить", "поднять"],
    "уменьши": ["уменьши", "понизь", "опусти", "уменьшить", "понизить", "опустить"],
    "измени": ["измени", "поменяй", "изменить", "поменять"],
    "сохрани": ["сохрани", "сохранить"],
    "переключи": ["переключи", "переключить"],
    "покажи": ["покажи", "показать", "выведи", "вывести"],
    "найди": ["найди", "найти", "найди мне"]
}

# Словарь объектов и их синонимов
OBJECTS = {
    "свет": ["свет", "освещение", "лампу", "лампы", "лампочку", "лампочки"],
    "телевизор": ["телевизор", "тв", "телик", "телевизора"],
    "температура": ["температура", "температуру", "температуре", "градусы", "градусов", "градуса"],
    "кондиционер": ["кондиционер", "кондиционера", "кондиционеру"],
    "обогреватель": ["обогреватель", "обогревателя", "обогревателю", 'батарея', 'батареи'],
    "шторы": ["шторы", "штора", "штор", "занавески", "занавесок"],
    "окно": ["окно", "окна", "окну"],
    "дверь": ["дверь", "двери", "дверь"],
    "музыка": ["музыка", "музыку", "музыке", "музыки", "песня", "песню"],
    "радио": ["радио"],
    "вентилятор": ["вентилятор", "вентилятора", "вентилятору"],
    "громкость": ["громкость", "громкости", "громкостью", "звук", "звука", "звуку", "звуком"]
}

# Словарь для преобразования текстовых числительных в числа
NUMBER_WORDS = {
    "ноль": 0, "один": 1, "два": 2, "три": 3, "четыре": 4, "пять": 5,
    "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10,
    "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13, "четырнадцать": 14,
    "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17, "восемнадцать": 18,
    "девятнадцать": 19, "двадцать": 20, "тридцать": 30, "сорок": 40,
    "пятьдесят": 50, "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80,
    "девяносто": 90, "сто": 100, "двести": 200, "триста": 300, "четыреста": 400,
    "пятьсот": 500, "шестьсот": 600, "семьсот": 700, "восемьсот": 800,
    "девятьсот": 900, "тысяча": 1000
}

def text_to_number(text: str) -> Optional[int]:
    """
    Преобразует текстовое числительное в число.
    Например: "двадцать два" → 22, "тридцать пять" → 35
    """
    text_lower = text.lower().strip()
    
    # Сначала проверяем точное совпадение
    if text_lower in NUMBER_WORDS:
        return NUMBER_WORDS[text_lower]
    
    # Разбиваем на слова и ищем составные числа
    words = text_lower.split()
    total = 0
    
    for word in words:
        if word in NUMBER_WORDS:
            total += NUMBER_WORDS[word]
    
    return total if total > 0 else None

def extract_action(text: str) -> Optional[str]:
    """
    Извлекает действие из текста команды.
    Возвращает каноническое название действия или None.
    """
    text_lower = text.lower()
    for action, synonyms in ACTIONS.items():
        for synonym in synonyms:
            if synonym in text_lower:
                return action
    return None

def extract_object(text: str) -> Optional[str]:
    """
    Извлекает объект из текста команды.
    Возвращает каноническое название объекта или None.
    """
    text_lower = text.lower()
    for obj, synonyms in OBJECTS.items():
        for synonym in synonyms:
            if synonym in text_lower:
                return obj
    return None

def extract_value(text: str) -> Optional[str]:
    """
    Извлекает значение/параметр из команды (например, "22 градуса", "двадцать два градуса", "на 5").
    Поддерживает как цифровые, так и текстовые числительные.
    """
    text_lower = text.lower()
    
    # Сначала ищем цифровые числа
    numbers = re.findall(r'\d+', text)
    if numbers:
        # Ищем единицы измерения или контекст
        if "градус" in text_lower:
            return f"{numbers[0]} градусов"
        elif "процент" in text_lower or "%" in text or "громкость" in text_lower or "звук" in text_lower:
            return f"{numbers[0]}%"
        else:
            return numbers[0]
    
    # Ищем текстовые числительные для процентов (громкость)
    if "процент" in text_lower or "%" in text_lower or ("громкость" in text_lower or "звук" in text_lower):
        # Извлекаем часть текста до "процент" или ищем числительное перед "громкость"/"звук"
        if "процент" in text_lower:
            parts = text_lower.split("процент")[0].strip()
        else:
            # Ищем числительное перед "громкость" или "звук"
            parts = ""
            words = text_lower.split()
            for i, word in enumerate(words):
                if word in ["громкость", "звук", "звука", "звуку", "звуком"]:
                    if i > 0:
                        # Берем предыдущие 1-3 слова
                        start = max(0, i - 3)
                        parts = " ".join(words[start:i])
                    break
        
        if parts:
            number = text_to_number(parts)
            if number is not None:
                return f"{number}%"
            # Если не нашли, пробуем найти в последних 2-3 словах
            words = parts.split()
            if len(words) >= 2:
                for i in range(len(words) - 2, len(words)):
                    if i >= 0:
                        phrase = " ".join(words[i:])
                        number = text_to_number(phrase)
                        if number is not None:
                            return f"{number}%"
    
    # Ищем текстовые числительные
    # Ищем фразы типа "двадцать два градуса", "тридцать пять градусов"
    if "градус" in text_lower:
        # Извлекаем часть текста до "градус"
        parts = text_lower.split("градус")[0].strip()
        # Пробуем найти числительное в этой части
        number = text_to_number(parts)
        if number is not None:
            return f"{number} градусов"
        # Если не нашли, пробуем найти в последних 2-3 словах перед "градус"
        words = parts.split()
        if len(words) >= 2:
            # Пробуем последние 2-3 слова
            for i in range(len(words) - 2, len(words)):
                if i >= 0:
                    phrase = " ".join(words[i:])
                    number = text_to_number(phrase)
                    if number is not None:
                        return f"{number} градусов"
    
    # Ищем текстовые числительные без единиц измерения
    # Пробуем найти числительное в тексте
    words = text_lower.split()
    for i in range(len(words)):
        for j in range(i + 1, min(i + 4, len(words) + 1)):  # Проверяем фразы до 3 слов
            phrase = " ".join(words[i:j])
            number = text_to_number(phrase)
            if number is not None:
                return str(number)
    
    # Ищем текстовые значения
    if "максимум" in text_lower or "максимально" in text_lower or "на полную" in text_lower:
        return "максимум"
    if "минимум" in text_lower or "минимально" in text_lower:
        return "минимум"
    if "тихо" in text_lower or "тише" in text_lower:
        return "тихо"
    if "громко" in text_lower or "громче" in text_lower:
        return "громко"
    
    return None

def extract_task(segment: str) -> Dict[str, Optional[str]]:
    """
    Извлекает полную задачу из сегмента команды.
    Возвращает словарь с полями: 'action', 'object', 'value', 'full_text'
    """
    return {
        'action': extract_action(segment),
        'object': extract_object(segment),
        'value': extract_value(segment),
        'full_text': segment
    }

def extract_tasks_from_segments(segments: List[str]) -> List[Dict[str, Optional[str]]]:
    """
    Извлекает задачи из списка сегментов команд.
    """
    return [extract_task(segment) for segment in segments]

