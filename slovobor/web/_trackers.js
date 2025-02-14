function load_script_async(src, success, error) {
    let script = document.createElement('script');
    script.async = true;
    script.defer = true;
    script.src = src;
    if (success) { script.onload = success; }
    if (error) { script.onerror = error; }
    document.body.appendChild(script);
}

if (YANDEX_METRIKA_ID) {
    window.ym = function () {
        window.ym.a = window.ym.a || [];
        window.ym.a.push(arguments);
    };
    window.ym(
        YANDEX_METRIKA_ID,
        "init",
        { clickmap: true, trackLinks: true, accurateTrackBounce: true, }
    );
    function fallback_metrika_tracker() {
        var img = document.createElement('img');
        img.src = 'https://mc.yandex.ru/watch/' + YANDEX_METRIKA_ID;
        img.style = 'position:absolute; bottom:0; left:0; width:1px; height:1px;';
        document.body.appendChild(img);
    }
    load_script_async(
        'https://mc.yandex.ru/metrika/tag.js',
        null,
        fallback_metrika_tracker
    );
}

if (GOOGLE_TRACKING_ID) {
    function init_google_tracker() {
        window.dataLayer = window.dataLayer || [];
        function gtag() { dataLayer.push(arguments); }
        gtag('js', new Date());
        gtag('config', GOOGLE_TRACKING_ID);
    }
    load_script_async(
        'https://www.googletagmanager.com/gtag/js?id=' + GOOGLE_TRACKING_ID,
        init_google_tracker,
    );
}
