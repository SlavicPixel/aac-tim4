from django import forms
from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
            'address',
            'gender',
            'date_of_birth',
            'faculty',
            'study_program',
            'year_of_study',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'text',
                    'placeholder': 'dd/mm/yyyy',
                },
                format='%d/%m/%Y'
            ),
        }
        labels = {
            'first_name': 'Ime',
            'last_name': 'Prezime',
            'address': 'Adresa',
            'gender': 'Spol',
            'date_of_birth': 'Datum rođenja',
            'faculty': 'Sastavnica',
            'study_program': 'Studijski smjer',
            'year_of_study': 'Godina studija',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].input_formats = ['%d/%m/%Y']