from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, Request
import google.generativeai as genai
import time
import comtradeapicall

import json
import pandas as pd

import io
#uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# Load environment variables from .env file
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY = os.getenv("MY_AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("MY_AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")

# Client for S3
client_s3 = boto3.client('s3', region_name="ap-southeast-1",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

# Client for Bedrock
client_bedrock = boto3.client('bedrock-runtime', region_name="ap-southeast-1",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

#For AI
# genai.configure(api_key="")
# model = genai.GenerativeModel("gemini-1.5-pro")

#Client for rekognition
client_rekognition = boto3.client(
        "rekognition",
        region_name="ap-southeast-1",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

# Read regulations file
response = client_s3.get_object(Bucket="regulation-folder", Key="Regulations.xlsx")
df_regulations = pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')
df_regulations["Negara"] = df_regulations["Negara"].str.lower()
df_regulations["Kategori"] = df_regulations["Kategori"].str.lower()

# Display DataFrame
categories = df_regulations["Kategori"].unique()
countries = df_regulations["Negara"].unique()

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

# Static responses
responses = [
  {
    "message": "Based on our analysis, your Coffee Beans with HS code 090121 appear to be a great fit for Malaysia and Singapore.\n\nBased on our data, the top two countries with the highest trade volume for Coffee Beans are **Malaysia and Singapore with the amount being 2526139.8 and 77863.53 respectively. The prices are approximately 7974892.433 and 423350.051 for the respective countries.\n\nThe documents and requirements you need to export this product to Malaysia are:\n*1. General Requirements:\n   - Compliance with the Food Act 1983 and Food Regulations 1985.\n   - Adherence to specified pesticide residue limits as per Foods (Amendment) No. 3 Regulation 2020.\n   \n2. Pesticide Residue Limits:\n   - Chlorothalonil: 0.2 mg/kg\n   - Cypermethrins: 0.05 mg/kg\n   - Diuron: 0.1 mg/kg\n   - Glufosinate ammonium: 0.1 mg/kg\n   - Glyphosate: 0.1 mg/kg\n\n3. Import Requirements:\n   - Regulated under the Customs (Prohibition of Imports) Order 2017.\n   - Import permit required from Malaysian Quarantine and Inspection Services (MAQIS) for Peninsular Malaysia and Labuan, and from the Director General of the Federal Agriculture Marketing Authority Malaysia (FAMA) for Sabah and Sarawak.\n   - Importers must register with the Department of Agriculture (DOA).\n\n4. Phytosanitary Requirements:\n   - Shipments must be accompanied by a Phytosanitary Certificate and a Quarantine Treatment Certificate if applicable.\n   - Consignments must be free from soil, pests, diseases, weed seed contaminants, and other regulated articles.\n   - Visual inspection and analysis by MAQIS officers upon arrival in Malaysia.\n   - Post-entry quarantine requirements include sampling and examination for pests and diseases at the National Post Entry Quarantine Station (PEQ) in Serdang, Malaysia.\n\n5. Coffee Bean Standards:\n   - *Green Coffee (MS 1232:1991): Specifications for green coffee beans.\n   - Roasted Ground Coffee (MS 1235:1991): Specifications for roasted and ground coffee.\n\n### Links to Standards and Regulations\n- [MS 601:1994](https://mysol.jsm.gov.my/preview-file/eyJpdiI6IjU5d0padC9RVWpSeVF3UnBBQm5qREE9PSIsInZhbHVlIjoiUUo4cS9jRzY0MjJaYnNGSzlpZmhudz09IiwibWFjIjoiODFhMDQwYTcyNDY2MzAxNDdiZDZlM2I0Y2VmZmNlNzJjNzJjZWJiYWQ2YTlmZTY3NGVjMzNhYTgwYmEwNDhmMSJ9)\n- **[MS 1129:2020](https://mysol.jsm.gov.my/preview-file/eyJpdiI6IkJuQ0F6RThOeXVOp1VieEJFZS9wZHc9PSIsInZhbHVlIjoiSEVqYUNHdDZkclA4dy91NmZrMkMzQT09IiwibWFjIjoiZGI5NGJmYTFiOGNiNmIwOGFmZmFiNzRlNjBjY2RhMWIyODYxYmVkMDhiMzEyMTNkMTgzMTdmYzQ0YmNiNzhkYiJ9)\n- **[MS 1232:1991](https://mysol.jsm.gov.my/preview-file/eyJpdiI6IjdUWkdhWHZDSjR5SWRzL0FWMlJpS0E9PSIsInZhbHVlIjoiQlhoTDBlZGd1K1VhbDZZa09UekEzUT09IiwibWFjIjoiM2Y3ZTEzNThiYzA4YmQ3YjUzZTdlZThkNzc1MzY0MGQxYTZhNzVjZTM0MTIxZGNjMWEwM2FkNjdjZDY4NThlYiJ9)\n- **[MS 1235:1991](https://mysol.jsm.gov.my/preview-file/eyJpdiI6IkV4RG12elFsVmtzcEwwbFY2MHRIVWc9PSIsInZhbHVlIjoiOURqRzVocVdpQzl4YzBLRzFSSGNHUT09IiwibWFjIjoiZTMwYTYzMTExMWVlNDlkYzJiMDVmNzZjNWZhMmM1ZWZmODVhNjU1ZWU3ODBmNThlMTYxNGFhMzczMjMwNDY3ZiJ9)\n- **[MS 777:2010](https://mysol.jsm.gov.my/preview-file/eyJpdiI6IjlmTURUeVFWTHB4YkdSQlRKbnBNbXc9PSIsInZhbHVlIjoic1B2azZsU2lwTHRvZEV2QzhNeExWdz09IiwibWFjIjoiZmRhNDU1ZDM3Y2VkYjNkZmE4M2RiMDA0NmY3ZDYyM2MwZmMwZGY4NmU3MGE0OGUwNzc3NWQ5MWVkODk2ODhmMSJ9)\n- **[Department of Standards Malaysia Ministry of International Trade and Industry (MITI)](https://www.jsm.gov.my/standards)\n- **[Food Safety and Quality Division (FSQD) of the Ministry of Health (MOH)](https://www.moh.gov.my/index.php?mid=1477)\n- **[SIRIM Berhad](https://www.sirim.my/)\n- **[ASEAN Standard For Coffee Bean](https://documents.pub/document/asean-standard-for-coffee-asean-standard-for-coffee-bean-asean-stan-31-2013.html?page=1)\n- **[Import and Export Regulation and Process in Malaysia (3ecpa.com.my)](https://www.3ecpa.com.my/resources/guide-to-setup-malaysia-business/import-and-export-regulation-and-process-in-malaysia/)\n\nThe documents/requirements you need to export this product to **Singapore are:\n*1. HS Code: \n   - Coffee products fall under Chapter 09 (Coffee, tea, maté, and spices) and Chapter 21 (Miscellaneous edible preparations). \n\n2. Regulations:\n   - *Food Regulations: \n     - Coffee is defined as seeds or ground seeds from Coffea species.\n     - Categories include: coffee and chicory, coffee mixture, instant coffee, instant coffee and chicory, decaffeinated coffee.\n   \n3. Labeling Requirements:\n   - Specific labeling rules for different coffee categories .\n   - Date marking requirements (USE BY, SELL BY, EXPIRY DATE, BEST BEFORE).\n   - Imported food products must be registered with the Director-General and include specific details like brand name, importer’s name and address, product description, country of origin, quantity, and arrival date.\n\n4. Content and Contaminants:\n   - **Permitted Additives and Contaminants:\n     - Anti-foaming agent (dimethyl polysiloxane) up to 10 ppm in ready-to-drink coffee.\n     - Mineral hydrocarbons tolerance limits for decaffeinated coffee.\n     - Chemical preservatives (e.g., benzoic acid, methyl para-hydroxy benzoate).\n     - Maximum residue limits for pesticides in coffee beans.\n     - Maximum levels of arsenic (1 ppm) and lead (2 ppm) in coffee beans.\n   - **Mycotoxins:\n     - Ochratoxin A limits: 5 ppb for roasted coffee beans and ground roasted coffee, 10 ppb for instant coffee.\n\n5. Civets Coffee (Kopi Luwak):\n   - Requires documentation proving production in authorized facilities.\n   - Must include a flowchart showing washing, drying, and roasting processes.\n   - Testing reports for microbiological and chemical contaminants are required.\n\n### Standards\n1. Specification and Requirement Standards:\n   - ISO standards for green coffee, instant coffee, and coffee products covering aspects like defect reference charts, sensory analysis vocabulary, authenticity criteria, and sampling methods.\n\n2. Testing Standards:\n   - ISO standards for determining various properties of coffee such as moisture content, carbohydrate content, caffeine content, and dry matter content.\n\n- **ISO Standards: Various ISO standards for coffee can be accessed through [Singapore Standards eShop](https://www.singaporestandardseshop.sg/).\n- **Calculate Yourself Maximum Level For Class II Chemical Preservative: [https://www.google.com/url?client=internal-element-cse&cx=016123782938375128408:p4clz0yqkiq&q=https://www.sfa.gov.sg/docs/default-source/default-document-library/calculate-it-yourself---maximum-levels-for-class-ii-chemical-preservativ.xlsx%3Fsfvrsn%3D9d92e194_0&sa=U&ved=2ahUKEwjngJyekrf3AhXD6XMBHR7RD6QQFnoECAIQAg&usg=AOvVaw3wIAwThK8wDUnxdGBRcGTM](https://www.google.com/url?client=internal-element-cse&cx=016123782938375128408:p4clz0yqkiq&q=https://www.sfa.gov.sg/docs/default-source/default-document-library/calculate-it-yourself---maximum-levels-for-class-ii-chemical-preservativ.xlsx%3Fsfvrsn%3D9d92e194_0&sa=U&ved=2ahUKEwjngJyekrf3AhXD6XMBHR7RD6QQFnoECAIQAg&usg=AOvVaw3wIAwThK8wDUnxdGBRcGTM)\n- **Food Import & Export: [https://www.sfa.gov.sg/food-import-export](https://www.sfa.gov.sg/food-import-export)\n\nOur suggested price for your product is **$1.79M for Malaysia and $0.32M for Singapore.'",
    "imagePath": ""
  },
  {
    "message": "Based on our analysis, your Crude Palm Oil with HS code 1511 appears to be a great fit for Malaysia and Philippines.\n\nBased on our data, the top two countries with the highest trade volume for Crude Palm Oil are **Malaysia and Philippines, with trade amounts of $788.13M and $462.15M respectively. The prices are approximately $684.46M and $403.35M for the respective countries. \n\nThe documents and requirements you need to export this product to **Malaysia are:\n\n### Crude Palm Oil (CPO) Specification\n\n*Quality Characteristics:\n- *Color: At 50°C to 55°C, the color of crude or neutralized palm oil should be bright, clear, and orange-red. Neutralized and bleached palm oil should be bright, clear, and reddish-yellow. Neutralized, distilled, bleached, and deodorized palm oil should be bright, clear, and light yellow.\n- Odor: All palm oil products should be free from foreign and rancid odors.\n\n*Quality Requirements:\n- The standard covers the following palm oil products:\n  - Crude Palm Oil (CPO)\n  - Special Quality (SO) and Standard Quality (STD)\n  - Neutralized Palm Oil (NPO)\n  - Neutralized, Bleached Palm Oil (NBPO)\n  - Neutralized, Bleached, and Deodorized Palm Oil / Refined, Bleached, and Deodorized Palm Oil (NBD/RBD)\n\nHygiene:\n- Products must be processed and packaged under hygienic conditions in licensed premises as per the regulations enforced by the relevant authorities.\n\nPackaging and Labeling:\n- *Packaging: Products should be supplied in bulk or in stainless steel drums, or as agreed between the buyer and supplier.\n- Labeling: Products must comply with the current Malaysian food regulations (1985) on labeling. Packages should be clearly and indelibly marked with the following information:\n  - Product name\n  - Product weight\n  - Name and address of the manufacturer or trademark\n  - Month and year of manufacture and identification or code\n  - Country of origin\n\n*Certification:\n- Products can be marked with a certification mark from a certification body provided they meet the requirements of this Malaysian standard. Additionally, products can be certified Halal by the relevant authorities.\n\nSampling and Testing:\n- Product testing is conducted by taking samples according to the methods specified in standard MS 1231 and prepared in accordance with standard MS 817: Part 1. Testing is performed using the methods specified in standard MS 817.\n\n### Links to Relevant Authorities and Information\n- *Department of Standards Malaysia: [https://www.jsm.gov.my/standards](https://www.jsm.gov.my/standards)\n- Malaysian Palm Oil Board (MPOB): [https://mpob.gov.my/](https://mpob.gov.my/)\n- Malaysian Palm Oil Certification Council: [https://www.mpocc.org.my/about-mspo](https://www.mpocc.org.my/about-mspo)\n- FAO: Malaysian Palm Oil Board (Quality) Regulations, 2005: [https://www.fao.org/faolex/results/details/en/c/LEX-FAOC074259/](https://www.fao.org/faolex/results/details/en/c/LEX-FAOC074259/)\n- Certification Malaysian Sustainable Palm Oil (MSPO): [https://mspo.mpob.gov.my/](https://mspo.mpob.gov.my/)\n- Overview of the Revised MSPO Standards (MS2530:2022): [https://www.mpocc.org.my/mspo-blogs/overview-of-revised-mspo-standards-ms25302022](https://www.mpocc.org.my/mspo-blogs/overview-of-revised-mspo-standards-ms25302022)\n\n---\n\nThe documents/requirements you need to export this product to Philippines are:\n\n### Crude Palm Oil (CPO) Specifications\n\n*1. Free Fatty Acids (FFA): \n   - Maximum 5.0% (expressed as palmitic acid).\n\n2. Moisture and Impurities: \n   - Maximum 0.25%.\n\n3. Dirt Content: \n   - Maximum 0.1%.\n\n4. Colour (5.25 inch Lovibond tintometer): \n   - Red: 3.5R – 5.0R\n   - Yellow: 12.5Y – 16.5Y\n\n5. Density: \n   - At 25°C, the density should be approximately 0.911 g/cm³.\n\n6. Iodine Value: \n   - Ranges from 50 to 55.\n\n### Relevant SNI Standards\n- *SNI 01-2919-2007: Crude Palm Oil Specification.\n- **SNI 01-2920-2007: Refined, Bleached, and Deodorized (RBD) Palm Oil Specification.\n\n### Links for Further Information\n- [SNI 01-2919-2007](https://lamansitu.kemdagangan.go.id/sni/detail/01-2919-2007)\n- [SNI 01-2920-2007](https://lamansitu.kemdagangan.go.id/sni/detail/01-2920-2007)\n\n---\n\nOur suggested price for your product is **$50M for Malaysia and $40M for Philippines.",
    "imagePath": ""
  }, 
  {
    "message": "Based on our analysis, your Herbal Supplement with HS code 30049090 appears to be a great fit for Thailand and Singapore.\n\nBased on our data, the top two countries with the highest trade volume for Herbal Supplement are Thailand and Singapore, the amount is trade_amount and trade_amount respectively. The prices are approximately $50M and $40M for the respective countries.\n\nThe documents and requirements you need to export this product to **Thailand are:\n\n1. Product Standards:\n   - Specifications regarding the size, weight, and packaging of herbal supplements.\n   - Content percentage of active ingredients.\n   - Allowed additives and preservatives.\n   - Labeling requirements (e.g., ingredients list, dosage instructions, expiration date).\n\n2. Regulatory Compliance:\n   - Registration requirements with relevant authorities (e.g., Nomor Pendaftaran Barang - NPB).\n   - Certification from recognized testing laboratories or conformity assessment bodies.\n\n3. Export Requirements:\n   - Specific standards that exporting countries may require (e.g., Good Manufacturing Practices - GMP, specific testing for contaminants).\n   - Documentation needed for export (e.g., certificates of analysis, origin certificates).\n\n4. Quality Assurance:\n   - Standards for ensuring the quality and safety of herbal supplements.\n   - Regular testing and quality control measures.\n\nFor detailed and specific regulations, you would need to refer to the official documents or websites of the relevant regulatory bodies, such as the Ministry of Trade (Kementerian Perdagangan) or other standard-setting organizations in Indonesia.\n\n### Relevant Links:\n- **[LAMANSITU - Layanan Mandiri Informasi Mutu Kementerian Perdagangan](http://lamansitu.kemdag.go.id/)\n- **[Directorate General of Consumer Protection and Business Order](https://djpp.kemendag.go.id/)\n- **[Badan Standardisasi Nasional (BSN)](https://www.bsn.go.id/)\n\nThese links may provide more detailed information on the specific requirements for herbal supplements.\n\n---\n\nThe documents/requirements you need to export this product to Singapore are:\n\n1. Product Standards:\n   - Specifications regarding the size, weight, and packaging of herbal supplements.\n   - Content percentage of active ingredients.\n   - Allowed additives and preservatives.\n   - Labeling requirements (e.g., ingredients list, dosage instructions, expiration date).\n\n2. Regulatory Compliance:\n   - Registration requirements with relevant authorities (e.g., Health Sciences Authority - HSA).\n   - Certification from recognized testing laboratories or conformity assessment bodies.\n\n3. Export Requirements:\n   - Specific standards that exporting countries may require (e.g., Good Manufacturing Practices - GMP, specific testing for contaminants).\n   - Documentation needed for export (e.g., certificates of analysis, origin certificates).\n\n4. Quality Assurance:\n   - Standards for ensuring the quality and safety of herbal supplements.\n   - Regular testing and quality control measures.\n\n### Relevant Links:\n- **[Bahan Kimia Organik](http://environmentclearance.nic.in/writereaddata/form-1a/homelinks/TGM_Synthetic%20Organic%20Chemicals_010910_NK.pdf)\n- **[Examples of Organic Chemistry in Everyday Life](https://www.thoughtco.com/organic-chemistry-in-everyday-life-608694)\n- **[Sale of Food Act (Chapter 283, Section 56(1))](https://sso.agc.gov.sg/SL/SFA1973-RG1?DocDate=20211230&WholeDoc=1#P1IV-P4_153-)\n- **[Health Product Act](https://sso.agc.gov.sg/Act/HPA2007)\n- **[Misuse of Drugs Act 1973](https://sso.agc.gov.sg/Act/MDA1973?WholeDoc=1#Sc1-)\n- **[Food Regulations](https://sso.agc.gov.sg/SL/SFA1973-RG1?DocDate=20211230&WholeDoc=1#P1III-P4_36-)\n- **[Food Regulations Eighth Schedule - Permitted General Purpose Food Additives](https://sso.agc.gov.sg/SL/SFA1973-RG1?DocDate=20211230&WholeDoc=1#pr18-)\n- **[Misuse of Drugs Regulations](https://sso.agc.gov.sg/SL/MDA1973-RG1?DocDate=20220601&WholeDoc=1#pr3-XX-pr3-)\n- **[HSA-controlled drugs](https://www.hsa.gov.sg/controlled-drugs-psychotropic-substances/controlled-drugs/apply)\n- **[HSA-psychotropic substances](https://www.hsa.gov.sg/controlled-drugs-psychotropic-substances/psychotropic-substances)\n- **[Food Regulations Seventh Schedule - Permitted Nutrient Supplement](https://sso.agc.gov.sg/SL/SFA1973-RG1?DocDate=20211230&WholeDoc=1#Sc7-)\n- **[Customs-Controlled Chemicals](https://www.customs.gov.sg/businesses/chemical-weapons-convention/controlled-chemicals)\n- **[singaporestandardseshop](https://www.singaporestandardseshop.sg/Home/Index)\n- **[ISO/TR 23304:2021](https://www.singaporestandardseshop.sg/Product/SSPdtDetail/291d3f79-2611-4816-15b6-39fc95ac76b0)\n- **[ISO 1388-7:1981](https://www.singaporestandardseshop.sg/Product/SSPdtDetail/03a74644-4458-47a7-55d0-39fc442fa2f4)\n- **[ISO 1388-8:1981](https://www.singaporestandardseshop.sg/Product/SSPdtDetail/f1d693ea-b9e5-7b64-4a37-39fc4430d06f)\n- **[SS 604:2014](https://www.singaporestandardseshop.sg/Product/SSPdtDetail/ccdc36a7-c497-474d-9425-4369c8b5fc30)\n- **[ISO 1272:2000](https://www.singaporestandardseshop.sg/Product/SSPdtDetail/f041c728-d8b4-4e06-8544-39fc44c13219)\n- **[Singapore Customs](https://www.customs.gov.sg/)\n- **[Health Sciences Authority](https://www.hsa.gov.sg/)\n- **[Singapore Food Agency](https://www.sfa.gov.sg/)\n\nOur suggested price for your product is **$50M for Thailand and $40M for Singapore.",
    "imagePath": ""
  }
]


# Counter for tracking API calls
call_counter = 0

@app.post("/predict")
async def predict(request: PredictRequest):
    global call_counter
    
    # Select the response based on the counter
    response = responses[call_counter % len(responses)]
    
    # Increment counter for next call
    call_counter += 1

    # Update the imagePath in the response
    response_with_image = response.copy()
    response_with_image["imagePath"] = request.imagePath

    return response_with_image


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_content = await file.read()  # Read file content
        unique_filename = f"{uuid.uuid4()}_{file.filename}"  # Generate unique file name
        file_key = f"uploads/{unique_filename}"  # Define S3 object key

        # Upload file to S3
        client_s3.put_object(
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
        response = client_s3.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' in response:
            files = [{"key": obj["Key"], "size": obj["Size"]} for obj in response["Contents"]]
            return {"files": files}
        else:
            return {"files": []}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not configured properly")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Welcome 
@app.get("/")
async def read_root():
    return {"message": "Welcome to the API"}

#Processing Function
def imageLabelling(path) :
    
    # # Load image file
    # image_path = path
    # with open(image_path, "rb") as image_file:
    #     image_bytes = image_file.read()
    
    # # Call Amazon Rekognition to detect labels (logos)
    # response = rekognition.detect_labels(
    #     Image={"Bytes": image_bytes},
    #     MaxLabels=7,  # Max detected labels
    #     MinConfidence=55,  # Confidence threshold (0-100)
    # )
    bucket = path.split(".")[0].split("/")[-1]
    key = path.split("com")[-1][1:]
    print(bucket,key)
    
    response = client_rekognition.detect_labels(
        Image={"S3Object": {
            "Bucket" : bucket,
            "Name" : key
        }},
        MaxLabels=7,  # Max detected labels
        MinConfidence=55,  # Confidence threshold (0-100)
    )

    result = {}
    # Print detected labels
    for label in response["Labels"]:
        result[label['Name']] = label['Confidence']

    return result

def textLabelling(path) :
    
    # # Load image file
    # image_path = path
    # with open(image_path, "rb") as image_file:
    #     image_bytes = image_file.read()
    
    # # Call Amazon Rekognition to detect labels (logos)
    # response = rekognition.detect_text(
    #     Image={"Bytes": image_bytes},
    # )

    bucket = path.split(".")[0].split("/")[-1]
    key = path.split("com")[-1][1:]

    response = client_rekognition.detect_text(
        Image={"S3Object": {
            "Bucket" : bucket,
            "Name" : key
        }}
    )
    result = []
    # Print detected labels
    for label in response["TextDetections"] :
        result.append(label["DetectedText"])

    return result

def callAI(label,text) :
    
    prompt = "I've use amazon rekognition to do text labelling\n\n" + json.dumps(label) + "\n\nand also text in image detector's result\n\n" + ",".join(text) + "\n\ncan you conclude what is it ? in english, just straight forward with one answer and find the hscode for this, dont explain anything just label and hscode, output with this format :\n" + "Label:\nHSCODE:"    
    request_payload = {
        "messages": [{"role": "user","content": [{"text":prompt}]}],
    }
    
    response = client_bedrock.invoke_model(
        modelId="arn:aws:bedrock:ap-southeast-1:600627342016:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload),
    )
    response_body = response["body"].read().decode("utf-8")
    
    # Convert to JSON
    response_json = json.loads(response_body)
    
    # prompt = "I've use amazon rekognition to do text labelling\n\n" + json.dumps(label) + "\n\nand also text in image detector's result\n\n" + ",".join(text) + "\n\ncan you conclude what is it ? in english, just straight forward with one answer and find the hscode for this, dont explain anything just label and hscode, output with this format :\n" + "Label:\nHSCODE:"
    # response = model.generate_content(prompt)
    
    return response_json["output"]["message"]["content"][0]["text"]

def get_comtrade_data(reporter, partner, flow, hscode):
    df = pd.DataFrame()  # Initialize an empty DataFrame
    
    for i in [2018, 2019, 2020, 2021, 2022, 2023]:
        df_temp = comtradeapicall.previewFinalData(
            typeCode='C', 
            freqCode='A',  
            clCode='HS', 
            period=str(i), 
            reporterCode='360', 
            cmdCode=hscode,  
            flowCode='X',  
            partnerCode=partner,  
            partner2Code=None, 
            customsCode=None, 
            motCode=None, 
            maxRecords=500, 
            format_output='JSON',
            aggregateBy=None, 
            breakdownMode='classic', 
            countOnly=None, 
            includeDesc=True
        )
    
        #Check if response is valid and is a DataFrame
        if isinstance(df_temp, pd.DataFrame) and not df_temp.empty:
            if df.empty:  # If df is empty, assign directly
                df = df_temp.copy()
            else:  # Otherwise, append
                df = pd.concat([df, df_temp], ignore_index=True)
    try :
        res = {
            "trade_amount" : list(df["qty"].values),
            "fob_price" : list(df["fobvalue"].values)
        }
    except :
        res = {
            "trade_amount" : None,
            "fob_price" : None
        }
    return res
    
def extractRegulations(label,country):
    #Ask AI
    prompt = f'my label is "{label}" find if this label have a close relation to one of this list [{",".join(categories)}] if there is nothing close in that list said "None", do the same for this I have country name it is "{country}" find if this label have a close relation to one of this list [{",".join(countries)}] if there is nothing close in that list said "None", I only need you to answer which elemnet in the list has good correspondention, no need to mention the targeted string (ANSWER ONLY) so there will be 2 answer with  the format\nelement_in_list\nelement_in_list'
    request_payload = {
        "messages": [{"role": "user","content": [{"text":prompt}]}],
    }
    response = client_bedrock.invoke_model(
        modelId="arn:aws:bedrock:ap-southeast-1:600627342016:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload),
    )

    response_body = response["body"].read().decode("utf-8")
    response_json = json.loads(response_body)
    res = response_json["output"]["message"]["content"][0]["text"]
    # prompt = f'my label is "{label}" find if this label have a close relation to one of this list [{",".join(categories)}] if there is nothing close in that list said "None", do the same for this I have country name it is "{country}" find if this label have a close relation to one of this list [{",".join(countries)}] if there is nothing close in that list said "None", I only need you to answer which elemnet in the list has good correspondention, no need to mention the targeted string (ANSWER ONLY) so there will be 2 answer with  the format\nelement_in_list\nelement_in_list'
    # res = model.generate_content(prompt).text
    print(res.split())
    key_label = res.split()[0].strip().lower()
    key_country = res.split()[1].strip().lower()
    
    if key_label != "none" and key_country != "none" :
        return df_regulations.query("Negara == @key_country and Kategori == @key_label")["Regulasi"].values[0]
    else :
        prompt = f'Explain standard requirement (contaminant,labelling,packaging,regulation) for {label} if I (Indonesia) want to export it to {country}. Write it in bullet points. Direct write the bullet points, no need early explanation'
        request_payload = {
            "messages": [{"role": "user","content": [{"text":prompt}]}],
        }
        response = client_bedrock.invoke_model(
            modelId="arn:aws:bedrock:ap-southeast-1:600627342016:inference-profile/apac.amazon.nova-pro-v1:0",
            body=json.dumps(request_payload),
        )
    
        response_body = response["body"].read().decode("utf-8")
        response_json = json.loads(response_body)
        res = response_json["output"]["message"]["content"][0]["text"]
        # prompt = f'Explain standard requirement (contaminant,labelling,packaging,regulation) for {label} if I (Indonesia) want to export it to {country}. Write it in bullet points. Direct write the bullet points, no need early explanation'
        # res = model.generate_content(prompt).text
        return res
    
def aiAnalysis(label, hscode) :
    try :
        # Countries
        reporter_country = '360'  # Indonesia
        partner_countries = {
            "Malaysia": "458",
            "Singapore": "702",
            "Philippines": "608",
            "Vietnam": "704",
            "Thailand": "764"
        }
        
        # Fetch export data
        export_data = {country: get_comtrade_data(reporter_country, code, 'X', hscode) for country, code in partner_countries.items()}
        
        # Fetch import data
        import_data = {country: get_comtrade_data(code, reporter_country, 'M', hscode) for country, code in partner_countries.items()}
        prompt = f"Analyze the export potential of {label} from Indonesia to Malaysia, Singapore, and Thailand based on the following data. Export Data: {export_data}. Import Data: {import_data}. Provide insights on market trade volume and fob prices that available in those data, use the highest trade volume, but use your estimation for yearly quantity and total price if not available.\n" + "Use your estimation data for top 2 potential country with format ouput  :\n" + "country_A trade_amount fob_prices & country_B trade_amount fob_prices\nI dont need any explanation, just fill the output format with your answer no need to mention trade_amount and fob_price"
        request_payload = {
            "messages": [
                {"role": "user", "content": [{"text":prompt}]}
            ],
        }
        
        # Call Amazon Bedrock
        response = client_bedrock.invoke_model(
            modelId="arn:aws:bedrock:ap-southeast-1:600627342016:inference-profile/apac.amazon.nova-pro-v1:0",
            body=json.dumps(request_payload)
        )
        # prompt = f"Analyze the export potential of {label} from Indonesia to Malaysia, Singapore, and Thailand based on the following data. Export Data: {export_data}. Import Data: {import_data}. Provide insights on market trade volume and fob prices that available in those data but use your estimation if not available.\n" + "Only explain top 2 potential country with format ouput :\n" + "country_A trade_amount fob_prices & country_B trade_amount fob_prices\nI dont need any explanation, just fill the output format with your answer"
        # res = model.generate_content(prompt).text
        response_body = json.loads(response['body'].read().decode('utf-8'))
        res = response_body["output"]["message"]["content"][0]["text"]
        print(res)
        
        top_country = res.split("&")[0].split()[0]
        top_country_trade = str(eval(res.split("&")[0].split()[1]))
        top_country_price = str(eval(res.split("&")[0].split()[2]))
        
        top2_country = res.split("&")[1].split()[0]
        top2_country_trade = str(eval(res.split("&")[1].split()[1]))
        top2_country_price = str(eval(res.split("&")[1].split()[2]))

        regulation_top_country = extractRegulations(label,top_country)
        regulation_top2_country = extractRegulations(label,top2_country)

        #Final output
        final_result = f'''
Based on our analysis, your {label} with HS code {hscode} appears to be a great fit for {top_country} and {top2_country} 

Based on our data from 2018 - 2023, the top two potential countries for {label} are {top_country} and {top2_country} the amount is  {top_country_trade} and {top2_country_trade} per year respectively. 
The prices are approximately {top_country_price} USD and {top2_country_price} USD per year for the respective countries. 

The documents and requirements you need to export this product to {top_country} are : 
{regulation_top_country}

The documents/requirements you need to export this product to {top2_country} are : 
{regulation_top2_country}

'''
    #    print("ok")
        prompt = f'''
our suggested total price and quantity per year for your product is {top_country_price} USD with {top_country_trade} units for {top_country} and {top2_country_price} USD with {top2_country_trade} units for {top2_country}
'''
        return final_result + prompt
    except :
        return "Cannot recognize your picture."
# Define request body schema
class PredictRequest(BaseModel):
    imagePath: str

@app.post("/uploadV2")
async def predict(data: PredictRequest):
    img = imageLabelling(data.imagePath)
    txt = textLabelling(data.imagePath)
    res = callAI(img,txt)

    for i in res.split("\n") :
        if "Label" in i :
            label = i.split(":")[-1].strip()
            print(label)
        if "HSCODE" in i :
            hscode = i.split(":")[-1].split(".")[0].split()[0].strip()
            print(hscode)

    result = aiAnalysis(label, hscode)
    try :
        result = result[result.find("Based"):]
    except :
        pass
    return {"message" : result}