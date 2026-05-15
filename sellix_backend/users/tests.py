from rest_framework.test import APITestCase
from users.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken


class UserMeViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="testpassword",
            name="Test User",
        )

        refresh = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    def test_get_user_me(self):

        response = self.client.get("/api/user/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["name"], "Test User")
        self.assertFalse(response.data["is_staff"])