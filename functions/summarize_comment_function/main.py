import vertexai
from vertexai.preview.language_models import TextGenerationModel
import os
from google.cloud import bigquery

# Set your own parameter
PROJECT_ID = os.environ.get('PROJECT_ID', 'Specified environment variable is not set.')
BQ_DATASET = 'youtube'
BQ_SUMMARY_TABLE = 'summary'

def hello_palm(request):
    """Ideation example with a Large Language Model"""

    # TODO developer - override these parameters as needed:
    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 256,   
        "top_p": .8,                
        "top_k": 40,                 
    }

    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(
        'Give me ten interview questions for the role of program manager.',
        **parameters,
    )
    print(f"Response from Model: {response.text}")