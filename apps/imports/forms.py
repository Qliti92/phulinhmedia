from django import forms


class ImportExcelForm(forms.Form):
    file = forms.FileField(label="File Excel")
