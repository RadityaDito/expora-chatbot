import boto3
import io
import json
import comtradeapicall
import pandas as pd

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
        modelId="arn:aws:bedrock:ap-southeast-1:688567308413:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload),
    )
    response_body = response["body"].read().decode("utf-8")
    
    # Convert to JSON
    response_json = json.loads(response_body)
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
            cmdCode='1511',  
            flowCode='X',  
            partnerCode='458',  
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
    
    return df
    
def extractRegulations(label,country):
    #Ask AI
    prompt = f'my label is "{label}" find if this label have a close relation to one of this list [{",".join(categories)}] if there is nothing close in that list said "None", do the same for this I have country name it is "{country}" find if this label have a close relation to one of this list [{",".join(countries)}] if there is nothing close in that list said "None", I only need you to answer which elemnet in the list has good correspondention, no need to mention the targeted string (ANSWER ONLY) so there will be 2 answer with  the format\nelement_in_list\nelement_in_list'
    request_payload = {
        "messages": [{"role": "user","content": [{"text":prompt}]}],
    }
    response = client_bedrock.invoke_model(
        modelId="arn:aws:bedrock:ap-southeast-1:688567308413:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload),
    )

    response_body = response["body"].read().decode("utf-8")
    response_json = json.loads(response_body)
    res = response_json["output"]["message"]["content"][0]["text"]
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
            modelId="arn:aws:bedrock:ap-southeast-1:688567308413:inference-profile/apac.amazon.nova-pro-v1:0",
            body=json.dumps(request_payload),
        )
    
        response_body = response["body"].read().decode("utf-8")
        response_json = json.loads(response_body)
        res = response_json["output"]["message"]["content"][0]["text"]
        return res
    
def aiAnalysis(label, hscode) :
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
    request_payload = {
        "messages": [
            {"role": "user", "content": [{"text":f"Analyze the export potential of {label} from Indonesia to Malaysia, Singapore, and Thailand based on the following data. Export Data: {export_data}. Import Data: {import_data}. Provide insights on market trade volume and fob prices that available in those data but use your estimation if not available.\n" + "Only explain top 2 potential country with format ouput :\n" + "country_A trade_amount fob_prices & country_B trade_amount fob_prices\nI dont need any explanation, just fill the output format with your answer"}]}
        ],
    }
    
    # Call Amazon Bedrock
    response = client_bedrock.invoke_model(
        modelId="arn:aws:bedrock:ap-southeast-1:688567308413:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload)
    )
    
    # Parse response
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
    prompt = f'''
With this data :
1. Label = {label}
2. HS code = {hscode}
3. Top 2 countries : {top_country} and {top2_country}
4. Trade amount of top 2 countries : {top_country_trade} and {top2_country_trade}
5. Price of top 2 countries : {top_country_price} and {top2_country_price}
if some of this reference is empty or None, filled with your estimation

Fill this sentences :
\'''
Based on our analysis, your {label} with HS code {hscode} appears to be a great fit for {top_country} and {top2_country} 

Based on our data, the top two countries with the highest trade volume for {label} are {top_country} and {top2_country} the amount is  {top_country_trade}  and {top2_country_trade} respectively. 
The prices are approximately {top_country_price} and {top2_country_price} for the respective countries. 

The documents and requirements you need to export this product to {top_country} are : 
{regulation_top_country}

The documents/requirements you need to export this product to {top2_country} are : 
{regulation_top2_country}

our suggested price for your product is ... for {top_country} and ... for {top2_country}, our suggested quantity is ... for {top_country} and ... for {top2_country}
\'''
Fill all the ...
'''
    # prompt = f'I have this information about import {import_data} and information about export {export_data} '
    request_payload = {
        "messages": [{"role": "user","content": [{"text":prompt}]}],
    }

    response = client_bedrock.invoke_model(
        modelId="arn:aws:bedrock:ap-southeast-1:688567308413:inference-profile/apac.amazon.nova-pro-v1:0",
        body=json.dumps(request_payload),
    )

    response_body = response["body"].read().decode("utf-8")
    response_json = json.loads(response_body)
    
    return response_json["output"]["message"]["content"][0]["text"]
    
    

# Client for S3
client_s3 = boto3.client('s3', region_name="ap-southeast-1",
        aws_access_key_id="AKIA2AUOPKB6267WA5EP",
        aws_secret_access_key="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"
    )

#Client for Bedrock
client_bedrock = boto3.client('bedrock-runtime', region_name="ap-southeast-1",
        aws_access_key_id="AKIA2AUOPKB6267WA5EP",
        aws_secret_access_key="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"
    )

#Client for rekognition
client_rekognition = boto3.client(
        "rekognition",
        region_name="ap-southeast-1",
        aws_access_key_id="AKIA2AUOPKB6267WA5EP",
        aws_secret_access_key="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"
    )

# Read regulations file
response = client_s3.get_object(Bucket="regulations-list", Key="Regulations.xlsx")
df_regulations = pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')
df_regulations["Negara"] = df_regulations["Negara"].str.lower()
df_regulations["Kategori"] = df_regulations["Kategori"].str.lower()

# Display DataFrame
categories = df_regulations["Kategori"].unique()
countries = df_regulations["Negara"].unique()


#PATH----------------------
path = "https://export-chatbot-ai-bucket.s3.ap-southeast-1.amazonaws.com/uploads/kopi.jpg"
img = imageLabelling(path)
txt = textLabelling(path)
res = callAI(img,txt)

for i in res.split("\n") :
    if "Label" in i :
        label = i.split(":")[-1].strip()
        print(label)
    if "HSCODE" in i :
        hscode = i.split(":")[-1].split(".")[0].split()[0].strip()
        print(hscode)

result = aiAnalysis(label,hscode)
result = result[result.find("Based"):]