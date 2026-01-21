"""
Модуль для извлечения информации о комнатах/локациях из голосовых команд и разрешения анафор.
"""
import re
from typing import List, Dict, Optional
# Список известных комнат/локаций (в именительном падеже)
KNOWN_ROOMS = [
    "гостиная", "спальня", "кухня", "ванная", "туалет", "коридор", "прихожая",
    "балкон", "лоджия", "кабинет", "детская", "столовая", "зал"
]

# Падежные окончания для комнат (родительный, дательный, винительный, творительный, предложный)
CASE_ENDINGS = {
    "гостиная": ["гостиной", "гостиную", "гостиной", "гостиной"],
    "спальня": ["спальни", "спальню", "спальней", "спальне"],
    "кухня": ["кухни", "кухню", "кухней", "кухне"],
    "ванная": ["ванной", "ванную", "ванной", "ванной"],
    "туалет": ["туалета", "туалету", "туалетом", "туалете"],
    "коридор": ["коридора", "коридору", "коридором", "коридоре"],
    "прихожая": ["прихожей", "прихожую", "прихожей", "прихожей"],
    "балкон": ["балкона", "балкону", "балконом", "балконе"],
    "лоджия": ["лоджии", "лоджию", "лоджией", "лоджии"],
    "кабинет": ["кабинета", "кабинету", "кабинетом", "кабинете"],
    "детская": ["детской", "детскую", "детской", "детской"],
    "столовая": ["столовой", "столовую", "столовой", "столовой"],
    "зал": ["зала", "залу", "залом", "зале"]
}

# Местоимения, которые могут ссылаться на предыдущую комнату
LOCATION_PRONOUNS = ["там", "туда", "в ней", "в нем", "там же", "в той же", "в этой", "и там же", "и там"]

def extract_room(text: str) -> Optional[str]:
    """
    Извлекает название комнаты из текста команды.
    Возвращает None, если комната не найдена.
    Учитывает падежные формы комнат.
    """
    text_lower = text.lower()
    
    # Сначала ищем именительный падеж
    for room in KNOWN_ROOMS:
        if room in text_lower:
            return room
    
    # Ищем падежные формы
    for room in KNOWN_ROOMS:
        if room in CASE_ENDINGS:
            for case_form in CASE_ENDINGS[room]:
                if case_form in text_lower:
                    return room
    
    # Ищем с предлогами "в", "на"
    for room in KNOWN_ROOMS:
        if f"в {room}" in text_lower or f"на {room}" in text_lower:
            return room
        if room in CASE_ENDINGS:
            for case_form in CASE_ENDINGS[room]:
                if f"в {case_form}" in text_lower or f"на {case_form}" in text_lower:
                    return room
    
    return None

def resolve_location_reference(segments: List[str]) -> List[Dict[str, str]]:
    """
    Обрабатывает список сегментов команд, извлекая комнаты и разрешая анафоры.
    Возвращает список словарей с полями: 'command', 'room', 'original_text'
    """
    resolved = []
    last_room = None
    previous_had_reference = False  # Флаг, что предыдущий сегмент содержал "там же" и т.д.
    
    for i, segment in enumerate(segments):
        segment_lower = segment.lower()
        room = extract_room(segment)
        
        # Проверяем, есть ли местоимение, указывающее на предыдущую комнату
        has_pronoun = any(pronoun in segment_lower for pronoun in LOCATION_PRONOUNS)
        
        # Проверяем, заканчивается ли сегмент на "там же" или подобное
        ends_with_reference = any(segment_lower.endswith(pronoun) or 
                                  segment_lower.endswith(f" {pronoun}") 
                                  for pronoun in ["там же", "и там же", "там", "и там"])
        
        if room:
            # Нашли явное упоминание комнаты
            last_room = room
            previous_had_reference = ends_with_reference
            resolved.append({
                'command': segment,
                'room': room,
                'original_text': segment
            })
        elif has_pronoun and last_room:
            # Нашли местоимение, используем последнюю упомянутую комнату
            previous_had_reference = ends_with_reference
            resolved.append({
                'command': segment,
                'room': last_room,
                'original_text': segment
            })
        elif previous_had_reference and last_room:
            # Предыдущий сегмент заканчивался на "там же", наследуем комнату
            previous_had_reference = False
            resolved.append({
                'command': segment,
                'room': last_room,
                'original_text': segment
            })
        elif last_room and i > 0:
            # Если в предыдущем сегменте была комната, а в текущем нет явного упоминания другой комнаты,
            # наследуем комнату из предыдущего сегмента
            previous_had_reference = False
            resolved.append({
                'command': segment,
                'room': last_room,
                'original_text': segment
            })
        else:
            # Комната не указана
            previous_had_reference = False
            resolved.append({
                'command': segment,
                'room': None,
                'original_text': segment
            })
    
    return resolved

