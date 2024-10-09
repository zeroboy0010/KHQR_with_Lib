import network
import urequests as requests
import ujson as json
from utime import sleep, ticks_us, time, mktime


from .crc import CRC
from .mcc import MCC
from .hash import HASH
from .amount import Amount
from .timestamp import TimeStamp
from .country_code import CountryCode
from .merchant_city import MerchantCity
from .merchant_name import MerchantName
from .point_of_initiation import PointOfInitiation
from .transaction_currency import TransactionCurrency
from .additional_data_field import AdditionalDataField
from .payload_format_indicator import PayloadFormatIndicator
from .global_unique_identifier import GlobalUniqueIdentifier

import gc

class KHQR:
    def __init__(self, bakong_token: str):
        self.crc = CRC()
        self.mcc = MCC()
        self.hash = HASH()
        self.amount = Amount()
        self.timestamp = TimeStamp()
        self.country_code = CountryCode()
        self.merchant_city = MerchantCity()
        self.merchant_name = MerchantName()
        self.point_of_initiation = PointOfInitiation()
        self.transaction_currency = TransactionCurrency()
        self.additional_data_field = AdditionalDataField()
        self.payload_format_indicator = PayloadFormatIndicator()
        self.global_unique_identifier = GlobalUniqueIdentifier()
        self.bakong_token = bakong_token
        self.bakong_api = 'https://api-bakong.nbc.gov.kh/v1'
    
    def create_qr(
        self,
        bank_account: str,
        merchant_name: str,
        merchant_city: str,
        amount: float,
        currency: str,
        store_label: str,
        phone_number: str,
        bill_number: str,
        terminal_label: str
    ) -> str:
        """
        Create a QR code string based on provided information.

        :param bank_account: Bank account information from Bakong profile (e.g., your_name@aba).
        :param merchant_name: Name of the merchant (e.g., Your Name).
        :param merchant_city: City of the merchant (e.g., Phnom Penh).
        :param amount: Transaction amount (e.g., 1.09).
        :param currency: Currency code (e.g., USD or KHR).
        :param store_label: Store label or merchant reference (e.g., Shop A).
        :param phone_number: Mobile number of the merchant (e.g., 85512345678).
        :param bill_number: Bill number or transaction reference (e.g., TRX019283775).
        :param terminal_label: Terminal label or transaction description (e.g., Buy Course).
        :return: Generated QR code as a string.
        """
        qr_data = self.payload_format_indicator.value()
        qr_data += self.point_of_initiation.dynamic()
        qr_data += self.global_unique_identifier.value(bank_account)
        qr_data += self.mcc.value()
        qr_data += self.country_code.value()
        qr_data += self.merchant_name.value(merchant_name)
        qr_data += self.merchant_city.value(merchant_city)
        qr_data += self.timestamp.value()
        qr_data += self.amount.value(amount)
        qr_data += self.transaction_currency.value(currency)
        qr_data += self.additional_data_field.value(store_label, phone_number, bill_number, terminal_label)
        qr_data += self.crc.value(qr_data)
        return qr_data

    def generate_deeplink(
        self, 
        qr: str, 
        callback: str = "https://bakong.nbc.org.kh", 
        appIconUrl: str = "https://bakong.nbc.gov.kh/images/logo.svg", 
        appName: str = "MyAppName"
        ) -> str:
        """
        Generate a deep link for the QR code.

        :param qr: QR code string generated from create_qr() method.
        :param callback: Callback URL for the deep link (default: https://bakong.nbc.org.kh).
        :param appIconUrl: App icon URL of your app or website (default: https://bakong.nbc.gov.kh/images/logo.svg).
        :param appName: Name of your app or website (default: MyAppName).
        :return: Deep link URL as a string.
        """
        payload = {
            "qr": qr,
            "sourceInfo": {
                "appIconUrl": appIconUrl,
                "appName": appName,
                "appDeepLinkCallback": callback
            }
        }
        headers = {
            "Authorization": f"Bearer {self.bakong_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.bakong_api + "/generate_deeplink_by_qr", json=payload, headers=headers).json()
        
        if response["responseCode"] == 0:
            return response["data"]["shortLink"]
        
        if response["responseCode"] == 1:
            raise ValueError("Error: ", response["status"]["message"])
        
    def generate_md5(
        self, 
        qr: str
        ) -> str:
        """
        Generate an MD5 hash for the QR code.

        :param qr: QR code string generated from create_qr() method.
        :return: MD5 hash as a string (32 characters).
        """
        return self.hash.md5(qr)
    
    def check_payment(
        self, 
        md5: str
        ) -> str:
        """
        Check the transaction status based on the MD5 hash.

        :param md5: MD5 hash of the QR code generated from generate_md5() method.
        :return: Transaction status as a string (PAID or UNPAID).
        """
        data = {
            'md5': md5
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZWYyNjdhYmZmMGEwNDA2In0sImlhdCI6MTcyNzc2MzA0NiwiZXhwIjoxNzM1NTM5MDQ2fQ.7An4XxwkaxM8uM1-vZpZEdJKF9Z1tsL7oCdhVVKMEnU'
        }
        payload = json.dumps(data)
        try : 
            response = requests.post('https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5', headers=headers, data=payload)
            print(response.status_code)
            if response.status_code == 200:
                data = response.json()
                if data["responseCode"] == 0:
                    return "PAID"
                return "UNPAID"
            else:
                print(f'POST request failed with status code {response.status_code}.')
                response.close()  # Close the response to free up memory
        except OSError as e:
            print(f'Network error: {e}')
            sleep(5)  # Wait before retrying
        except Exception as e:
            print(f'Error: {e}')

    def check_bulk_payments(
        self, 
        md5_list: list
        ) -> list:
        """
        Check the transaction status based on the list of MD5 hashes.

        :param md5_list: List of MD5 hashes generated from generate_md5() method.
        :return: md5 list of paid transactions.
        """
        headers = {
            "Authorization": f"Bearer {self.bakong_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.bakong_api + '/check_transaction_by_md5_list', json=md5_list, headers=headers).json()
        
        if response["responseCode"] == 0:
            # if md5 is SUCCESS, then append md5 to paid_list
            paid_list = []
            for data in response["data"]:
                if data["status"] == "SUCCESS":
                    paid_list.append(data["md5"])
            return paid_list
        return []