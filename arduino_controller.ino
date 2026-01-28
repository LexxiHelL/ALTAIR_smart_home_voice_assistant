#include <Wire.h>
#include <Servo.h>
#include <OneWire.h>
#include <iarduino_HC_SR04_int.h>

// Конфигурация пинов (можно менять через команды)
int lightPin = 4;
int windowServoPin = 12;
int heatingPin = 8;
int fanPin = 13;
int buzzerPin = 7;
int alarmActivatePin = 11;
int alarmSensorPin = 6;

// Датчики (фиксированные)
OneWire ds(A2); // Датчик температуры
iarduino_HC_SR04_int sensor(2, 3); // Датчик расстояния

// Сервопривод для окна
Servo windowServo;

// Глобальные переменные
int alarmActive = 0;
int alarmTriggered = 0;
float targetTemperature = 22.0; // Целевая температура по умолчанию
int windowAngle = 70; // Текущий угол окна

void setup() {
    // Инициализация сервопривода
    windowServo.attach(windowServoPin);
    windowServo.write(windowAngle);
    
    // Настройка пинов
    pinMode(lightPin, OUTPUT);
    pinMode(heatingPin, OUTPUT);
    pinMode(fanPin, OUTPUT);
    pinMode(buzzerPin, OUTPUT);
    pinMode(alarmActivatePin, INPUT_PULLUP);
    pinMode(alarmSensorPin, INPUT);
    
    // Инициализация пищалки
    pinMode(9, OUTPUT);
    digitalWrite(9, LOW);
    
    // Инициализация Serial
    Serial.begin(9600);
    
    // Установка начальных состояний
    digitalWrite(lightPin, LOW);
    digitalWrite(heatingPin, HIGH); // Отопление включено по умолчанию при t < 27
    digitalWrite(fanPin, LOW);
    digitalWrite(buzzerPin, LOW);
    
    delay(1000);
    Serial.println("READY");
}

void loop() {
    // Обработка Serial команд
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        processCommand(command);
    }
    
    // Автоматическое управление температурой
    autoTemperatureControl();
    
    // Управление сигнализацией
    alarmSystemControl();
    
    // Управление светом по датчику расстояния
    autoLightControl();
    
    // Отправка данных с датчиков
    sendSensorData();
    
    delay(100);
}

void processCommand(String command) {
    Serial.print("Received: ");
    Serial.println(command);
    
    if (command == "PING") {
        Serial.println("PONG");
        return;
    }
    
    // Разбор команд SET:type:pin:value
    if (command.startsWith("SET:")) {
        int colon1 = command.indexOf(':');
        int colon2 = command.indexOf(':', colon1 + 1);
        int colon3 = command.indexOf(':', colon2 + 1);
        
        if (colon1 != -1 && colon2 != -1 && colon3 != -1) {
            String type = command.substring(colon1 + 1, colon2);
            String pinStr = command.substring(colon2 + 1, colon3);
            String valueStr = command.substring(colon3 + 1);
            
            int pin = pinStr.toInt();
            int value = valueStr.toInt();
            
            if (type == "light") {
                controlLight(pin, value);
            } else if (type == "servo") {
                controlServo(pin, value);
            } else if (type == "heating") {
                controlHeating(pin, value);
            } else if (type == "fan") {
                controlFan(pin, value);
            } else if (type == "alarm") {
                controlAlarm(pin, value);
            } else {
                Serial.println("ERROR: Unknown device type");
            }
        } else if (command.startsWith("SET:target_temp:")) {
            // Установка целевой температуры
            int colon = command.indexOf(':');
            String tempStr = command.substring(colon + 1);
            targetTemperature = tempStr.toFloat();
            Serial.println("OK: Target temperature set");
        } else {
            Serial.println("ERROR: Invalid command format");
        }
    } else {
        Serial.println("ERROR: Unknown command");
    }
}

void controlLight(int pin, int value) {
    digitalWrite(pin, value == 1 ? HIGH : LOW);
    Serial.print("OK: Light ");
    Serial.println(value == 1 ? "ON" : "OFF");
}

void controlServo(int pin, int angle) {
    if (pin == windowServoPin) {
        windowAngle = constrain(angle, 0, 180);
        windowServo.write(windowAngle);
        Serial.print("OK: Window angle set to ");
        Serial.println(windowAngle);
    } else {
        Serial.println("ERROR: Invalid servo pin");
    }
}

void controlHeating(int pin, int value) {
    digitalWrite(pin, value == 1 ? HIGH : LOW);
    Serial.print("OK: Heating ");
    Serial.println(value == 1 ? "ON" : "OFF");
}

void controlFan(int pin, int value) {
    digitalWrite(pin, value == 1 ? HIGH : LOW);
    Serial.print("OK: Fan ");
    Serial.println(value == 1 ? "ON" : "OFF");
}

