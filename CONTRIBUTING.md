# CONTRIBUTING

## Run Docker Locally
    ```
    docker run -dp 5000:5005 -w /app -v "$(pwd):/app" <image-name> sh -c flask run --host=0.0.0.0
    ```