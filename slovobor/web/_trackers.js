if (YANDEX_METRIKA_ID) {
    // <!-- Yandex.Metrika counter --> <script type="text/javascript" >
    (function(m, e, t, r, i, k, a) {
        m[i] = m[i] || function() { (m[i].a = m[i].a || []).push(arguments) };
        m[i].l = 1 * new Date();
        k = e.createElement(t);
        a = e.getElementsByTagName(t)[0];
        k.async = 1;
        k.defer = 1;
        k.src = r;
        a.parentNode.insertBefore(k, a);
    })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

    ym(YANDEX_METRIKA_ID, "init", { clickmap: true, trackLinks: true, accurateTrackBounce: true, });
    // </script> <!-- /Yandex.Metrika counter -->
}

if (GOOGLE_TRACKING_ID) {
    (function(i, s, o, g, r, a, m) {
        i["GoogleAnalyticsObject"] = r;
        i[r] = i[r] || function() { (i[r].q = i[r].q || []).push(arguments); };
        i[r].l = 1 * new Date();
        a = s.createElement(o);
        m = s.getElementsByTagName(o)[0];
        a.async = 1;
        a.src = g;
        m.parentNode.insertBefore(a, m);
    })(window, document, "script", "https://www.google-analytics.com/analytics.js", "ga");

    ga("create", GOOGLE_TRACKING_ID, "auto");
    ga("send", "pageview");

}
