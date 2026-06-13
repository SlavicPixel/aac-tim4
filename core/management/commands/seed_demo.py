from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from datetime import date, timedelta
from django.utils import timezone

from core.models import (
    Disability, Student, StudentCounselor, Meeting,
    Accommodation, Guideline, Document, PeerSupportSession, AuditLog,
)
from users.models import Counselor, PeerSupportUser

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with demo data for deployment (Railway).'

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

        self.stdout.write(self.style.NOTICE('Starting demo seed...'))

        with transaction.atomic():
            self._create_superuser()
            counselors = self._create_counselors()
            peer_supports = self._create_peer_support_users()
            disabilities = self._create_disabilities()
            self._create_guidelines(disabilities)
            students = self._create_students(counselors, peer_supports)
            self._create_meetings(students, counselors)
            self._create_accommodations(students, disabilities)
            self._create_documents(students)
            self._create_peer_support_sessions(peer_supports, students)
            self._create_audit_logs(students, counselors)

        self.stdout.write(self.style.SUCCESS('Demo seed completed successfully!'))
        self._print_credentials()

    def _reset_data(self):
        """Deletes all data except superusers."""
        AuditLog.objects.all().delete()
        PeerSupportSession.objects.all().delete()
        Document.objects.all().delete()
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
                password='mvLAwwSnsAEe',
                first_name='Admin',
                last_name='Administrator',
            )
            self.stdout.write('Superuser "admin" created.')
        else:
            self.stdout.write('Superuser "admin" already exists, skipping.')

    def _create_counselors(self):
        # (username, first_name, last_name, email, password)
        counselors_data = [
            ('savjetnik1', 'Ana', 'Horvat', 'ana.horvat@aac.local', 'dX422nkSd8ib'),
            ('savjetnik2', 'Marko', 'Kovač', 'marko.kovac@aac.local', 'WYocQMykrtFI'),
        ]
        counselors = []
        for username, first_name, last_name, email, password in counselors_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Counselor user "{username}" created.')

            counselor, _ = Counselor.objects.get_or_create(user=user)
            counselors.append(counselor)
        return counselors

    def _create_peer_support_users(self):
        # (username, first_name, last_name, email, password)
        peer_supports_data = [
            ('peer1', 'Ivan', 'Novak', 'ivan.novak@aac.local', '8d3U24BahE58'),
            ('peer2', 'Maja', 'Babić', 'maja.babic@aac.local', 'LNkPfLZULlpV'),
        ]
        peer_supports = []
        for username, first_name, last_name, email, password in peer_supports_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                }
            )
            if created:
                user.set_password(password)
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
        # Prvih 5 studenata ide savjetniku1 (puni demo), 6. studentica ide savjetniku2 (minimalan)
        students_data = [
            ('Petra', 'Marić', 'Pula', 'F', date(2002, 5, 14), 'FIDIT', 'Informatika', 2),
            ('Luka', 'Vidović', 'Rijeka', 'M', date(2001, 9, 22), 'FFRI', 'Psihologija', 3),
            ('Iva', 'Tomić', 'Zagreb', 'F', date(2003, 1, 8), 'PRAVRI', 'Pravo', 1),
            ('Filip', 'Knežević', 'Split', 'M', date(2000, 11, 30), 'GRADRI', 'Građevinarstvo', 4),
            ('Doris', 'Pavić', 'Osijek', 'F', date(2002, 3, 17), 'EFRI', 'Ekonomija', 2),
            ('Vedran', 'Šimić', 'Zadar', 'M', date(2001, 6, 5), 'FIDIT', 'Informatika', 3),
        ]
        students = []
        for i, (first_name, last_name, address, gender, dob, faculty, program, year) in enumerate(students_data):
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
                if i < 5:
                    # Prvih 5 studenata: savjetnik1 (puni demo)
                    StudentCounselor.objects.create(student=student, counselor=counselors[0])
                else:
                    # Zadnji student: savjetnik2 (minimalan)
                    StudentCounselor.objects.create(student=student, counselor=counselors[1])

                # Petra i Iva su dodijeljene peer1 (puni demo, M:N)
                if first_name in ('Petra', 'Iva') and peer_supports:
                    peer_supports[0].students.add(student)

                # Doris je dodijeljena peer2 (minimalan, bez sesija)
                if first_name == 'Doris' and len(peer_supports) > 1:
                    peer_supports[1].students.add(student)

                self.stdout.write(f'Student "{first_name} {last_name}" created.')
        return students

    def _create_meetings(self, students, counselors):
        if not students or not counselors:
            return

        now = timezone.now()
        meetings_data = [
            # Petra (students[0]) - puna povijest
            (students[0], counselors[0], now - timedelta(days=45), 'initial', 'in_person', 'Inicijalni sastanak sa studenticom. Razgovor o potrebama i mogućim prilagodbama.'),
            (students[0], counselors[0], now - timedelta(days=30), 'follow_up', 'video', 'Sastanak praćenja, sve napreduje prema planu.'),
            (students[0], counselors[0], now - timedelta(days=10), 'follow_up', 'in_person', 'Praćenje primjene prilagodbe na ispitima.'),
            (students[0], counselors[0], now + timedelta(days=5), 'follow_up', 'in_person', ''),

            # Luka (students[1])
            (students[1], counselors[0], now - timedelta(days=20), 'initial', 'in_person', 'Inicijalni sastanak.'),
            (students[1], counselors[0], now - timedelta(days=3), 'follow_up', 'phone', 'Kratak telefonski razgovor o ispitnim rokovima.'),

            # Iva (students[2])
            (students[2], counselors[0], now - timedelta(days=12), 'initial', 'phone', 'Telefonski inicijalni sastanak.'),

            # Filip (students[3]) - bez sastanaka dulje od 30 dana (za notifikaciju)
            (students[3], counselors[0], now - timedelta(days=50), 'initial', 'in_person', 'Inicijalni sastanak prije ozljede ruke.'),

            # Doris (students[4]) - nadolazeći sastanak
            (students[4], counselors[0], now + timedelta(days=2), 'initial', 'video', ''),
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

        today = date.today()
        accommodations_data = [
            # (student, disability, description, type, status, start_date, end_date)
            (students[0], disabilities.get('Disleksija'), 'Produženo vrijeme za ispit (50%) i korištenje računala.', 'permanent', 'active', today - timedelta(days=40), None),
            (students[1], disabilities.get('ADHD'), 'Produženo vrijeme za ispit (25%) i tihi prostor za polaganje.', 'permanent', 'approved', today - timedelta(days=20), None),
            (students[2], disabilities.get('Anksiozni poremećaj'), 'Mogućnost usmenog ispita umjesto pisanog.', 'permanent', 'proposed', today - timedelta(days=5), None),
            # Privremena prilagodba koja istječe za 14 dana - za notifikaciju "pri isteku"
            (students[3], disabilities.get('Privremena ozljeda'), 'Korištenje računala umjesto rukopisa zbog ozljede ruke.', 'temporary', 'active', today - timedelta(days=30), today + timedelta(days=14)),
        ]

        for student, disability, description, acc_type, status, start_date, end_date in accommodations_data:
            if not disability:
                continue
            accommodation, created = Accommodation.objects.get_or_create(
                student=student,
                disability=disability,
                defaults={
                    'description': description,
                    'type': acc_type,
                    'status': status,
                    'start_date': start_date,
                    'end_date': end_date,
                }
            )
            if created:
                self.stdout.write(f'Accommodation for {student.full_name} created.')

    def _create_documents(self, students):
        if not students:
            return

        # Jedan jednostavan tekstualni dokument za Petru, za demo prikaza dokumentacije
        student = students[0]
        document, created = Document.objects.get_or_create(
            student=student,
            name='Medicinska dokumentacija - Petra Marić',
            defaults={'file_type': 'txt'}
        )
        if created:
            content = (
                "Demo dokument za prikaz funkcionalnosti dokumentacije.\n"
                "Ovaj dokument je dio demo podataka i ne sadrži stvarne medicinske podatke."
            )
            document.file.save(
                'demo_dokumentacija_petra.txt',
                ContentFile(content.encode('utf-8')),
                save=True,
            )
            self.stdout.write(f'Document for {student.full_name} created.')

    def _create_peer_support_sessions(self, peer_supports, students):
        if not peer_supports or not students:
            return

        peer1 = peer_supports[0]
        petra = students[0]
        iva = students[2]
        now = timezone.now().date()

        sessions_data = [
            # Petra - povijest kroz zadnja dva mjeseca
            (petra, now - timedelta(days=50), 60, 'Pratnja na predavanja i pomoć s bilješkama.'),
            (petra, now - timedelta(days=35), 45, 'Pomoć u snalaženju po kampusu.'),
            (petra, now - timedelta(days=20), 60, 'Pratnja na predavanja.'),
            (petra, now - timedelta(days=10), 30, 'Kratka pomoć oko prijave ispita.'),
            (petra, now - timedelta(days=2), 45, 'Pomoć s organizacijom bilješki za ispitni rok.'),
            (petra, now + timedelta(days=3), 60, 'Dogovorena pratnja na ispit.'),

            # Iva
            (iva, now - timedelta(days=25), 30, 'Pomoć oko prijave ispita.'),
            (iva, now - timedelta(days=8), 60, 'Pratnja na predavanja.'),
            (iva, now + timedelta(days=6), 45, 'Dogovoren termin za pomoć s pripremom za ispit.'),
        ]

        created_count = 0
        for student, session_date, duration, description in sessions_data:
            _, created = PeerSupportSession.objects.get_or_create(
                peer_support_user=peer1,
                student=student,
                date=session_date,
                defaults={
                    'duration_minutes': duration,
                    'description': description,
                },
            )
            if created:
                created_count += 1

        if created_count:
            self.stdout.write(f'{created_count} peer support sessions created.')

    def _create_audit_logs(self, students, counselors):
        if not students or not counselors:
            return

        user = counselors[0].user
        now = timezone.now()
        entries = [
            (now - timedelta(days=45), AuditLog.CREATED, 'Student', students[0].pk, str(students[0])),
            (now - timedelta(days=40), AuditLog.CREATED, 'Accommodation', students[0].pk, f'Prilagodba za {students[0].full_name}'),
            (now - timedelta(days=10), AuditLog.UPDATED, 'Student', students[0].pk, str(students[0])),
            (now - timedelta(days=5), AuditLog.UPDATED, 'Accommodation', students[1].pk, f'Prilagodba za {students[1].full_name}'),
        ]

        created_count = 0
        for timestamp, action, model_name, object_id, object_repr in entries:
            if AuditLog.objects.filter(
                user=user, action=action, model_name=model_name,
                object_id=object_id, object_repr=object_repr,
            ).exists():
                continue

            log = AuditLog.objects.create(
                user=user, action=action, model_name=model_name,
                object_id=object_id, object_repr=object_repr,
            )
            # auto_now_add ignorira create(); postavi pravi timestamp preko update
            AuditLog.objects.filter(pk=log.pk).update(timestamp=timestamp)
            created_count += 1

        if created_count:
            self.stdout.write(f'{created_count} audit log entries created.')

    def _print_credentials(self):
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=== Demo credentials ==='))
        self.stdout.write('Superuser: admin / mvLAwwSnsAEe')
        self.stdout.write('Counselor 1 (puni demo): savjetnik1 / dX422nkSd8ib')
        self.stdout.write('Counselor 2 (minimalan): savjetnik2 / WYocQMykrtFI')
        self.stdout.write('Peer support 1 (puni demo): peer1 / 8d3U24BahE58')
        self.stdout.write('Peer support 2 (minimalan): peer2 / LNkPfLZULlpV')
        self.stdout.write('')
