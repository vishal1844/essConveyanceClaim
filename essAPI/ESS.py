import datefinder
import pdfplumber
import re
import json
from address_extractor import ExtractAddress
import os

distance_patterns = [
    r'(\d+\.?\d*)\s*[kK][Mm]',
    r'(\d+\.?\d*)\s*kilometers',
]
amount_patterns = [
    r'[Tt]otal[\w\s]+₹\s*(\d+\.?\d*)'
]


class InvoiceParser(ExtractAddress):
    def __init__(self, invoice):
        self.invoice = pdfplumber.open(invoice)
        current_dir = os.path.dirname(__file__)
        location_json_path = os.path.join(current_dir, 'location.json')
        with open(location_json_path, 'r') as json_file:
            location = json.load(json_file)

        # location = json.load(open('./location.json'))
        super().__init__(location)
        invoiceText = ''
        self.address = []
        for page in self.invoice.pages:
            page=page.dedupe_chars(tolerance=1)
            invoiceText += page.extract_text()+' '
            super().extractWords(page.extract_words())
            super().extractLines()
            self.address.extend(super().getAddress())
        self.invoice.close()
        self.textList = invoiceText.split('\n')
        self.distance = set()
        self.date = set()
        self.cost = set()
        for pattern in amount_patterns:
            for amount in re.findall(pattern, invoiceText):
                self.cost.add(amount)

        for text in self.textList:
            self.findDates(text)
            self.findDistanceTravelled(text)

    def findDates(self, text):
        dates = list(datefinder.find_dates(text, strict=True))
        for d in dates:
            self.date.add(d.strftime("%d-%m-%Y"))

    def findDistanceTravelled(self, text):
        for pattern in distance_patterns:
            for km in re.findall(pattern, text):
                self.distance.add(float(km))

    def getData(self):
        print(self.date)
        return {'Date': list(self.date), 'Distance': list(self.distance), 'travelMode': [], 'sourceAddress': self.address, 'destinationAddress': self.address, 'amount': list(self.cost)}
