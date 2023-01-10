#define contact_pin 2
void setup() {
  // put your setup code here, to run once:
  Serial.begin(1152000);
  pinMode(contact_pin, INPUT_PULLUP);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println(digitalRead(contact_pin));
  delayMicroseconds(10);
}
