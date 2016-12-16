import importlib
from django.test import TestCase
from note.models import Note
from note.factories import NoteFactory
from django.contrib.auth.models import User
from member.factories import ClientFactory
from django.core.urlresolvers import reverse
from django.utils import timezone
from sous_chef.tests import TestMixin as SousChefTestMixin


class NoteTestCase(TestCase):

    fixtures = ['routes.json']

    @classmethod
    def setUpTestData(cls):
        cls.clients = ClientFactory()
        cls.admin = User.objects.create_superuser(
            username='admin', email='testadmin@example.com', password='test1234')
        cls.note = NoteFactory.create(client=cls.clients, author=cls.admin)

    def test_attach_note_to_member(self):
        """Create a note attached to a member"""
        note = self.note
        self.assertEqual(self.clients, note.client)
        self.assertEqual(self.admin, note.author)

    def test_mark_as_read(self):
        """Mark a note as read"""
        note = self.note
        self.assertFalse(note.is_read)
        note.mark_as_read()
        self.assertTrue(note.is_read)

    def test_mark_as_unread(self):
        """Mark a note as unread"""
        note = self.note
        note.mark_as_read()
        self.assertTrue(note.is_read)
        note.mark_as_unread()
        self.assertFalse(note.is_read)

    def test_str_includes_note(self):
        """An note listing must include the note text"""
        note = Note.objects.create(
            client=self.clients,
            author=self.admin,
            note='x123y'
        )
        self.assertTrue('x123y' in note.note)

    def test_anonymous_user_gets_redirected_to_login_page(self):
        self.client.logout()
        response = self.client.get('/note/')
        self.assertRedirects(
            response,
            reverse('page:login') + '?next=/note/',
            status_code=302
        )


class NoteAddTestCase(NoteTestCase):

    def setUp(self):
        self.client.force_login(self.admin, 'django.contrib.auth.backends.ModelBackend')

    def test_create_set_fields(self):
        """
        Test if author, date, is_read are correctly set.
        """
        time_1 = timezone.now()
        response = self.client.post(reverse('note:note_add'), {
            'note': "test note TEST_PHRASE",
            "client": ClientFactory().pk,
            "priority": 'normal'
        }, follow=False)
        time_2 = timezone.now()
        self.assertEqual(response.status_code, 302)  # successful creation
        note = Note.objects.get(note__contains="TEST_PHRASE")
        self.assertEqual(note.author, self.admin)
        self.assertEqual(note.is_read, False)
        self.assertTrue(time_1 <= note.date <= time_2)

    def test_redirects_users_who_do_not_have_edit_permission(self):
        # Setup
        user = User.objects.create_user(username='foo', email='foo@example.com', password='secure')
        user.is_staff = True
        user.save()
        self.client.login(username='foo', password='secure')
        url = reverse('note:note_add')
        # Run
        response = self.client.get(url)
        # Check
        self.assertEqual(response.status_code, 302)

    def test_allow_access_to_users_with_edit_permission(self):
        # Setup
        user = User.objects.create_superuser(
            username='foo', email='foo@example.com', password='secure')
        user.save()
        self.client.login(username='foo', password='secure')
        url = reverse('note:note_add')
        # Run
        response = self.client.post(url, {
            'note': "test note TEST_PHRASE",
            "client": ClientFactory().pk,
            "priority": 'normal'
        }, follow=True)
        # Check
        self.assertEqual(response.status_code, 200)


class ClientNoteAddTestCase(NoteTestCase):

    def setUp(self):
        self.client.force_login(self.admin, 'django.contrib.auth.backends.ModelBackend',)

    def test_get_with_client_pk(self):
        client = ClientFactory()
        response = self.client.get(reverse(
            'member:client_notes_add',
            kwargs={'pk': client.pk}
        ))
        self.assertEqual(response.status_code, 200)
        content = str(response.content, encoding=response.charset)
        self.assertIn(str(client.pk), content)
        self.assertIn(client.member.firstname, content)
        self.assertIn(client.member.lastname, content)

    def test_redirects_users_who_do_not_have_edit_permission(self):
        # Setup
        user = User.objects.create_user(username='foo', email='foo@example.com', password='secure')
        user.is_staff = True
        user.save()
        self.client.login(username='foo', password='secure')
        client = ClientFactory()
        url = reverse('member:client_notes_add', kwargs={'pk': client.pk})
        # Run
        response = self.client.get(url)
        # Check
        self.assertEqual(response.status_code, 302)

    def test_allow_access_to_users_with_edit_permission(self):
        # Setup
        user = User.objects.create_superuser(
            username='foo', email='foo@example.com', password='secure')
        user.save()
        self.client.login(username='foo', password='secure')
        client = ClientFactory()
        url = reverse('member:client_notes_add', kwargs={'pk': client.pk})
        # Run
        response = self.client.get(url)
        # Check
        self.assertEqual(response.status_code, 200)


class RedirectAnonymousUserTestCase(SousChefTestMixin, TestCase):

    fixtures = ['routes.json']

    def test_anonymous_user_gets_redirect_to_login_page(self):
        check = self.assertRedirectsWithAllMethods
        check(reverse('note:note_list'))
        check(reverse('note:read', kwargs={'id': 1}))
        check(reverse('note:unread', kwargs={'id': 1}))
        check(reverse('note:note_add'))


class NoteListViewTestCase(SousChefTestMixin, TestCase):
    fixtures = ['routes.json']

    def test_redirects_users_who_do_not_have_read_permission(self):
        # Setup
        User.objects.create_user(username='foo', email='foo@example.com', password='secure')
        self.client.login(username='foo', password='secure')
        url = reverse('note:note_list')
        # Run & check
        self.assertRedirectsWithAllMethods(url)

    def test_allow_access_to_users_with_read_permission(self):
        # Setup
        user = User.objects.create_user(username='foo', email='foo@example.com', password='secure')
        user.is_staff = True
        user.save()
        self.client.login(username='foo', password='secure')
        url = reverse('note:note_list')
        # Run
        response = self.client.get(url)
        # Check
        self.assertEqual(response.status_code, 200)
