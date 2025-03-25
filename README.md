# ML PDF Splitter App

This app is now designed to be deployed onto Azure cloud services via Azure Container Apps. The related PDF extraction Azure function must be deployed onto Azure functions.

The splitter app divides PDF files into chunks and makes multiple calls in parallel to the Azure function for rapid decoding of large pdf files into text.
