# Use an official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# # for the extractADR_RDF script
# # Install dependencies
# RUN pip install --no-cache-dir rdflib requests  
# # Set the command to run the script. command: docker build -t extract-adr .
# CMD ["python", "/app/extractADR_RDF.py"]

# # for the extractData_RDF script
# # Install dependencies
# RUN pip install --no-cache-dir rdflib requests fuzzywuzzy pandas
# # Set the command to run the script. command: docker build -t extract-lareb-data .
# CMD ["python", "/app/extractData_RDF.py"]

# # for the extractSideEFF_RDF script
# # Install dependencies
# RUN pip install --no-cache-dir rdflib requests
# # Set the command to run the script. command: docker build -t extract-sideeff-data .
# CMD ["python", "/app/extractSideEFF_RDF.py"]

# # for the extractVigi_RDF script
# # Install dependencies
# RUN pip install --no-cache-dir rdflib requests pandas
# # Set the command to run the script. command: docker build -t extract-vigi-data .
# CMD ["python", "/app/extractVigi_RDF.py"]