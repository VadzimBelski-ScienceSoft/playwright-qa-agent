"""Unit tests for agent_service helper functions."""

from __future__ import annotations

from src.models.requirement import Requirement
from src.services.agent_service import (
    _extract_url_from_requirement,
    _requirement_needs_url,
    _requires_authentication,
)


def _make_req(
    description: str = "",
    given: str = "",
    when: str = "",
    then: str = "",
    title: str = "Test",
) -> Requirement:
    return Requirement(
        id="REQ-001",
        number=1,
        title=title,
        description=description,
        given=given,
        when=when,
        then=then,
    )


class TestExtractUrlFromRequirement:
    def test_explicit_url_in_description(self) -> None:
        req = _make_req(description="Navigate to https://example.com and check the title.")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "https://example.com"

    def test_explicit_url_in_when(self) -> None:
        req = _make_req(when="User visits https://google.com")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "https://google.com"

    def test_explicit_url_in_given(self) -> None:
        req = _make_req(given="Given user is at https://staging.app.io/dashboard")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "https://staging.app.io/dashboard"

    def test_explicit_url_in_then(self) -> None:
        req = _make_req(then="Then redirect to https://success.example.com")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "https://success.example.com"

    def test_explicit_url_strips_trailing_punctuation(self) -> None:
        req = _make_req(description="Visit https://example.com, then check.")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "https://example.com"

    def test_falls_back_to_default_url(self) -> None:
        req = _make_req(description="Check the homepage loads correctly.")
        url = _extract_url_from_requirement(req, default_url="https://default.com")
        assert url == "https://default.com"

    def test_returns_none_when_no_url(self) -> None:
        req = _make_req(description="Some generic requirement.")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url is None

    def test_explicit_url_takes_priority_over_default(self) -> None:
        req = _make_req(description="Navigate to https://explicit.com")
        url = _extract_url_from_requirement(req, default_url="https://default.com")
        assert url == "https://explicit.com"

    def test_http_url_also_works(self) -> None:
        req = _make_req(description="Visit http://internal.corp/app")
        url = _extract_url_from_requirement(req, default_url=None)
        assert url == "http://internal.corp/app"


class TestRequirementNeedsUrl:
    def test_navigate_keyword(self) -> None:
        req = _make_req(description="Navigate to the login page")
        assert _requirement_needs_url(req) is True

    def test_visit_keyword(self) -> None:
        req = _make_req(when="User visits the homepage")
        assert _requirement_needs_url(req) is True

    def test_go_to_keyword(self) -> None:
        req = _make_req(description="Go to Google and verify it loads")
        assert _requirement_needs_url(req) is True

    def test_open_keyword(self) -> None:
        req = _make_req(given="Open the application")
        assert _requirement_needs_url(req) is True

    def test_page_keyword(self) -> None:
        req = _make_req(then="The page should display a success message")
        assert _requirement_needs_url(req) is True

    def test_url_keyword(self) -> None:
        req = _make_req(description="Verify the URL contains /dashboard")
        assert _requirement_needs_url(req) is True

    def test_no_url_keywords(self) -> None:
        req = _make_req(description="Verify the API response is valid JSON")
        assert _requirement_needs_url(req) is False

    def test_title_with_keyword(self) -> None:
        req = _make_req(title="Navigate to Dashboard", description="")
        assert _requirement_needs_url(req) is True


class TestRequiresAuthentication:
    def test_login_keyword(self) -> None:
        req = _make_req(description="User should be able to login with valid credentials")
        assert _requires_authentication(req) is True

    def test_log_in_phrase(self) -> None:
        req = _make_req(when="User logs in to the application")
        assert _requires_authentication(req) is True

    def test_sign_in_phrase(self) -> None:
        req = _make_req(description="Sign in with admin account")
        assert _requires_authentication(req) is True

    def test_authenticate_keyword(self) -> None:
        req = _make_req(given="User is authenticated")
        assert _requires_authentication(req) is True

    def test_credentials_keyword(self) -> None:
        req = _make_req(description="Enter credentials and submit")
        assert _requires_authentication(req) is True

    def test_username_keyword(self) -> None:
        req = _make_req(then="The username should be displayed in header")
        assert _requires_authentication(req) is True

    def test_password_keyword(self) -> None:
        req = _make_req(description="Change user password in settings")
        assert _requires_authentication(req) is True

    def test_no_auth_keywords(self) -> None:
        req = _make_req(description="Navigate to https://example.com and verify title")
        assert _requires_authentication(req) is False

    def test_title_with_auth_keyword(self) -> None:
        req = _make_req(title="User Login Flow", description="")
        assert _requires_authentication(req) is True
