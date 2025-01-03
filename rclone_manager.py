import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import configparser
from urllib.parse import parse_qs, urlparse

class RcloneManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        # Rclone's default client configuration
        self.CLIENT_CONFIG = {
            "installed": {
                "client_id": "202264815644.apps.googleusercontent.com",
                "client_secret": "X4Z3ca8xfWDb1Voo-F9a7ZxJ",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://127.0.0.1:53682/"]
            }
        }
        
    def get_auth_url(self, user_id: int = None):
        """Generate authorization URL for Google Drive"""
        redirect_uri = "http://127.0.0.1:53682/"
        
        auth_url = (
            "https://accounts.google.com/o/oauth2/auth"
            f"?client_id={self.CLIENT_CONFIG['installed']['client_id']}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=https://www.googleapis.com/auth/drive"
            "&access_type=offline"
            "&approval_prompt=force"
        )
        
        return auth_url

    def extract_code_from_url(self, url):
        """Extract authorization code from redirect URL"""
        try:
            parsed = urlparse(url)
            code = parse_qs(parsed.query)['code'][0]
            return code
        except:
            return None
        
    async def save_token(self, user_id: int, auth_input: str):
        """Save token after authorization"""
        try:
            # Check if input is URL or code
            auth_code = self.extract_code_from_url(auth_input) if '?' in auth_input else auth_input

            if not auth_code:
                return "Error: Invalid authorization code or URL"

            # Create flow
            flow = InstalledAppFlow.from_client_config(
                self.CLIENT_CONFIG,
                scopes=self.SCOPES
            )

            flow.redirect_uri = "http://127.0.0.1:53682/"

            # Get token
            token = flow.fetch_token(code=auth_code)

            # Calculate expiry time (current time + 1 hour)
            expiry_time = datetime.now().timestamp() + 3600

            # Create rclone config
            config = f"""[gdrive]
type = drive
token = {json.dumps({
    "access_token": token["access_token"],
    "token_type": "Bearer",
    "refresh_token": token["refresh_token"],
    "expiry": datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(datetime.fromtimestamp(expiry_time).microsecond):07d}" + "+06:00"
})}
team_drive ="""

            return config

        except Exception as e:
            print(f"Failed to save token: {str(e)}")
            return None
        
    async def refresh_token(self, rclone_conf: str):
        """Refresh token from rclone.conf file"""
        try:
            # Read rclone.conf
            config = configparser.ConfigParser()
            config.read(rclone_conf)
            
            if 'gdrive' not in config:
                raise Exception("Invalid rclone.conf file")
                
            # Get token data
            token_data = json.loads(config['gdrive']['token'])
            
            # Create credentials
            creds = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.CLIENT_CONFIG['installed']['client_id'],
                client_secret=self.CLIENT_CONFIG['installed']['client_secret'],
                scopes=self.SCOPES
            )
            
            # Refresh token
            creds.refresh(Request())
            
            # Calculate expiry time (current time + 1 hour)
            expiry_time = datetime.now().timestamp() + 3600

            # Create new rclone config
            new_config = f"""[gdrive]
type = drive
token = {json.dumps({
    "access_token": creds.token,
    "token_type": "Bearer",
    "refresh_token": creds.refresh_token,
    "expiry": datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(datetime.fromtimestamp(expiry_time).microsecond):07d}" + "+06:00"
})}
team_drive ="""

            return new_config
            
        except Exception as e:
            print(f"Failed to refresh token: {str(e)}")
            return None
