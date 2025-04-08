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
    DPI = 400
    doc = fitz.open(stream=file_stream, filetype="pdf")
    image_list = []

    for page_number in range(len(doc)):
        pix = doc[page_number].get_pixmap(matrix=fitz.Matrix(DPI / 72, DPI / 72))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        pixels = img.load()
        width, height = img.size

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if is_dark_color((r, g, b)):
                    pixels[x, y] = dark_blue

        image_list.append(img)

    output_stream = io.BytesIO()
    image_list[0].save(output_stream, format="PDF", save_all=True, append_images=image_list[1:], resolution=DPI, quality=95)
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
