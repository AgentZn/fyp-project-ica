import os
import logging
from OpenSSL import crypto

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IFileManager:
    """Interface for File Management."""
    def file_exists(self, filename):
        raise NotImplementedError

    def save_to_file(self, filename, content, mode):
        raise NotImplementedError


class FileManager(IFileManager):
    """File Manager class implementing IFileManager."""

    @staticmethod
    def file_exists(filename):
        """Check if a file exists."""
        return os.path.exists(filename)

    @staticmethod
    def save_to_file(filename, content, mode="wb"):
        """Utility function to save content to a file."""
        with open(filename, mode) as file:
            file.write(content)
        logger.info(f"Saved content to {filename} successfully.")


class IConfiguration:
    """Interface for Configuration Management."""
    def get_configuration(self):
        raise NotImplementedError


class FileConfiguration(IConfiguration):
    """Configuration class for file names and settings."""

    def get_configuration(self):
        """Retrieve configuration settings."""
        return {
            "cert_filename": "cert.pem",
            "key_filename": "key.pem",
            "organization": "Development",
            "serial_number": 1000,
            "validity_days": 365,
            "key_bits": 4096
        }


class KeyPair:
    """Handles Key Pair operations."""

    def __init__(self, bits=4096):
        self.key = crypto.PKey()
        self.bits = bits

    def generate(self):
        """Generate an RSA key pair."""
        logger.info(f"Generating RSA key pair with {self.bits} bits...")
        self.key.generate_key(crypto.TYPE_RSA, self.bits)

    def get_key(self):
        return self.key


class Certificate:
    """Handles Certificate operations."""

    def __init__(self, key, organization, serial_number, validity_days):
        self.cert = crypto.X509()
        self.key = key
        self.organization = organization
        self.serial_number = serial_number
        self.validity_days = validity_days

    def setup(self):
        """Setup certificate parameters."""
        self.cert.get_subject().O = self.organization
        self.cert.set_serial_number(self.serial_number)
        self.cert.gmtime_adj_notBefore(0)
        self.cert.gmtime_adj_notAfter(self.validity_days * 24 * 60 * 60)
        self.cert.set_issuer(self.cert.get_subject())
        self.cert.set_pubkey(self.key.get_key())
        self.cert.sign(self.key.get_key(), 'sha256')

    def get_certificate(self):
        return self.cert


class CertificateManager:
    """Main Manager class for certificate and key operations."""

    def __init__(self, config):
        self.config = config.get_configuration()
        self.key = KeyPair(self.config["key_bits"])
        self.cert = Certificate(self.key, self.config["organization"], self.config["serial_number"], self.config["validity_days"])

    def generate_and_save(self):
        """Generate and save the certificate and key."""
        if not (FileManager.file_exists(self.config["cert_filename"]) and FileManager.file_exists(self.config["key_filename"])):
            self.key.generate()
            self.cert.setup()
            FileManager.save_to_file(self.config["cert_filename"], crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert.get_certificate()))
            FileManager.save_to_file(self.config["key_filename"], crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key.get_key()))
        else:
            logger.warning("Certificate and key files already exist.")


# Execution
if __name__ == "__main__":
    config = FileConfiguration()
    manager = CertificateManager(config)
    manager.generate_and_save()
