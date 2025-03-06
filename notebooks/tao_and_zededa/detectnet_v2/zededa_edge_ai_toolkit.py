import requests

# API Endpoint
API_URL = "http://renesp.selfhost.co:5090/trtexec"

def ZededaTRTConverter(file1_path, outfile_path):
    """Sends ONNX file to the API and downloads the output file."""
    with open(file1_path, 'rb') as f1:
        files = {
            "model.onnx": f1,
        }

        response = requests.post(API_URL, files=files)

        if response.status_code == 200:
            # Save the output file
            with open(outfile_path, "wb") as out:
                out.write(response.content)
            print(f"✅ Output file saved as: {outfile_path}")
        else:
            print(f"❌ Error: {response.json()}")
