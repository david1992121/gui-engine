from string import whitespace
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import white, black
from math import ceil
from basics.models import ReceiptSetting
from django.conf import settings
from datetime import datetime

global current_path
current_path = os.path.dirname(os.path.realpath(__file__))


def make_page(seed, date, name, no, point):

    pdfmetrics.registerFont(
        TTFont(
            'Hebrew',
            os.path.join(
                current_path,
                'UtsukushiMincho.ttf')))

    # read your existing PDF
    existing_pdf = PdfFileReader(
        open(
            os.path.join(
                current_path,
                "template.pdf"),
            "rb"))

    # create a new PDF with Reportlab
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Hebrew", 12)
    can.drawString(180, 106, seed)
    can.drawString(480, 210, str(no))
    can.drawString(480, 183, date)

    can.setFont("Helvetica-Bold", 20)
    can.drawString(280, 138, "{:3,d}".format(point))

    # put fixed information
    receipt_queryset = ReceiptSetting.objects.all()
    if receipt_queryset.count() > 0:
        receipt_data = receipt_queryset.get()
        can.setFont("Hebrew", 12)
        offset = 10
        can.drawString(
            280,
            80 + offset,
            receipt_data.company_name.encode('utf-8'))
        can.drawString(
            280,
            66 + offset,
            receipt_data.postal_code.encode('utf-8'))
        can.drawString(280, 52 + offset, receipt_data.address.encode('utf-8'))
        can.drawString(280, 38 + offset, receipt_data.building)
        can.drawString(280, 24 + offset, receipt_data.phone_number)

        can.drawString(540, 32, receipt_data.charger)

    can.setFont("Hebrew", 15)
    can.drawString(280, 210, name)
    can.save()

    # move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)

    # add content on the existing page
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))

    return page


def export_pdf(seed, date, name_array, number, no, point, user_id):
    per_point = ceil(point / number * 1.1)
    output = PdfFileWriter()

    for i in range(number):

        if i < len(name_array):
            name = name_array[i]
        else:
            name = ""

        page = make_page(seed, date, name, no, per_point)
        output.addPage(page)

    # finally, write "output" to a real file
    file_name = '領収書_{}_{}.pdf'.format(no, user_id)
    receipt_file = os.path.join(
        settings.BASE_DIR,
        "static/pdf/{}".format(file_name))

    if os.path.exists(receipt_file):
        os.remove(receipt_file)

    outputStream = open(receipt_file, "wb")
    output.write(outputStream)
    outputStream.close()

    return "static/pdf/{}".format(file_name)
