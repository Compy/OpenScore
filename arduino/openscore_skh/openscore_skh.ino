/*
 * OpenScore Arduino Hardware Interface
 */

#include <avr/wdt.h>

String inputString = "";
boolean stringComplete = false;
char EOL_CHAR = '\n';
boolean debug = false;
boolean do_restart = false;

/*
 * Set up serial port and reserve memory space
 *
 * Also set up watchdog timer
 */
void setup()
{
  // Initialize serial
  Serial.begin(9600);
  
  resetIOPins();
  
  if (debug)
  {
    Serial.println("Starting OpenScore hardware controller...");
  }
  wdt_enable(WDTO_1S);
  // Reserve 200 bytes for the input string
  inputString.reserve(200);
}

void resetIOPins()
{
  // Reset pins to a known state
  for (int i = 3; i < 14; i++)
  {
    pinMode(i, OUTPUT);
  }
  for (int i = 3; i < 14; i++)
  {
    digitalWrite(i, LOW);
  } 
}

/*
 * Main event loop, hand read serial data to processor when the complete flag is marked
 */
void loop()
{
  // If our string is complete, pass data to the command processor
  if (stringComplete)
  {
    processCommand(inputString);
    // Reset values to read another serial command
    inputString = "";
    stringComplete = false;
  }
  if (!do_restart)
  {
    // Tickle the watchdog
    wdt_reset();
  }
}

/*
 * Raised when a serial event occurs. This allows us to read serial data from the controller
 * program asynchronously.
 */
void serialEvent()
{
  while (Serial.available())
  {
    char inChar = (char)Serial.read();
    if (inChar == '\r') continue;
    if (inChar == EOL_CHAR)
    {
      stringComplete = true;
    }
    else
    {
      inputString += inChar;
    }
  }
}

void processCommand(String cmd)
{
  if (debug)
  {
    Serial.print("Got CMD: \"");
    Serial.print(cmd);
    Serial.println("\"");
  }
  
  if (cmd.length() > 1)
  {
    String command = cmd.substring(0,2);
    if (command == "RS")
    {
      // Reset
      resetIOPins();
      do_restart = true;
    }
    else if (command == "HL")
    {
      Serial.println("HL");
    }
    else if (command == "WD" || command == "RD" || command == "WA" || command == "RA")
    {
      String pin = cmd.substring(2,4);
      int pNum = pin.toInt();
      int mode = 0;
      if (cmd.length() > 4)
        mode = cmd.substring(4).toInt();
        
      if (command == "WD") WriteDigital(pNum, mode);
      if (command == "RD") Serial.println(ReadDigital(pNum));
    }
  }
}

void WriteDigital(int pin, int mode)
{
  if (debug)
  {
    Serial.print("Setting pin ");
    Serial.print(pin);
    Serial.print(" to ");
    Serial.println(mode);
  }
  digitalWrite(pin, mode);
}

int ReadDigital(int pin)
{
  int val = digitalRead(pin);
  if (debug)
  {
    Serial.print("Pin ");
    Serial.print(pin);
    Serial.print(" is " );
    Serial.println(val);
  }
  return val;
}
