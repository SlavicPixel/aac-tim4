from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from django.utils import timezone

from core.models import (
    Disability, Student, StudentCounselor, Meeting,
    Accommodation, Guideline,
)
from users.models import Counselor, PeerSupportUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with test data for development and testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Deletes all existing data before seeding (except superusers).',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Resetting database...'))
            self._reset_data()

        self.stdout.write(self.style.NOTICE('Starting seed...'))

        with transaction.atomic():
            self._create_superuser()
            counselors = self._create_counselors()
            peer_supports = self._create_peer_support_users()
            disabilities = self._create_disabilities()
            self._create_guidelines(disabilities)
            students = self._create_students(counselors, peer_supports)
            self._create_meetings(students, counselors)
            self._create_accommodations(students, disabilities)

        self.stdout.write(self.style.SUCCESS('Seed completed successfully!'))
        self._print_credentials()

    def _reset_data(self):
        """Deletes all data except superusers."""
        Meeting.objects.all().delete()
        Accommodation.objects.all().delete()
        StudentCounselor.objects.all().delete()
        Student.objects.all().delete()
        Guideline.objects.all().delete()
        Disability.objects.all().delete()
        PeerSupportUser.objects.all().delete()
        Counselor.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Database reset.'))

    def _create_superuser(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@aac.local',
                password='admin',
                first_name='Admin',
                last_name='Administrator',
            )
            self.stdout.write('Superuser "admin" created.')
        else:
            self.stdout.write('Superuser "admin" already exists, skipping.')

    def _create_counselors(self):
        counselors_data = [
            ('savjetnik1', 'Ana', 'Horvat', 'ana.horvat@aac.local'),
            ('savjetnik2', 'Marko', 'Kovač', 'marko.kovac@aac.local'),
        ]
        counselors = []
        for username, first_name, last_name, email in counselors_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Counselor user "{username}" created.')

            counselor, _ = Counselor.objects.get_or_create(user=user)
            counselors.append(counselor)
        return counselors

    def _create_peer_support_users(self):
        peer_supports_data = [
            ('peer1', 'Ivan', 'Novak', 'ivan.novak@aac.local'),
            ('peer2', 'Maja', 'Babić', 'maja.babic@aac.local'),
        ]
        peer_supports = []
        for username, first_name, last_name, email in peer_supports_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Peer support user "{username}" created.')

            peer_support, _ = PeerSupportUser.objects.get_or_create(user=user)
            peer_supports.append(peer_support)
        return peer_supports

    def _create_disabilities(self):
        disabilities_data = [
            ('Disleksija', 'Specifična teškoća učenja koja utječe na vještine čitanja, pisanja i pravopisa.', 'permanent'),
            ('Disgrafija', 'Specifična teškoća u pisanju koja utječe na rukopis, ortografiju i pisanu produkciju.', 'permanent'),
            ('ADHD', 'Poremećaj pažnje i hiperaktivnosti koji utječe na koncentraciju i organizaciju.', 'permanent'),
            ('Oštećenje vida', 'Djelomično ili potpuno oštećenje vida koje zahtijeva prilagodbu nastavnih materijala.', 'permanent'),
            ('Oštećenje sluha', 'Djelomično ili potpuno oštećenje sluha koje zahtijeva prilagodbu komunikacije i nastave.', 'permanent'),
            ('Motorička teškoća', 'Teškoće u motoričkoj kontroli koje utječu na pisanje, kretanje ili korištenje računala.', 'permanent'),
            ('Anksiozni poremećaj', 'Stanje povišene anksioznosti koje može utjecati na ispitne situacije i prezentacije.', 'permanent'),
            ('Privremena ozljeda', 'Privremena fizička ozljeda (npr. slomljena ruka, oporavak nakon operacije).', 'temporary'),
            ('Kronična bolest', 'Kronična zdravstvena stanja koja zahtijevaju povremenu prilagodbu (npr. epilepsija, dijabetes).', 'permanent'),
            ('Privremeno bolničko liječenje', 'Privremena nemogućnost prisustvovanja nastavi zbog hospitalizacije.', 'temporary'),
        ]
        disabilities = {}
        for name, description, disability_type in disabilities_data:
            disability, created = Disability.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'type': disability_type,
                }
            )
            disabilities[name] = disability
            if created:
                self.stdout.write(f'Disability "{name}" created.')
        return disabilities

    def _create_guidelines(self, disabilities):
        guidelines_data = [
            {
                'title': 'Produženo vrijeme za ispit',
                'content': 'Studentu se odobrava produženo vrijeme za pisanje ispita, najčešće 25-50% dodatnog vremena u odnosu na standardno trajanje. Konkretno produženje određuje se na temelju procjene potreba studenta i prirode ispita.',
                'disabilities': ['Disleksija', 'Disgrafija', 'ADHD', 'Anksiozni poremećaj', 'Motorička teškoća', 'Privremena ozljeda'],
            },
            {
                'title': 'Usmeni ispit umjesto pisanog',
                'content': 'Studentu se omogućuje polaganje ispita u usmenom obliku kao alternativa pisanom ispitu. Sadržaj i razina znanja koja se provjerava ostaju identični kao na pisanom ispitu.',
                'disabilities': ['Disgrafija', 'Motorička teškoća', 'Oštećenje vida', 'Privremena ozljeda'],
            },
            {
                'title': 'Korištenje računala na ispitu',
                'content': 'Studentu se odobrava korištenje računala za pisanje odgovora na ispitu umjesto rukopisa. Računalo treba biti pripremljeno bez pristupa internetu i bez relevantnih datoteka.',
                'disabilities': ['Disgrafija', 'Disleksija', 'Motorička teškoća', 'Oštećenje vida'],
            },
        ]

        for guideline_data in guidelines_data:
            guideline, created = Guideline.objects.get_or_create(
                title=guideline_data['title'],
                defaults={'content': guideline_data['content']}
            )
            if created:
                for disability_name in guideline_data['disabilities']:
                    if disability_name in disabilities:
                        guideline.disabilities.add(disabilities[disability_name])
                self.stdout.write(f'Guideline "{guideline.title}" created.')

    def _create_students(self, counselors, peer_supports):
        students_data = [
            ('Petra', 'Marić', 'Pula', 'F', date(2002, 5, 14), 'FIDIT', 'Informatika', 2),
            ('Luka', 'Vidović', 'Rijeka', 'M', date(2001, 9, 22), 'FFRI', 'Psihologija', 3),
            ('Iva', 'Tomić', 'Zagreb', 'F', date(2003, 1, 8), 'PRAVRI', 'Pravo', 1),
            ('Filip', 'Knežević', 'Split', 'M', date(2000, 11, 30), 'GRADRI', 'Građevinarstvo', 4),
        ]
        students = []
        for first_name, last_name, address, gender, dob, faculty, program, year in students_data:
            student, created = Student.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'address': address,
                    'gender': gender,
                    'date_of_birth': dob,
                    'faculty': faculty,
                    'study_program': program,
                    'year_of_study': year,
                }
            )
            students.append(student)
            if created:
                # Dodijeli prvog savjetnika svakom studentu
                StudentCounselor.objects.create(
                    student=student,
                    counselor=counselors[0]
                )
                # Drugog savjetnika dodjeli samo prvom studentu (za testiranje M:N)
                if first_name == 'Petra':
                    StudentCounselor.objects.create(
                        student=student,
                        counselor=counselors[1]
                    )
                # Dodjeli peer support prvom studentu
                if first_name == 'Petra' and peer_supports:
                    peer_supports[0].student = student
                    peer_supports[0].save()

                self.stdout.write(f'Student "{first_name} {last_name}" created.')
        return students

    def _create_meetings(self, students, counselors):
        if not students or not counselors:
            return

        now = timezone.now()
        meetings_data = [
            (students[0], counselors[0], now - timedelta(days=30), 'initial', 'in_person', 'Inicijalni sastanak sa studenticom. Razgovor o potrebama i mogućim prilagodbama.'),
            (students[0], counselors[0], now - timedelta(days=15), 'follow_up', 'video', 'Sastanak praćenja, sve napreduje prema planu.'),
            (students[1], counselors[0], now - timedelta(days=20), 'initial', 'in_person', 'Inicijalni sastanak.'),
            (students[2], counselors[0], now - timedelta(days=10), 'initial', 'phone', 'Telefonski inicijalni sastanak.'),
            (students[0], counselors[0], now + timedelta(days=7), 'follow_up', 'in_person', ''),
        ]

        for student, counselor, dt, m_type, m_format, notes in meetings_data:
            meeting, created = Meeting.objects.get_or_create(
                student=student,
                counselor=counselor,
                date_time=dt,
                defaults={
                    'type': m_type,
                    'format': m_format,
                    'notes': notes,
                }
            )
            if created:
                self.stdout.write(f'Meeting on {dt.strftime("%d/%m/%Y")} created.')

    def _create_accommodations(self, students, disabilities):
        if not students or not disabilities:
            return

        accommodations_data = [
            (students[0], disabilities.get('Disleksija'), 'Produženo vrijeme za ispit (50%) i korištenje računala.', 'permanent', 'active'),
            (students[1], disabilities.get('ADHD'), 'Produženo vrijeme za ispit (25%) i tihi prostor za polaganje.', 'permanent', 'approved'),
            (students[2], disabilities.get('Privremena ozljeda'), 'Korištenje računala umjesto rukopisa zbog ozljede ruke.', 'temporary', 'active'),
        ]

        for student, disability, description, acc_type, status in accommodations_data:
            if not disability:
                continue
            accommodation, created = Accommodation.objects.get_or_create(
                student=student,
                disability=disability,
                defaults={
                    'description': description,
                    'type': acc_type,
                    'status': status,
                    'start_date': date.today() - timedelta(days=20),
                }
            )
            if created:
                self.stdout.write(f'Accommodation for {student.full_name} created.')

    def _print_credentials(self):
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=== Test credentials ==='))
        self.stdout.write('Superuser: admin / admin')
        self.stdout.write('Counselor 1: savjetnik1 / password123')
        self.stdout.write('Counselor 2: savjetnik2 / password123')
        self.stdout.write('Peer support 1: peer1 / password123')
        self.stdout.write('Peer support 2: peer2 / password123')
        self.stdout.write('')