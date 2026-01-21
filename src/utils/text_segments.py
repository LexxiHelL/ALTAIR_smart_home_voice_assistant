"""
Модуль для разбивки распознанного текста на сегменты команды (токенизация, выделение основных частей для последующей обработки).
"""
import re
from typing import List

# Типовой список глаголов команд (расширяемый)
COMMAND_VERBS = [
    "включи", "выключи", "открой", "закрой", "установи", "сделай", "поставь", "запусти", "останови", "увеличь", "уменьши",
    "убавь", "добавь", "измени", "подними", "опусти", "сохрани", "переключи", "переведи"
]

def segment_command(text: str) -> List[str]:
    """
    Разбивка по глаголам, объединяя фрагменты без глагола с предыдущей командой.
    Например:
    "включи свет и открой шторы, затем выключи телевизор и поставь температуру 22"
    → [
        'включи свет',
        'открой шторы',
        'выключи телевизор',
        'поставь температуру 22'
    ]
    """
    COMMAND_VERBS = [
        "включи", "выключи", "открой", "закрой", "установи", "сделай", "поставь", "запусти",
        "останови", "увеличь", "уменьши", "убавь", "добавь", "измени", "подними", "опусти",
        "сохрани", "переключи", "переведи"
    ]
    segments = re.split(r'(?=\b(?:' + '|'.join(COMMAND_VERBS) + r')\b)', text, flags=re.IGNORECASE)
    result = []
    buffer = ''
    for seg in segments:
        seg = seg.strip(' ,.;\n')
        if not seg:
            continue
        if re.match(r'^(' + '|'.join(COMMAND_VERBS) + r')\b', seg, flags=re.IGNORECASE):
            if buffer:
                result.append(buffer.strip())
            buffer = seg
        else:
            buffer += ' ' + seg
    if buffer:
        result.append(buffer.strip())

    def clean_segment(text: str) -> str:
        return re.sub(r'(и|затем|потом)\s*$', '', text.strip(), flags=re.IGNORECASE).strip()
    return [clean_segment(r) for r in result if clean_segment(r)]


# Пример:
# segments = segment_command("Включи свет в гостиной и выключи телевизор.")
# print(segments)  # ['Включи свет в гостиной', 'выключи телевизор']

