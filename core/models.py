from django.db import models

class Disability(models.Model):
    PERMANENT = 'permanent'
    TEMPORARY = 'temporary'
    TYPE_CHOICES = [
        (PERMANENT, 'Permanent'),
        (TEMPORARY, 'Temporary'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=PERMANENT
    )

    class Meta:
        verbose_name = 'Disability'
        verbose_name_plural = 'Disabilities'
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Student(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    GENDER_CHOICES = [
        (MALE, 'Muško'),
        (FEMALE, 'Žensko'),
        (OTHER, 'Ostalo'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    faculty = models.CharField(max_length=200)
    study_program = models.CharField(max_length=200)
    year_of_study = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    counselors = models.ManyToManyField(
        'users.Counselor',
        through='StudentCounselor',
        related_name='students'
    )

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
class StudentCounselor(models.Model):
    """
    Medjutablica za many-to-many vezu između Studenta i Savjetnika
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='counselor_assignments'
    )
    counselor = models.ForeignKey(
        'users.Counselor',
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    assigned_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Student-Counselor Assignment'
        verbose_name_plural = 'Student-Counselor Assignments'
        unique_together = ['student', 'counselor']
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.student} ↔ {self.counselor}"
    
class Document(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_type = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} ({self.student})"
    
class Accommodation(models.Model):
    PERMANENT = 'permanent'
    TEMPORARY = 'temporary'
    TYPE_CHOICES = [
        (PERMANENT, 'Permanent'),
        (TEMPORARY, 'Temporary'),
    ]

    PROPOSED = 'proposed'
    APPROVED = 'approved'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    STATUS_CHOICES = [
        (PROPOSED, 'Proposed'),
        (APPROVED, 'Approved'),
        (ACTIVE, 'Active'),
        (EXPIRED, 'Expired'),
    ]

    description = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=PERMANENT
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PROPOSED
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='accommodations'
    )
    disability = models.ForeignKey(
        Disability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accommodations'
    )

    class Meta:
        verbose_name = 'Accommodation'
        verbose_name_plural = 'Accommodations'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.student} – {self.description[:50]}"