"""Render the story map page."""

from lib.assets import (
    BREADCRUMB_CSS,
    BREADCRUMB_JS,
    TOPBAR_CSS,
    VERSION_BANNER_CSS,
    VERSION_BANNER_HTML,
    VERSION_CHECK_JS,
)
from lib.html_helpers import e, generate_navbar, get_build_version, render_template


def render_story_map() -> str:
    """Render the Story Map HTML from the template."""
    build_version = get_build_version()
    nav_html = generate_navbar(active_section="", depth=0)
    breadcrumb_html = '<nav id="breadcrumb-nav" class="breadcrumb-nav" aria-label="Breadcrumb"></nav>'
    return render_template(
        "story-map.html",
        {
            "BUILD_VERSION": e(build_version),
            "NAVBAR": nav_html,
            "BREADCRUMBS": breadcrumb_html,
            "VERSION_BANNER": VERSION_BANNER_HTML,
            "TOPBAR_CSS": TOPBAR_CSS,
            "BREADCRUMB_CSS": BREADCRUMB_CSS,
            "VERSION_BANNER_CSS": VERSION_BANNER_CSS,
            "BREADCRUMB_JS": BREADCRUMB_JS,
            "VERSION_CHECK_JS": VERSION_CHECK_JS,
        },
    )
