import pytest

from citation_guard.ingest import document_from_text, load_document

SYNTH_RFC = (
    "Internet Engineering Task Force (IETF)                          A. Author\n"
    "\n"
    "1.  Introduction\n"
    "\n"
    "   The widget format is a compact representation.  Widgets are case-\n"
    "   sensitive strings.  A widget MUST contain a name and the parser\n"
    "\n"
    "\n"
    "\n"
    "Author, et al.                Standards Track                    [Page 1]\n"
    "\f\n"
    "RFC 9999                  Widget Format                          May 2015\n"
    "\n"
    "\n"
    "   MUST reject widgets without one.  Use of the colour field is\n"
    "   OPTIONAL.\n"
    "\n"
    "2.  Processing Rules\n"
    "\n"
    "   Processors SHOULD ignore unknown fields.  Processors MUST NOT\n"
    "   modify the name field.  The name field is a “case-sensitive”\n"
    "   value.\n"
    "\n"
    "Author, et al.                Standards Track                    [Page 2]\n"
)


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", default=False, help="run live API smoke tests")


@pytest.fixture
def synth_doc():
    return document_from_text("synth", SYNTH_RFC, "Widget Format")


@pytest.fixture(scope="session")
def rfc_doc():
    return load_document("rfc7519")
