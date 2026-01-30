from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return ["home", "features", "why_us", "privacy", "terms"]

    def location(self, item):
        return reverse(item)


class HomeSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"
    protocol = "https"

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse(item)
