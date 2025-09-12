import os
from flask import Flask, render_template, request, send_file
from rembg import new_session, remove
from io import BytesIO
from PIL import Image
import base64
import gc  # for garbage collection

app = Flask(__name__)

# Use smaller U2Net model for less memory usage
session = new_session("u2netp")

MAX_SIZE = 2048  # Maximum dimension to resize images

def resize_image(img):
    """Resize image while maintaining aspect ratio."""
    if max(img.size) > MAX_SIZE:
        img.thumbnail((MAX_SIZE, MAX_SIZE))
    return img

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "image" not in request.files:
            return "No file uploaded", 400
        file = request.files["image"]
        if file.filename == "":
            return "No selected file", 400

        # Read image
        input_data = file.read()
        original_image = Image.open(BytesIO(input_data))
        resized_image = resize_image(original_image.copy())  # Always assign

        # Convert resized image to bytes
        buf = BytesIO()
        resized_image.save(buf, format="PNG")
        resized_bytes = buf.getvalue()
        buf.close()

        # Remove background
        output_data = remove(resized_bytes, session=session)

        # Convert to base64 for display
        output_b64 = base64.b64encode(output_data).decode('utf-8')
        input_b64 = base64.b64encode(resized_bytes).decode('utf-8')

        # Get dimensions
        width, height = resized_image.size

        # Free memory
        del original_image, resized_image, resized_bytes, input_data, output_data
        gc.collect()

        return render_template(
            "index.html",
            output_image=output_b64,
            input_image=input_b64,
            original_width=width,
            original_height=height
        )

    return render_template("index.html", output_image=None, input_image=None)

@app.route("/download", methods=["POST"])
def download():
    image_data = request.form.get("image_data")
    if image_data:
        # Remove possible data URL prefix
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(image_data)
        return send_file(
            BytesIO(image_bytes),
            as_attachment=True,
            download_name="background_removed.png",
            mimetype="image/png"
        )
    return "No image to download", 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use environment port or default 5000
    app.run(host="0.0.0.0", port=port, debug=True)
