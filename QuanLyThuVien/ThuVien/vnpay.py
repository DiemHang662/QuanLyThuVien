import hashlib
import urllib.parse


class vnpay:
    def __init__(self):
        self.requestData = {}

    def get_payment_url(self, vnpay_url, secret_key):
        sorted_params = sorted(self.requestData.items())
        query_string = '&'.join(
            '{}={}'.format(urllib.parse.quote(k), urllib.parse.quote(str(v))) for k, v in sorted_params)
        hash_value = hashlib.sha256((query_string + secret_key).encode('utf-8')).hexdigest()
        return '{}?{}&vnp_SecureHash={}'.format(vnpay_url, query_string, hash_value)

    def verify_payment(self, vnp_response_data, secret_key):
        """
        Verify the payment with the response data from VNPAY.

        :param vnp_response_data: The data returned from VNPAY.
        :param secret_key: Your VNPAY secret key.
        :return: True if verification is successful, False otherwise.
        """
        # Extract the secure hash from the response data
        secure_hash = vnp_response_data.get('vnp_SecureHash')

        # Remove the secure hash from the response data for verification
        vnp_response_data.pop('vnp_SecureHash', None)

        # Sort the response data
        sorted_params = sorted(vnp_response_data.items())
        query_string = '&'.join(
            '{}={}'.format(urllib.parse.quote(k), urllib.parse.quote(str(v))) for k, v in sorted_params)

        # Generate hash using the secret key
        hash_value = hashlib.sha256((query_string + secret_key).encode('utf-8')).hexdigest()

        # Compare the generated hash with the secure hash from the response
        return hash_value == secure_hash
