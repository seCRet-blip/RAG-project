"""Crawler parser tests."""

from crawler.parser import extract_page_content, is_valid_doc_url


SAMPLE_HTML = """
<html>
  <head><title>ENTRYPOINT vs CMD</title></head>
  <body>
    <nav>Skip</nav>
    <main>
      <h1>ENTRYPOINT</h1>
      <p>The ENTRYPOINT instruction configures a container to run as an executable.</p>
      <h2>CMD</h2>
      <p>CMD provides defaults for an executing container.</p>
    </main>
  </body>
</html>
"""


def test_is_valid_doc_url_filters_external_links():
    assert is_valid_doc_url(
        "https://docs.docker.com/reference/dockerfile/",
        "https://docs.docker.com",
        ["/reference/", "/engine/"],
    )
    assert not is_valid_doc_url(
        "https://google.com/search",
        "https://docs.docker.com",
        ["/reference/"],
    )


def test_extract_page_content_finds_main_text():
    result = extract_page_content(
        SAMPLE_HTML,
        "https://docs.docker.com/reference/dockerfile/",
        ["main"],
    )
    assert result["title"] == "ENTRYPOINT vs CMD"
    assert "ENTRYPOINT instruction" in result["body"]
    assert "CMD" in result["headings"]
