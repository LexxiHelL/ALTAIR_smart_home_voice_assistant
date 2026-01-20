#include <Wire.h>

#define BuzzerPin 9 // пин, управляющий пищалкой
#define BuzzerGndPin 9 // пин, минусового питания пищалкой
#include <Servo.h>
#include <OneWire.h>
#include <iarduino_HC_SR04_int.h>       // библиотека для работы с ультразвуковым датчиком расстояния HC-SR04 на Arduino
iarduino_HC_SR04_int sensor(2,3);    
Servo Okno;
OneWire ds(A2);
int a;
int d;
void setup() 
{
Okno.attach(12);
pinMode(8,OUTPUT);//нагрев горит диод отопления
pinMode(13,OUTPUT);//вентелятор 
 pinMode(7,OUTPUT);//звук бип
 pinMode(4,OUTPUT); //свет
 pinMode(11,INPUT);//включение сигнализации
 pinMode(6,INPUT);//включение сигнализаци
 a=0;
 d=0;
 Serial.begin(9600);
 pinMode(BuzzerGndPin, OUTPUT);
  digitalWrite(BuzzerGndPin, LOW);
  pinMode(BuzzerPin, OUTPUT); // пин управления пищалкой
}

void BeepAlarm(int d) // тревожный бип
{
  if (d==1) {
  for (int f = 1500; f >= 700; f--) {
    digitalWrite(BuzzerPin, HIGH);
    delayMicroseconds(f);
    digitalWrite(BuzzerPin, LOW);
    delayMicroseconds(f);}
     
  for (int f = 700; f <= 1500; f++) {
    digitalWrite(BuzzerPin, HIGH);
    delayMicroseconds(f);
    digitalWrite(BuzzerPin, LOW);
    delayMicroseconds(f);
  }
  }
   else
    {digitalWrite(BuzzerPin, LOW);}

}

void loop() 
{
if ((digitalRead(11) == LOW ) && (a==0)) {a=1;} //включение сигнализаци
 if (a==1)
 {digitalWrite(7,1);
 if (digitalRead(6) == HIGH ) d=1;
if (sensor.distance()<= 60) d=1;
delay(1000);
while ((digitalRead(11) == HIGH ) && (d==1)){
BeepAlarm(d); // тревожный бип
digitalWrite(4,1);
delay(1000);
digitalWrite(4,0);
delay(500);
}
 }
else{ d=0;
BeepAlarm(d); // тревожный бип
digitalWrite(7,0);
}
  if ((digitalRead(11) == LOW ) && (a==1)) {a=0;}//выключение сигнализации 
 delay(1000);
  byte data[2]; // РњРµСЃС‚Рѕ РґР»СЏ Р·РЅР°С‡РµРЅРёСЏ С‚РµРјРїРµСЂР°С‚СѓСЂС‹
  
  ds.reset(); // РќР°С‡РёРЅР°РµРј РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёРµ СЃРѕ СЃР±СЂРѕСЃР° РІСЃРµС… РїСЂРµРґС‹РґСѓС‰РёС… РєРѕРјР°РЅРґ Рё РїР°СЂР°РјРµС‚СЂРѕРІ
  ds.write(0xCC); // Р”Р°РµРј РґР°С‚С‡РёРєСѓ DS18b20 РєРѕРјР°РЅРґСѓ РїСЂРѕРїСѓСЃС‚РёС‚СЊ РїРѕРёСЃРє РїРѕ Р°РґСЂРµСЃСѓ. Р’ РЅР°С€РµРј СЃР»СѓС‡Р°Рµ С‚РѕР»СЊРєРѕ РѕРґРЅРѕ СѓСЃС‚СЂР№РѕСЃС‚РІРѕ 
  ds.write(0x44); // Р”Р°РµРј РґР°С‚С‡РёРєСѓ DS18b20 РєРѕРјР°РЅРґСѓ РёР·РјРµСЂРёС‚СЊ С‚РµРјРїРµСЂР°С‚СѓСЂСѓ. РЎР°РјРѕ Р·РЅР°С‡РµРЅРёРµ С‚РµРјРїРµСЂР°С‚СѓСЂС‹ РјС‹ РµС‰Рµ РЅРµ РїРѕР»СѓС‡Р°РµРј - РґР°С‚С‡РёРє РµРіРѕ РїРѕР»РѕР¶РёС‚ РІРѕ РІРЅСѓС‚СЂРµРЅРЅСЋСЋ РїР°РјСЏС‚СЊ
  
  delay(1000); // РњРёРєСЂРѕСЃС…РµРјР° РёР·РјРµСЂСЏРµС‚ С‚РµРјРїРµСЂР°С‚СѓСЂСѓ, Р° РјС‹ Р¶РґРµРј.  
  
  ds.reset(); // РўРµРїРµСЂСЊ РіРѕС‚РѕРІРёРјСЃСЏ РїРѕР»СѓС‡РёС‚СЊ Р·РЅР°С‡РµРЅРёРµ РёР·РјРµСЂРµРЅРЅРѕР№ С‚РµРјРїРµСЂР°С‚СѓСЂС‹
  ds.write(0xCC); 
  ds.write(0xBE); // РџСЂРѕСЃРёРј РїРµСЂРµРґР°С‚СЊ РЅР°Рј Р·РЅР°С‡РµРЅРёРµ СЂРµРіРёСЃС‚СЂРѕРІ СЃРѕ Р·РЅР°С‡РµРЅРёРµРј С‚РµРјРїРµСЂР°С‚СѓСЂС‹
  // РџРѕР»СѓС‡Р°РµРј Рё СЃС‡РёС‚С‹РІР°РµРј РѕС‚РІРµС‚
  data[0] = ds.read(); // Р§РёС‚Р°РµРј РјР»Р°РґС€РёР№ Р±Р°Р№С‚ Р·РЅР°С‡РµРЅРёСЏ С‚РµРјРїРµСЂР°С‚СѓСЂС‹
  data[1] = ds.read(); // Рђ С‚РµРїРµСЂСЊ СЃС‚Р°СЂС€РёР№
  // Р¤РѕСЂРјРёСЂСѓРµРј РёС‚РѕРіРѕРІРѕРµ Р·РЅР°С‡РµРЅРёРµ: 
  //    - СЃРїРµСЂРІР° "СЃРєР»РµРёРІР°РµРј" Р·РЅР°С‡РµРЅРёРµ, 
  //    - Р·Р°С‚РµРј СѓРјРЅРѕР¶Р°РµРј РµРіРѕ РЅР° РєРѕСЌС„С„РёС†РёРµРЅС‚, СЃРѕРѕС‚РІРµС‚СЃРІСѓСЋС‰РёР№ СЂР°Р·СЂРµС€Р°СЋС‰РµР№ СЃРїРѕСЃРѕР±РЅРѕСЃС‚Рё (РґР»СЏ 12 Р±РёС‚ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ - СЌС‚Рѕ 0,0625)
  float temperature =  ((data[1] << 8) | data[0]) * 0.0625;

if (temperature > 27)
{Okno.write(0);
digitalWrite(8,0);
digitalWrite(13,1);
}
else
{Okno.write(70);
digitalWrite(8,1);
digitalWrite(13,0);
}

if (sensor.distance()<= 60) 
{digitalWrite(4,1);}
else {digitalWrite(4,0);}
Serial.println(temperature);
Serial.println(sensor.distance());

Serial.println("==================");
}
