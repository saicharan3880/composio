"""
App enums.
"""

# pylint: disable=too-many-public-methods, unused-import

import typing as t

import typing_extensions as te  # noqa: F401

from composio.client.enums._action import Action
from composio.client.enums.base import APPS_CACHE, AppData, _AnnotatedEnum, enum


@enum
class App(_AnnotatedEnum[AppData], path=APPS_CACHE):
    """Class to represent `App` entity."""

    APALEO: "App"
    APIFY: "App"
    ASANA: "App"
    ATTIO: "App"
    BITBUCKET: "App"
    BREVO: "App"
    BROWSERBASE_TOOL: "App"
    BROWSER_TOOL: "App"
    CLICKUP: "App"
    CODEINTERPRETER: "App"
    CODE_FORMAT_TOOL: "App"
    CODE_GREP_TOOL: "App"
    CODE_INDEX_TOOL: "App"
    CODE_MAP_TOOL: "App"
    COMPOSIO: "App"
    DISCORD: "App"
    DROPBOX: "App"
    ELEVENLABS: "App"
    EMBED_TOOL: "App"
    EXA: "App"
    FIGMA: "App"
    FILETOOL: "App"
    FIRECRAWL: "App"
    GIT: "App"
    GITHUB: "App"
    GITLAB: "App"
    GMAIL: "App"
    GOOGLECALENDAR: "App"
    GOOGLEDOCS: "App"
    GOOGLEDRIVE: "App"
    GOOGLEMEET: "App"
    GOOGLESHEETS: "App"
    GOOGLETASKS: "App"
    GREPTILE: "App"
    HACKERNEWS: "App"
    HEROKU: "App"
    HISTORY_FETCHER: "App"
    HUBSPOT: "App"
    IMAGE_ANALYSER: "App"
    INDUCED_AI: "App"
    JIRA: "App"
    KLAVIYO: "App"
    LINEAR: "App"
    LISTENNOTES: "App"
    MATHEMATICAL: "App"
    MULTIONAI: "App"
    NASA: "App"
    NOTION: "App"
    OKTA: "App"
    PAGERDUTY: "App"
    PERPLEXITYAI: "App"
    POSTHOG: "App"
    RAGTOOL: "App"
    SCHEDULER: "App"
    SERPAPI: "App"
    SHELLTOOL: "App"
    SLACK: "App"
    SLACKBOT: "App"
    SNOWFLAKE: "App"
    SOUNDCLOUD: "App"
    SPIDERTOOL: "App"
    SPLITWISE: "App"
    SPOTIFY: "App"
    SQLTOOL: "App"
    STRAVA: "App"
    TASKADE: "App"
    TAVILY: "App"
    TRELLO: "App"
    TWILIO: "App"
    TYPEFORM: "App"
    WEATHERMAP: "App"
    WEBTOOL: "App"
    WHATSAPP: "App"
    WORKABLE: "App"
    YOUSEARCH: "App"
    YOUTUBE: "App"
    ZENDESK: "App"
    ZEPTOOL: "App"
    ZOOM: "App"

    @property
    def is_local(self) -> bool:
        """The tool is local if set to `True`"""
        return self.load().is_local

    @property
    def name(self) -> str:
        """Name of the app."""
        return self.load().name

    def get_actions(self, tags: t.Optional[t.List[str]] = None) -> t.Iterator[Action]:
        """
        Get actions for the given app filtered by the `tags`

        :param tags: List of tags to filter the actions
        :return: Iterator object which yields `Action`
        """
        tags = tags or []
        app = f"{self.slug.lower()}_"
        for action in Action.all():
            if not action.slug.lower().startswith(app):
                continue
            if len(tags) == 0:
                yield action
            if any((tag in action.tags for tag in tags)):
                yield action
