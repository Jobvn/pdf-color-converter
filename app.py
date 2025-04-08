import os
from flask import Flask, request, render_template, send_file, redirect
import fitz
from PIL import Image
import io

app = Flask(__name__)

def is_dark_color(color, threshold=80):
    r, g, b = color[:3]
    brightness = (r + g + b) / 3
    return brightness < threshold

def convert_pdf(file_stream):
    dark_blue = (10, 10, 95)
    DPI = 200  # reduced DPI significantly improves speed

    doc = fitz.open(stream=file_stream, filetype="pdf")
    image_list = []

    for page_number in range(len(doc)):
        pix = doc[page_number].get_pixmap(matrix=fitz.Matrix(DPI / 72, DPI / 72))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Optimize with numpy for significant speed boost
        import numpy as np
        img_np = np.array(img)

        # Calculate brightness and create mask quickly
        brightness = img_np.mean(axis=2)
        mask = brightness < 80

        # Apply color only to masked pixels (much faster)
        img_np[mask] = dark_blue

        # Convert numpy array back to PIL image
        img_processed = Image.fromarray(img_np)
        image_list.append(img_processed)

    output_stream = io.BytesIO()
    image_list[0].save(output_stream, format="PDF",
                       save_all=True, append_images=image_list[1:],
                       resolution=DPI)
    output_stream.seek(0)
    return output_stream


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return redirect(request.url)
        file = request.files['pdf_file']
        if file.filename == '':
            return redirect(request.url)
        if file and file.filename.lower().endswith('.pdf'):
            output_pdf = convert_pdf(file.read())
            return send_file(
                output_pdf,
                download_name="converted.pdf",
                as_attachment=True,
                mimetype='application/pdf'
            )
    return render_template('index.html')

if __name__ == "__main__":
    app.run()
