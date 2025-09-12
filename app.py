import os
from flask import Flask, render_template, request, send_file
from rembg import new_session, remove
from io import BytesIO
from PIL import Image
import base64

app = Flask(__name__)

# Create a session using the u2net model
session = new_session("u2net")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "image" not in request.files:
            return "No file uploaded", 400
        file = request.files["image"]
        if file.filename == "":
            return "No selected file", 400

        # Read and process image without saving
        input_data = file.read()
        
        # Process image (remove background)
        output_data = remove(input_data, session=session)
        
        # Convert to base64 for display
        output_b64 = base64.b64encode(output_data).decode('utf-8')
        input_b64 = base64.b64encode(input_data).decode('utf-8')
        
        # Get original image dimensions
        original_image = Image.open(BytesIO(input_data))
        original_width, original_height = original_image.size
        
        return render_template(
            "index.html", 
            output_image=output_b64,
            input_image=input_b64,
            original_width=original_width,
            original_height=original_height
        )

    return render_template("index.html", output_image=None, input_image=None)


@app.route("/download", methods=["POST"])
def download():
    if request.method == "POST":
        # Get the base64 image data from the form
        image_data = request.form.get("image_data")
        
        if image_data:
            # Remove the data URL prefix if present
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]
            
            # Decode the base64 image
            image_bytes = base64.b64decode(image_data)
            
            # Create a BytesIO object and return as file
            return send_file(
                BytesIO(image_bytes),
                as_attachment=True,
                download_name="background_removed.png",
                mimetype="image/png"
            )
    
    return "No image to download", 400


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Use Render's port if available
    app.run(host="0.0.0.0", port=port, debug=True)
