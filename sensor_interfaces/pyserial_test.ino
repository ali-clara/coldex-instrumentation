// Serial read parameters
const byte numChars = 32; // expected maximum input length: 32 bits
char receivedChars[numChars];   // an array to store the received data
boolean newData = false;  // flag to keep track of if we have new data to process or not

// Define input options - the serial message will come in from Pyserial as an integer, but that's not
// very human-readable
#define one_thing 1
#define another_thing 2

#define pinLow 00
#define pinHigh 01
char delimiter = ";"

// Make sure the serial is set up
void setup() {
  Serial.begin(115200);
  while (!Serial); // Wait out until serial starts up
  clearInputBuffer();
  delay(100);
}

// Then loop forever reading serial input
void loop() {
  recvWithStartEndMarker();
  parseCommands();
}

// Function to accept and retain serial input
void recvWithStartEndMarker() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  // Loop through the serial message until we receive an end character.
  while (Serial.available() > 0 && newData == false) {
    // Read one byte.
    rc = Serial.read(); 
    // If we're currently reading data:
    if (recvInProgress == true) {
      // If we haven't received an "end" char, 
      if (rc != endMarker) {
        // Add the char to our data array and increase the index.
        receivedChars[ndx] = rc;
        ndx++;
        // If we've received more than the expected 32 bits, no we haven't.
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      // Otherwise, we've received an "end" char.
      else {
        // Terminate the string
        receivedChars[ndx] = '\0'; 
        // Reset the flags for the next command
        recvInProgress = false; 
        ndx = 0;
        newData = true;
      }
    }
    // Otherwise, check if the character is our "start" char. If so, we should start reading data...
    else if (rc == startMarker) {
      // So set that flag appropriately.
      recvInProgress = true;
    }
  }
}

// Function to process serial input
void parseCommands() {
  int c = 0;
  int c_idx = 0;
  int t_idx = 0;
  char temp[32];

  // If we have new data to process
  if (newData == true) {
    // Convert serial monitor value to int and cast as float
    // int len = strlen(receivedChars);
    // c = (float) atoi(receivedChars);

    // Reset the new data flag
    newData = false;

    // I THINK this splits the input into substrings depending on delimiter, but will need to 
    // test it when actually plugged into an arduino
    char * p_substring;
    // printf ("Splitting string \"%s\" into tokens:\n",receivedChars);
    p_substring = strtok(receivedChars, delimiter);
    int command = strlen(p_substring[0])
    int command_input = strlen(p_substring[1])

    // Loop through pch
    // while (p_substring != NULL)
    // {
    //   printf("%s\n",p_substring);
    //   p_substring = strtok(NULL, " ,.-");
    // }

    // Manage the serial input accordingly
    if (c == pinLow){
      setPinLow(command_input);
    }
    else if (c == pinHigh){
      setPinHigh(command_input);
    }
    else{
      Serial.println("Unknown input received");
    }
  }
}

void setPinLow(int pin){
  Serial.println("Setting pin low");
  digitalWrite(pin, LOW)
}

void setPinHigh(int pin){
  Serial.println("Setting pin high");
  digitalWrite(pin, HIGH)
}

void clearInputBuffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}