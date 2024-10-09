from .emv import EMV
from utime import ticks_us, time

# Initialize EMV instance
emv = EMV()

class TimeStamp:
    def __init__(self):
        """
        Initialize the TimeStamp class with parameters from the EMV configuration.
        """
        self.language_preference = emv.language_perference
        self.timestamp_tag = emv.timestamp_tag

    def value(self) -> str:
        """
        Generate the QR code data for the current timestamp.

        Returns:
        - str: Formatted QR code data including language preference, timestamp, and related tags.
        """
        # Get the current timestamp in milliseconds
        timestamp = str(1000000000000 + int(round(time() * 1000) + ticks_us() / 1000))

        # Format the length of the timestamp
        length_of_timestamp = str(len(timestamp))

        # Create the initial result with language preference and timestamp
        result = f"{self.language_preference}{length_of_timestamp}{timestamp}"

        # Format the length of the result
        length_result = f"{len(result):02d}"

        # Append the timestamp tag and formatted result
        return f"{self.timestamp_tag}{length_result}{result}"
