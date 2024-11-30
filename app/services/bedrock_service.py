import boto3
import json
from app.config import Config
import base64
from app.services.s3_service import S3Service

class BedrockService:
    def __init__(self):
        # Create session with AWS credentials
        self.session = boto3.Session(
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            aws_session_token=Config.AWS_SESSION_TOKEN,
            region_name=Config.AWS_REGION
        )
        
        # Create Bedrock client using the session
        self.bedrock = self.session.client(service_name='bedrock-runtime')
        self.model_id = Config.BEDROCK_MODEL_ID

    def analyze_ad(self, ad_details, images_data=None, video_data=None, audio_data=None):
        """Analyze ad content using Claude"""
        print("Images data:", images_data)
        print("Video data:", video_data)
        print("Audio data:", audio_data)
        prompt = self._construct_analysis_prompt(ad_details, images_data, video_data, audio_data)
        # print("Prompt:", prompt)
        print("hello")
        print("Model ID:", self.model_id)
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response.get('body').read())
            print("Response body:", response_body)
            return response_body['content'][0]['text']
        
        except Exception as e:
            print("Error analyzing ad with Bedrock:", str(e))
            raise Exception(f"Error analyzing ad with Bedrock: {str(e)}")

    def _construct_analysis_prompt(self, ad_details, images_data=None, video_data=None, audio_data=None):
        """Construct the prompt for ad analysis"""
        prompt = f"""Please analyze this advertisement against platform policies and provide a detailed report.

Ad Details:
{ad_details}

Your task is to:
1. Analyze all ad components (text, images, video, audio) for policy compliance
2. Generate a comprehensive report in the following format:

Ad Details:
- Ad Name:
- Ad Description:
- Ad Category:
- Ad Targeting:
- Ad Message:

Ad Analysis:
- Image Analysis:
- Text Analysis:
- Video Analysis:
- Audio Analysis:

Final Report:
- Ad Details:
- Ad Analysis:
- Ad Compliance:
- Ad Status:

What to do if the ad is not compliant:
- Fix the ad (suggest specific changes)
- Explain why the ad is not compliant
- Suggest changes to the ad
- Suggest alternative ads

Please be specific and detailed in your analysis, focusing on:
- Platform policy compliance
- Content appropriateness
- Target audience alignment
- Brand safety
- Regulatory compliance

"""
        if images_data:
            prompt += f"\nImages for analysis: {images_data}"
        if video_data:
            prompt += f"\nVideo for analysis: {video_data}"
        if audio_data:
            prompt += f"\nAudio for analysis: {audio_data}"
            
        s3_service = S3Service()
        guidelines_file_url_list = s3_service.get_guidelines_file_url_list()
        # for url in guidelines_file_url_list:
        #     prompt += f"\nGuidelines for analysis: {url}"

        return prompt

    def fix_ad(self, original_analysis, ad_content):
        """Fix non-compliant ads based on the original analysis"""
        prompt = f"""Based on the following analysis, please fix this advertisement to make it compliant:

Original Analysis:
{original_analysis}

Ad Content to Fix:
{ad_content}

Please provide:
1. Specific changes made
2. New ad content
3. Analysis of the fixed ad
"""
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response.get('body').read())
            print("Response body:", response_body)
            return response_body['content'][0]['text']
        
        except Exception as e:
            print("Error fixing ad with Bedrock:", str(e))
            raise Exception(f"Error fixing ad with Bedrock: {str(e)}") 