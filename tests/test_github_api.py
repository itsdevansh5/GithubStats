from app.github_service import get_next_url

 def test_get_next_url_returns_next_link():
    link = '<https://api.github.com/users/devansh/repos?page=2>; rel="next", <https://api.github.com/users/devansh/repos?page=5>; rel="last"'

    result = get_next_url(link)

    assert result == "https://api.github.com/users/devansh/repos?page=2"

