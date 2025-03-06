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
    return {"message": "'### Potential Country: Malaysia\n\n*Explanation:\n1. **Market Demand:\n   - Malaysia shows a significant demand for coffee beans, as indicated by the high net weight of imports (26,003,066.41 kg) for the period. This suggests a robust market that can absorb large quantities of coffee beans.\n\n2. **Export Volume:\n   - Indonesia exported a substantial volume of coffee beans to Malaysia (25,230,670 kg), indicating a well-established trade relationship. The data shows that Malaysia is a key market for Indonesian coffee beans.\n\n3. **Value of Trade:\n   - The FOB value of coffee beans exported from Indonesia to Malaysia is 68,604,500 USD, reflecting a high-value trade. This highlights the potential for profitable exports.\n\n4. **Competitive Landscape:\n   - While Malaysia imports a large volume of coffee beans, the data does not indicate significant competition from other exporting countries within the provided dataset. This presents an opportunity for Indonesian exporters to capture a larger market share.\n\n5. **Pricing Strategy:\n   - The primary value of exports to Malaysia is competitive, suggesting that Indonesian coffee beans are priced attractively. Maintaining or slightly adjusting prices could help sustain market demand and competitiveness.\n\nConclusion:\nMalaysia emerges as the most potential country for exporting coffee beans from Indonesia due to its high demand, established trade relationship, and the significant value of exports. Focusing on maintaining competitive pricing and exploring market expansion strategies could further enhance export potential.\n\n---\n\n### General Overview of Coffee Beans Export Regulations\n\n1. Quality Standards:\n   - Exporters must ensure that coffee beans meet specific quality standards. These standards often include parameters like moisture content, bean size, and absence of defects. Compliance with international standards such as ISO or national standards set by the exporting country is crucial.\n\n2. Certification and Documentation:\n   - Exporters may need to obtain certifications like organic, fair trade, or other specific certifications depending on the target market. Proper documentation, including certificates of origin, phytosanitary certificates, and commercial invoices, is required.\n\n3. Packaging Requirements:\n   - Coffee beans must be packaged according to regulations to ensure they remain fresh and are not contaminated during transit. This may include specific materials for packaging and labeling requirements.\n\n4. Customs and Trade Regulations:\n   - Exporters must comply with the customs regulations of both the exporting and importing countries. This includes understanding tariff rates, quotas, and any trade agreements that may affect the export process.\n\n5. Food Safety and Hygiene:\n   - Adherence to food safety standards is critical. This involves maintaining hygiene in processing facilities, using approved pesticides, and ensuring that the final product is safe for consumption.\n\n6. Environmental and Ethical Considerations:\n   - Sustainable farming practices and ethical sourcing are increasingly important. Exporters may need to demonstrate compliance with environmental regulations and ethical trading standards.\n\n7. Export Licenses:\n   - Depending on the country, exporters may need to obtain specific licenses or permits to export coffee beans. This could involve registering with relevant trade authorities and adhering to their guidelines.\n\n8. Monitoring and Inspection:*\n   - Regular monitoring and inspection by both domestic and international authorities may be required to ensure ongoing compliance with export regulations.\n\nBy adhering to these regulations, exporters can ensure smooth and compliant trade of coffee beans, thereby maintaining market access and reputation.'", "imagePath": request.imagePath}

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

