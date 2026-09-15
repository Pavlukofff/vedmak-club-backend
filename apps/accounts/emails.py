from django.core import signing
from django.core.mail import send_mail

EMAIL_VERIFICATION_SALT = "accounts.email-verification"
EMAIL_VERIFICATION_MAX_AGE = 60 * 60 * 24 * 3  # 3 дня


def make_email_verification_token(user):
    return signing.dumps({"user_id": user.pk, "email": user.email}, salt=EMAIL_VERIFICATION_SALT)


def read_email_verification_token(token):
    """Возвращает {"user_id", "email"} или бросает signing.BadSignature/SignatureExpired."""
    return signing.loads(
        token, salt=EMAIL_VERIFICATION_SALT, max_age=EMAIL_VERIFICATION_MAX_AGE,
    )


def send_verification_email(user, request=None):
    token = make_email_verification_token(user)
    verify_path = f"/api/accounts/verify-email/?token={token}"
    base_url = request.build_absolute_uri("/") if request else "http://localhost:8000/"
    link = base_url.rstrip("/") + verify_path

    send_mail(
        subject="Подтверждение email — Цех ведьмаков",
        message=(
            f"Здравствуйте, {user.display_name}!\n\n"
            f"Подтвердите ваш email, перейдя по ссылке:\n{link}\n\n"
            "Ссылка действительна 3 дня. Пока email не подтверждён, вы можете "
            "пользоваться сайтом — ограничена только загрузка собственного аватара."
        ),
        from_email=None,
        recipient_list=[user.email],
    )
