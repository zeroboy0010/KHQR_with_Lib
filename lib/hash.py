import hashlib
import ubinascii

# MD5 implementation for MicroPython
def qr_to_md5(qr_string):
    # Convert QR string to bytes
    qr_bytes = qr_string.encode('utf-8')
    
    # Compute MD5 hash
    md5_hash = hashlib.md5(qr_bytes).digest()
    
    # Convert the binary hash to a hexadecimal string
    md5_hex = ubinascii.hexlify(md5_hash).decode('utf-8')
    
    return md5_hex

    
class HASH:
    def __init__(self):
        """
        Initialize the HASH class.
        """
        pass

    def md5(self, data: str) -> str:
        """
        Generate an MD5 hash for the given data.

        Args:
        - data (str): The data to hash.

        Returns:
        - str: The hexadecimal MD5 hash of the input data.

        Raises:
        - TypeError: If `data` is not a string.
        """
        if not isinstance(data, str):
            raise TypeError("Data must be a string.")
        
        # Generate and return the MD5 hash of the input data
        return qr_to_md5(data)
