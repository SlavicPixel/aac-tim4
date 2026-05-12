from django import forms
from .models import Student, Document, Meeting


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

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'file']
        labels = {
            'name': 'Naziv dokumenta',
            'file': 'Datoteka',
        }

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['student', 'date_time', 'type', 'format', 'notes']
        widgets = {
            'date_time': forms.DateTimeInput(
                attrs={
                    'type': 'text',
                    'placeholder': 'dd/mm/yyyy HH:MM',
                },
                format='%d/%m/%Y %H:%M'
            ),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'student': 'Student',
            'date_time': 'Datum i vrijeme',
            'type': 'Tip sastanka',
            'format': 'Format',
            'notes': 'Bilješke',
        }

    def __init__(self, *args, **kwargs):
        counselor = kwargs.pop('counselor', None)
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        self.fields['date_time'].input_formats = ['%d/%m/%Y %H:%M']

        # Limit student choices to those assigned to the counselor
        if counselor:
            self.fields['student'].queryset = Student.objects.filter(
                counselors=counselor,
                is_active=True
            )

        # If creating meeting from student detail, lock the student field
        if student:
            self.fields['student'].initial = student
            self.fields['student'].disabled = True