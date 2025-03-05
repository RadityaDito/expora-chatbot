from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
import uuid
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION,
)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create API that accept imagePath string and return the dummy string for now 
# Define request body schema
class PredictRequest(BaseModel):
    imagePath: str

@app.post("/predict")
async def predict(request: PredictRequest):
    return {"message": "Mock Chatbot Response: Your product appears to comply with US import regulations. Key compliance points:\n\n• No prohibited symbols or markings\n• Labeling appears to meet FDA standards\n• No obvious restricted materials\n\nRecommendation: Proceed with export, but verify specific industry regulations that may apply.", "imagePath": request.imagePath}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_content = await file.read()  # Read file content
        unique_filename = f"{uuid.uuid4()}_{file.filename}"  # Generate unique file name
        file_key = f"uploads/{unique_filename}"  # Define S3 object key

        # Upload file to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=file.content_type,
        )

        file_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{file_key}"
        return {"message": "File uploaded successfully", "file_url": file_url}
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not configured properly")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Create API to list all files in S3 bucket
@app.get("/list")
async def list_files():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' in response:
            files = [{"key": obj["Key"], "size": obj["Size"]} for obj in response["Contents"]]
            return {"files": files}
        else:
            return {"files": []}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not configured properly")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API"}

