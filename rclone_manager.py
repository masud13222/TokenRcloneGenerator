import os
import json
from datetime import datetime
from config import Config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import configparser

class RcloneManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        
    def get_auth_url(self, user_id: int):
        """Generate authorization URL for Google Drive"""
        redirect_uri = "http://127.0.0.1:53682"
        
        auth_url = (
            "https://accounts.google.com/o/oauth2/auth"
            f"?client_id={Config.RCLONE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=https://www.googleapis.com/auth/drive"
            "&access_type=offline"
            "&approval_prompt=force"
        )
        
        return auth_url
        
    async def save_token(self, user_id: int, code: str):
        """Save token after authorization"""
        try:
            # Create flow with redirect_uri
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": Config.RCLONE_CLIENT_ID,
                        "client_secret": Config.RCLONE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://127.0.0.1:53682"]
                    }
                },
                self.SCOPES
            )
            
            # Set redirect_uri
            flow.redirect_uri = "http://127.0.0.1:53682"
            
            # Fetch token
            token = flow.fetch_token(code=code)
            
            # Format token for rclone.conf
            token_dict = {
                "access_token": token["access_token"],
                "token_type": "Bearer",
                "refresh_token": token["refresh_token"],
                "expiry": datetime.fromtimestamp(token["expires_in"]).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            }
            
            return json.dumps(token_dict)
            
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
                client_id=Config.RCLONE_CLIENT_ID,
                client_secret=Config.RCLONE_CLIENT_SECRET,
                scopes=self.SCOPES
            )
            
            # Refresh token
            creds.refresh(Request())
            
            # Format new token
            new_token = {
                "access_token": creds.token,
                "token_type": "Bearer",
                "refresh_token": creds.refresh_token,
                "expiry": creds.expiry.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
            }
            
            return json.dumps(new_token)
            
        except Exception as e:
            print(f"Failed to refresh token: {str(e)}")
            return None 
