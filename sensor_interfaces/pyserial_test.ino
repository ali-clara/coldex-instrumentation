// Serial read stuff
const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data
boolean newData = false;
int dataNumber = 0;

// Define input options - the serial message will come in from Pyserial as an integer, but that's not
// very human-readable
#define one_thing 1
#define another_thing 2


void setup() {
  Serial.begin(115200);
  while (!Serial);
  clearInputBuffer();

  delay(100);
}

void loop() {
  recvWithStartEndMarker();
  parseCommands();
}

void recvWithStartEndMarker() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();
    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }
    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

void parseCommands() {
  int c = 0;
  int c_idx = 0;
  int t_idx = 0;
  char temp[32];

  if (newData == true) {
    // Convert serial monitor value to int and cast as float
    int len = strlen(receivedChars);
    c = (float) atoi(receivedChars);
    newData = false;

    // Manage the serial input accordingly
    if (c == one_thing){
      doOneThing();
    }
    else if (c == another_thing){
      doAnotherThing();
    }
    else{
      Serial.println("Unknown input recieved");
    }
  }
}

void doOneThing(){
  Serial.println("Arduino: one thing");
}

void doAnotherThing(){
  Serial.println("Arduino: another thing");
}

void testInput(float c){
  Serial.println("recieved input");
}

void sendIntSerial(int x) {
  uint8_t LSB = x;
  uint8_t MSB = x >> 8;
  Serial.write(MSB);
  Serial.write(LSB);
}

void clearInputBuffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}