void controlAlarm(int pin, int value) {
    if (pin == alarmActivatePin) {
        alarmActive = value;
        Serial.print("OK: Alarm ");
        Serial.println(value == 1 ? "ACTIVATED" : "DEACTIVATED");
    } else {
        Serial.println("ERROR: Invalid alarm pin");
    }
}

void autoTemperatureControl() {
    float temperature = readTemperature();
    
    if (temperature > targetTemperature + 2) {
        // Температура выше целевой - открываем окно, выключаем отопление, включаем вентилятор
        if (windowAngle < 180) {
            windowAngle = min(windowAngle + 10, 180);
            windowServo.write(windowAngle);
        }
        digitalWrite(heatingPin, LOW);
        digitalWrite(fanPin, HIGH);
    } else if (temperature < targetTemperature - 2) {
        // Температура ниже целевой - закрываем окно, включаем отопление, выключаем вентилятор
        if (windowAngle > 0) {
            windowAngle = max(windowAngle - 10, 0);
            windowServo.write(windowAngle);
        }
        digitalWrite(heatingPin, HIGH);
        digitalWrite(fanPin, LOW);
    } else {
        // Температура в пределах нормы - оставляем как есть
        digitalWrite(fanPin, LOW);
    }
}

float readTemperature() {
    byte data[2];
    
    ds.reset();
    ds.write(0xCC);
    ds.write(0x44);
    
    delay(100);
    
    ds.reset();
    ds.write(0xCC);
    ds.write(0xBE);
    
    data[0] = ds.read();
    data[1] = ds.read();
    
    return ((data[1] << 8) | data[0]) * 0.0625;
}

void alarmSystemControl() {
    // Включение/выключение сигнализации
    if (digitalRead(alarmActivatePin) == LOW && alarmActive == 0) {
        alarmActive = 1;
        Serial.println("INFO: Alarm activated manually");
    }
    
    if (alarmActive == 1) {
        digitalWrite(buzzerPin, HIGH);
        
        // Проверка датчика движения
        if (digitalRead(alarmSensorPin) == HIGH) {
            alarmTriggered = 1;
        }
        
        // Проверка датчика расстояния
        if (sensor.distance() <= 60) {
            alarmTriggered = 1;
        }
        
        delay(1000);
        
        // Если сработала тревога
        if (alarmTriggered == 1) {
            triggerAlarm();
        }
    } else {
        alarmTriggered = 0;
        digitalWrite(buzzerPin, LOW);
        beepAlarm(0);
    }
    
    if (digitalRead(alarmActivatePin) == LOW && alarmActive == 1) {
        alarmActive = 0;
        Serial.println("INFO: Alarm deactivated manually");
    }
    
    delay(1000);
}

void triggerAlarm() {
    // Мигание светом и звуковая сигнализация
    while (alarmTriggered == 1 && digitalRead(alarmActivatePin) == HIGH) {
        beepAlarm(1);
        digitalWrite(lightPin, HIGH);
        delay(1000);
        digitalWrite(lightPin, LOW);
        delay(500);
    }
}

void beepAlarm(int d) {
    if (d == 1) {
        for (int f = 1500; f >= 700; f--) {
            digitalWrite(buzzerPin, HIGH);
            delayMicroseconds(f);
            digitalWrite(buzzerPin, LOW);
            delayMicroseconds(f);
        }
        
        for (int f = 700; f <= 1500; f++) {
            digitalWrite(buzzerPin, HIGH);
            delayMicroseconds(f);
            digitalWrite(buzzerPin, LOW);
            delayMicroseconds(f);
        }
    } else {
        digitalWrite(buzzerPin, LOW);
    }
}

void autoLightControl() {
    if (sensor.distance() <= 60) {
        digitalWrite(lightPin, HIGH);
    } else {
        // Не выключаем свет, если он был включен вручную
        // Для этого нужно отслеживать состояние
    }
}

void sendSensorData() {
    float temperature = readTemperature();
    int distance = sensor.distance();
    
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print(", Distance: ");
    Serial.println(distance);
    
    // Отправляем дополнительные данные каждые 5 секунд
    static unsigned long lastSend = 0;
    if (millis() - lastSend > 5000) {
        Serial.print("STATUS: Light=");
        Serial.print(digitalRead(lightPin) ? "ON" : "OFF");
        Serial.print(", Heating=");
        Serial.print(digitalRead(heatingPin) ? "ON" : "OFF");
        Serial.print(", Fan=");
        Serial.print(digitalRead(fanPin) ? "ON" : "OFF");
        Serial.print(", Window=");
        Serial.print(windowAngle);
        Serial.print(", Alarm=");
        Serial.println(alarmActive ? "ACTIVE" : "INACTIVE");
        
        lastSend = millis();
    }
}
